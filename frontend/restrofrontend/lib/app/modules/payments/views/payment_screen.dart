import 'package:flutter/material.dart';
import 'package:get/get.dart';
// import 'package:flutter_stripe/flutter_stripe.dart'; // Uncomment when integrating Stripe

import '../controllers/payment_controller.dart'; // Ensure this path is correct

class PaymentScreen extends GetView<PaymentController> {
  const PaymentScreen({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    // It's good practice to ensure orderToPay is available.
    // The controller's onInit handles this, but an extra check or fallback UI is robust.
    if (controller.orderToPay == null) { // This check might be redundant if controller handles it robustly
        return Scaffold(
            appBar: AppBar(title: const Text("Payment Error")),
            body: const Center(child: Text("Order details are missing. Cannot proceed with payment.")),
        );
    }

    return Scaffold(
      appBar: AppBar(
        title: Text(
          "Pay for Order #${controller.orderToPay.orderNumber.length > 6 ? controller.orderToPay.orderNumber.substring(controller.orderToPay.orderNumber.length - 6) : controller.orderToPay.orderNumber}"
        ),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () {
            // Custom back button logic if needed, e.g., confirm before leaving payment
            if (controller.processStatus.value == PaymentProcessStatus.processing ||
                controller.processStatus.value == PaymentProcessStatus.initializing) {
              Get.dialog(
                AlertDialog(
                  title: const Text("Payment in Progress"),
                  content: const Text("Are you sure you want to go back? Your payment is being processed."),
                  actions: [
                    TextButton(onPressed: () => Get.back(), child: const Text("Stay")),
                    TextButton(onPressed: () => Get.back(result: true), child: const Text("Go Back")),
                  ],
                )
              ).then((goBack) {
                if (goBack == true) Get.back();
              });
            } else {
              Get.back();
            }
          },
        ),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20.0),
        child: Center( // Center the content for better appearance on wider screens
          child: ConstrainedBox( // Max width for the content
            constraints: const BoxConstraints(maxWidth: 500),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                // Order Total Display
                Card(
                  elevation: 0,
                  color: Get.theme.colorScheme.surfaceVariant.withOpacity(0.7),
                  child: Padding(
                    padding: const EdgeInsets.all(16.0),
                    child: Column(
                      children: [
                        Text(
                          "Amount to Pay",
                          style: Get.textTheme.titleMedium?.copyWith(
                            color: Get.theme.colorScheme.onSurfaceVariant,
                          ),
                        ),
                        const SizedBox(height: 8),
                        Text(
                          "\$${controller.orderToPay.totalPrice.toStringAsFixed(2)}",
                          style: Get.textTheme.displaySmall?.copyWith(
                            fontWeight: FontWeight.bold,
                            color: Get.theme.colorScheme.primary,
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
                const SizedBox(height: 24),

                // Payment Method Section Title
                Text(
                  "Enter Card Details", // Or "Select Payment Method"
                  style: Get.textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w600),
                  textAlign: TextAlign.center,
                ),
                const SizedBox(height: 16),

                // --- Placeholder for Actual Payment Gateway Widget ---
                // Example: Stripe CardField
                // Ensure you have flutter_stripe dependency and setup
                /*
                Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    border: Border.all(color: Get.theme.dividerColor),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: CardField(
                    controller: controller.cardFormController, // Create this in your PaymentController
                    style: TextStyle(fontSize: 16, color: Get.textTheme.bodyLarge?.color),
                    decoration: const InputDecoration(
                      border: InputBorder.none,
                      hintText: 'Card number', // Stripe SDK handles specific field hints
                    ),
                    onCardChanged: (details) {
                      // You can react to card changes if needed, e.g., validate CVC, expiry
                      print("Card details changed: ${details?.complete}");
                    },
                  ),
                ),
                */
                Container(
                  padding: const EdgeInsets.symmetric(vertical: 40, horizontal: 20),
                  decoration: BoxDecoration(
                    border: Border.all(color: Colors.grey.shade300, style: BorderStyle.solid, width: 1.5),
                    borderRadius: BorderRadius.circular(12),
                    color: Colors.grey.shade50,
                  ),
                  child: const Center(
                    child: Text(
                      "Payment Gateway Integration\n(e.g., Stripe CardField) \nwould render here.",
                      textAlign: TextAlign.center,
                      style: TextStyle(color: Colors.grey),
                    ),
                  ),
                ),
                const SizedBox(height: 30),

                // --- Pay Button ---
                Obx(() {
                  bool isLoading = controller.processStatus.value == PaymentProcessStatus.initializing ||
                                   controller.processStatus.value == PaymentProcessStatus.processing;
                  bool isPaymentDone = controller.processStatus.value == PaymentProcessStatus.succeeded ||
                                      controller.processStatus.value == PaymentProcessStatus.failed;

                  return ElevatedButton.icon(
                    icon: isLoading
                        ? const SizedBox(
                            width: 20,
                            height: 20,
                            child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2.5),
                          )
                        : Icon(isPaymentDone ? Icons.check_circle_outline : Icons.lock_open_outlined), // Or Icons.credit_card
                    label: Text(
                      isLoading
                          ? "Processing..."
                          : (isPaymentDone ? "Payment Attempted" : "Pay Securely"),
                    ),
                    onPressed: (isLoading || isPaymentDone) // Disable if loading or already attempted (succeeded/failed)
                        ? null
                        : controller.initiateAndProcessCardPayment,
                  );
                }),
                const SizedBox(height: 16),

                // --- Status Message Display ---
                Obx(() {
                  if (controller.statusMessage.value != null) {
                    Color messageColor = Colors.grey;
                    IconData messageIcon = Icons.info_outline;

                    switch (controller.processStatus.value) {
                      case PaymentProcessStatus.succeeded:
                        messageColor = Colors.green.shade700;
                        messageIcon = Icons.check_circle_outline;
                        break;
                      case PaymentProcessStatus.failed:
                        messageColor = Colors.red.shade700;
                        messageIcon = Icons.error_outline;
                        break;
                      case PaymentProcessStatus.initializing:
                      case PaymentProcessStatus.processing:
                        messageColor = Get.theme.colorScheme.primary;
                        messageIcon = Icons.hourglass_empty_rounded;
                        break;
                      case PaymentProcessStatus.requiresAction:
                        messageColor = Colors.orange.shade700;
                        messageIcon = Icons.warning_amber_rounded;
                         break;
                      default: // idle
                        return const SizedBox.shrink(); // No message if idle and no prior message
                    }

                    return Padding(
                      padding: const EdgeInsets.only(top: 8.0),
                      child: Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Icon(messageIcon, color: messageColor, size: 18),
                          const SizedBox(width: 8),
                          Expanded(
                            child: Text(
                              controller.statusMessage.value!,
                              style: TextStyle(color: messageColor, fontWeight: FontWeight.w500),
                              textAlign: TextAlign.center,
                            ),
                          ),
                        ],
                      ),
                    );
                  }
                  return const SizedBox.shrink();
                }),
                const SizedBox(height: 20),
                 // Optionally, add a way to try a different payment method or cancel
                if (controller.processStatus.value == PaymentProcessStatus.failed ||
                    controller.processStatus.value == PaymentProcessStatus.requiresAction)
                  TextButton(
                    onPressed: () {
                      // Reset state to allow trying again or choosing another method
                      controller.processStatus.value = PaymentProcessStatus.idle;
                      controller.statusMessage.value = null;
                      // Potentially navigate to a screen to choose other methods
                    },
                    child: const Text("Try Again or Change Method"),
                  )
              ],
            ),
          ),
        ),
      ),
    );
  }
}