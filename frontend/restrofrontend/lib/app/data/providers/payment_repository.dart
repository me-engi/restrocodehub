import 'package:dio/dio.dart';
import 'package:get/get.dart'; // For Get.find<Dio>() and Get.snackbar
import 'package:restrofrontend/app/data/model/payment_initiation_model.dart';

import '../../shared/constants/api_constants.dart';
// We defined this earlier
// You might also have models for payment confirmation responses if needed

class PaymentRepository {
  final Dio _dio = Get.find<Dio>(); // Uses the globally registered Dio instance

  /// Initiates a payment process for a given order.
  ///
  /// This typically involves telling the backend to prepare a payment
  /// with a payment gateway (e.g., create a PaymentIntent with Stripe).
  /// The backend responds with data needed by the frontend SDK to proceed
  /// (e.g., a client_secret).
  ///
  /// [orderId]: The ID of the order for which payment is being initiated.
  /// [paymentMethodHint]: Optional hint for the backend about the user's
  /// preferred payment method (e.g., "STRIPE_CARD", "GPAY").
  Future<PaymentInitiationResponse?> initiatePayment({
    required String orderId,
    String? paymentMethodHint,
    // You might pass other relevant data like amount, currency if not solely derived from orderId on backend
  }) async {
    try {
      final requestData = PaymentInitiationRequest(
        orderId: orderId,
        paymentMethodHint: paymentMethodHint,
      );

      final response = await _dio.post(
        ApiConstants.initiatePaymentEndpoint,
        data: requestData.toJson(),
      );

      if (response.statusCode == 201 && response.data != null) { // 201 Created is common for initiating resources
        return PaymentInitiationResponse.fromJson(response.data as Map<String, dynamic>);
      } else {
        // Handle other successful but unexpected status codes if necessary
        Get.snackbar(
          "Payment Error",
          "Could not initialize payment (Status: ${response.statusCode}). Please try again.",
          snackPosition: SnackPosition.BOTTOM,
        );
        return null;
      }
    } on DioException catch (e) {
      // Dio errors (network, non-2xx status codes) are often handled by a global interceptor.
      // If not, or for specific handling:
      print("DioError initiating payment: ${e.message}");
      print("DioError response data: ${e.response?.data}");
      String errorMessage = "Failed to initiate payment. Please check your connection and try again.";
      if (e.response?.data != null && e.response!.data is Map) {
          final errorMap = e.response!.data as Map<String, dynamic>;
          errorMessage = errorMap['error']?.toString() ?? errorMap['detail']?.toString() ?? errorMessage;
      } else if (e.message != null && e.message!.isNotEmpty) {
          errorMessage = e.message!;
      }
      Get.snackbar("Payment Error", errorMessage, snackPosition: SnackPosition.BOTTOM);
      return null;
    } catch (e) {
      print("Unexpected error initiating payment: $e");
      Get.snackbar("Payment Error", "An unexpected error occurred. Please try again.", snackPosition: SnackPosition.BOTTOM);
      return null;
    }
  }

  // Optional: Confirm payment from client-side
  // This is often more for UX updates while waiting for a webhook,
  // as the webhook is the source of truth for payment completion.
  /*
  Future<bool> confirmClientSidePaymentSuccess({
    required String orderId,
    required String internalTransactionId, // Your PaymentTransaction.id
    required String gatewayPaymentId, // e.g., Stripe PaymentIntent ID
    required String paymentMethod,
  }) async {
    try {
      final response = await _dio.post(
        ApiConstants.confirmPaymentEndpoint, // You'd need to define this endpoint
        data: {
          'order_id': orderId,
          'internal_transaction_id': internalTransactionId,
          'gateway_payment_id': gatewayPaymentId,
          'payment_method': paymentMethod,
          'status': 'CLIENT_CONFIRMED_SUCCESS', // Example status
        },
      );
      return response.statusCode == 200;
    } catch (e) {
      print("Error confirming client-side payment: $e");
      // Don't necessarily show an error to user for this, as webhook is primary
      return false;
    }
  }
  */

  // You might add other methods here if needed, e.g.:
  // - Fetching available payment methods for a restaurant/region (if dynamic)
  // - Handling refunds initiated from the app (though often an admin task)
}