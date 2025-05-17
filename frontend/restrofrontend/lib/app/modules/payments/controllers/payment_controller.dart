import 'package:flutter/material.dart'; // For ModalRoute in navigation
import 'package:get/get.dart';
import 'package:restrofrontend/app/data/model/order_model.dart';

// Assuming models are in app/data/models/

import '../../../data/providers/payment_repository.dart';
import '../../../routes/app_pages.dart';
// import '../../auth/controllers/login_controller.dart'; // Optional, if needed for user details beyond order snapshot

// Enum for clearer payment status within the controller
enum PaymentProcessStatus { idle, initializing, processing, succeeded, failed, requiresAction }

class PaymentController extends GetxController {
  final PaymentRepository _paymentRepository = Get.find<PaymentRepository>();
  // final LoginController? _loginController = Get.isRegistered<LoginController>() ? Get.find<LoginController>() : null; // Safely get login controller

  // Order to pay is passed as an argument when navigating to PaymentScreen
  late final OrderDetailModel orderToPay;

  // --- Observable State ---
  var processStatus = PaymentProcessStatus.idle.obs;
  var statusMessage = Rx<String?>(null); // For user-facing messages (success/error)
  var gatewayClientSecret = Rx<String?>(null); // For Stripe-like client secrets

  // Example for Stripe (you would uncomment and use if integrating Stripe)
  // final StripeCardFormController cardFormController = StripeCardFormController();

  @override
  void onInit() {
    super.onInit();
    // Get the order details passed as arguments
    if (Get.arguments is OrderDetailModel) {
      orderToPay = Get.arguments as OrderDetailModel;
    } else {
      // This should ideally not happen if navigation is correct
      Get.snackbar("Error", "Order details not found. Please go back and try again.",
        snackPosition: SnackPosition.BOTTOM,
        backgroundColor: Colors.redAccent,
        colorText: Colors.white
      );
      // Potentially navigate back or to an error screen
      Get.offNamed(Routes.HOME); // Fallback
      // To prevent further execution if orderToPay is not initialized:
      // You might throw an exception or ensure orderToPay is non-nullable and assert in constructor.
      // For this example, we assume it will be passed.
      return;
    }

    // Initialize payment SDKs here if needed
    // Example: Stripe.publishableKey = "YOUR_STRIPE_PUBLISHABLE_KEY";
    // Example: await Stripe.instance.applySettings();
  }

  Future<void> initiateAndProcessCardPayment() async {
    if (processStatus.value == PaymentProcessStatus.initializing ||
        processStatus.value == PaymentProcessStatus.processing) {
      return; // Prevent multiple submissions
    }

    processStatus.value = PaymentProcessStatus.initializing;
    statusMessage.value = "Initializing payment...";

    // 1. Initiate payment with your backend
    final initResponse = await _paymentRepository.initiatePayment(
      orderId: orderToPay.id,
      paymentMethodHint: "STRIPE_CARD", // Example, could be dynamic
    );

    if (initResponse == null) {
      processStatus.value = PaymentProcessStatus.failed;
      statusMessage.value = "Failed to initialize payment. Please try again.";
      // Snackbar already shown by repository/Dio interceptor in most cases
      return;
    }

    // Example for Stripe: check for client_secret
    if (initResponse.gatewayData == null || initResponse.gatewayData!['client_secret'] == null) {
      processStatus.value = PaymentProcessStatus.failed;
      statusMessage.value = initResponse.message ?? "Payment gateway did not provide necessary details.";
      Get.snackbar("Payment Error", statusMessage.value!, snackPosition: SnackPosition.BOTTOM);
      return;
    }

    gatewayClientSecret.value = initResponse.gatewayData!['client_secret'];
    processStatus.value = PaymentProcessStatus.processing; // Ready to interact with Stripe SDK
    statusMessage.value = "Please complete your payment details.";

    // --- MOCKING STRIPE SDK INTERACTION ---
    // In a real app, this section would involve Stripe's Flutter SDK.
    // For now, we simulate a delay and then a success.
    print("Mocking Stripe SDK interaction with clientSecret: ${gatewayClientSecret.value}");
    await Future.delayed(const Duration(seconds: 3)); // Simulate SDK processing

    // Assume payment was successful for the mock
    _handleMockPaymentSuccess();
    // --- END OF MOCK ---

    // --- REAL STRIPE SDK INTERACTION (Illustrative Pseudo-code) ---
    /*
    if (gatewayClientSecret.value != null) {
      try {
        // Ensure card details are valid if using StripeCardFormField
        // if (!cardFormController.details.complete) {
        //   processStatus.value = PaymentProcessStatus.idle;
        //   statusMessage.value = "Please complete your card details.";
        //   Get.snackbar("Card Details", statusMessage.value!, snackPosition: SnackPosition.BOTTOM);
        //   return;
        // }

        final paymentIntent = await Stripe.instance.confirmPayment(
          paymentIntentClientSecret: gatewayClientSecret.value!,
          data: PaymentMethodParams.card( // Or other payment method types
            paymentMethodData: PaymentMethodData(
              billingDetails: BillingDetails(
                email: orderToPay.customerEmailSnapshot ?? _loginController?.currentUser.value?.email,
                name: orderToPay.customerNameSnapshot ?? _loginController?.currentUser.value?.name,
                // address: ... if needed
              ),
            ),
          ),
        );

        if (paymentIntent.status == PaymentIntentsStatus.Succeeded) {
          _handlePaymentSuccess(initResponse.transactionId, paymentIntent.id);
        } else if (paymentIntent.status == PaymentIntentsStatus.RequiresAction ||
                   paymentIntent.status == PaymentIntentsStatus.RequiresPaymentMethod) {
          processStatus.value = PaymentProcessStatus.requiresAction;
          statusMessage.value = "Payment requires further action or a different payment method.";
          Get.snackbar("Payment Info", statusMessage.value!, snackPosition: SnackPosition.BOTTOM);
        } else { // Canceled, Failed, etc.
          _handlePaymentFailure(paymentIntent.lastPaymentError?.message ?? "Payment was not successful.");
        }
      } catch (e) {
        print("Stripe SDK Error: $e");
        _handlePaymentFailure("An error occurred while processing your payment with the bank. ${e.toString()}");
      }
    }
    */
    // --- END OF REAL STRIPE SDK INTERACTION ---
  }

  void _handleMockPaymentSuccess() {
    processStatus.value = PaymentProcessStatus.succeeded;
    statusMessage.value = "Mock Payment Successful!";
    Get.snackbar("Success", statusMessage.value!,
        snackPosition: SnackPosition.BOTTOM,
        backgroundColor: Colors.green,
        colorText: Colors.white
    );

    // Important: In a real app, the backend webhook is the source of truth for order status update.
    // This navigation is for immediate UX. The OrderDetailScreen should ideally refresh its data.
    Get.offNamedUntil(Routes.ORDER_DETAIL, ModalRoute.withName(Routes.HOME), arguments: orderToPay.id);
  }

  void _handlePaymentSuccess(String internalTransactionId, String gatewayPaymentId) {
    processStatus.value = PaymentProcessStatus.succeeded;
    statusMessage.value = "Payment Successful!";
    Get.snackbar("Success", statusMessage.value!,
        snackPosition: SnackPosition.BOTTOM,
        backgroundColor: Colors.green,
        colorText: Colors.white
    );

    // Optional: Inform backend about client-side success (though webhook is primary)
    // _paymentRepository.confirmClientSidePaymentSuccess(
    //   orderId: orderToPay.id,
    //   internalTransactionId: internalTransactionId,
    //   gatewayPaymentId: gatewayPaymentId,
    //   paymentMethod: "STRIPE_CARD" // Or detected method
    // );

    // Navigate to order detail screen, which should show updated status (polled or via WebSocket)
    // Using offNamedUntil to clear the payment screen and go back to home if user presses back from order detail.
    Get.offNamedUntil(Routes.ORDER_DETAIL, ModalRoute.withName(Routes.HOME), arguments: orderToPay.id);
  }

  void _handlePaymentFailure(String errorMessage) {
    processStatus.value = PaymentProcessStatus.failed;
    statusMessage.value = errorMessage;
    Get.snackbar("Payment Failed", statusMessage.value!,
        snackPosition: SnackPosition.BOTTOM,
        backgroundColor: Colors.redAccent,
        colorText: Colors.white
    );
  }

  // Add methods for other payment types like GPay, PayPal, etc.
  // Future<void> processGPayPayment() async { ... }
}