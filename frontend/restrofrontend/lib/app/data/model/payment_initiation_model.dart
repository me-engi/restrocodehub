class PaymentInitiationRequest {
  final String orderId;
  final String? paymentMethodHint; // e.g., "STRIPE_CARD", "GPAY"

  PaymentInitiationRequest({required this.orderId, this.paymentMethodHint});

  Map<String, dynamic> toJson() {
    return {
      'order_id': orderId,
      if (paymentMethodHint != null) 'payment_method_hint': paymentMethodHint,
    };
  }
}

class PaymentInitiationResponse {
  final String transactionId; // Your internal payment transaction ID
  final Map<String, dynamic>? gatewayData; // e.g., { "client_secret": "..." } for Stripe
  final String message;

  PaymentInitiationResponse({required this.transactionId, this.gatewayData, required this.message});

  factory PaymentInitiationResponse.fromJson(Map<String, dynamic> json) {
    return PaymentInitiationResponse(
      transactionId: json['transaction_id'] as String,
      gatewayData: json['gateway_data'] as Map<String, dynamic>?,
      message: json['message'] as String,
    );
  }
}