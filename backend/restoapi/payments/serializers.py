# backend/payments/serializers.py
from rest_framework import serializers
from .models import PaymentTransaction
from orders.models import Order # For validating order ID

class PaymentTransactionSerializer(serializers.ModelSerializer):
    order_number = serializers.CharField(source='order.order_number', read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True, allow_null=True)
    tenant_name = serializers.CharField(source='tenant.name', read_only=True, allow_null=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    payment_method_used_display = serializers.CharField(source='get_payment_method_used_display', read_only=True, allow_null=True)

    class Meta:
        model = PaymentTransaction
        fields = [
            'id', 'order', 'order_number', 'user', 'user_email', 'tenant', 'tenant_name',
            'gateway_name', 'gateway_transaction_id', 'gateway_payment_intent_id',
            'amount', 'currency', 'payment_method_used', 'payment_method_used_display',
            'status', 'status_display', 'error_message', 'error_code',
            'initiated_at', 'last_updated_at', 'completed_or_failed_at',
            'gateway_response_payload' # Be cautious exposing full payload publicly
        ]
        read_only_fields = [
            'id', 'user_email', 'tenant_name', 'status_display', 'payment_method_used_display',
            'initiated_at', 'last_updated_at', 'completed_or_failed_at'
        ]
        # Fields like 'gateway_transaction_id', 'status' etc. are updated by the system/webhook, not directly by API user


class InitiatePaymentSerializer(serializers.Serializer):
    """
    Serializer for the client to request payment initiation for an order.
    """
    order_id = serializers.UUIDField()
    payment_method_hint = serializers.ChoiceField(
        choices=PaymentTransaction.PAYMENT_METHOD_CHOICES,
        required=False,
        help_text="Optional: A hint from the client about the desired payment method."
    )
    # You might add other fields like 'return_url' for the gateway, etc.

    def validate_order_id(self, value):
        try:
            order = Order.objects.get(id=value)
            # Check if order is in a state that allows payment
            if order.payment_status == 'PAID':
                raise serializers.ValidationError("This order has already been paid.")
            if order.status in ['CANCELLED_BY_USER', 'CANCELLED_BY_RESTAURANT', 'COMPLETED', 'DELIVERED']:
                 raise serializers.ValidationError(f"Cannot initiate payment for an order with status: {order.get_status_display()}.")
            # Store order instance in context for use in the view
            self.context['order_instance'] = order
        except Order.DoesNotExist:
            raise serializers.ValidationError("Invalid Order ID.")
        return value

# --- Webhook Serializers (Example for a generic webhook) ---
# Each payment gateway will have a different webhook payload structure.
# You'll need specific serializers for each gateway you integrate.

class StripeWebhookEventSerializer(serializers.Serializer): # Highly simplified example
    id = serializers.CharField()
    type = serializers.CharField()
    data = serializers.JSONField()
    # ... other Stripe event fields ...

    def validate_type(self, value):
        # Validate if it's an event type you handle (e.g., 'charge.succeeded', 'payment_intent.succeeded')
        allowed_types = ['payment_intent.succeeded', 'payment_intent.payment_failed', 'charge.refunded']
        if value not in allowed_types:
            raise serializers.ValidationError(f"Unsupported Stripe event type: {value}")
        return value