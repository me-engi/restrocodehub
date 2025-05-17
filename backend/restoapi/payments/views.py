# backend/payments/views.py
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.conf import settings
from rest_framework import generics, status, views, viewsets
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.db import transaction as db_transaction # Alias to avoid conflict

from .models import PaymentTransaction
from .serializers import PaymentTransactionSerializer, InitiatePaymentSerializer, StripeWebhookEventSerializer # Example
from orders.models import Order
from .permissions import CanInitiatePaymentForOrder, IsPlatformAdminForPaymentAccess
from users.permissions import IsPlatformAdmin # Or use the one from .permissions

# Placeholder for payment gateway service functions
# These would live in a separate services.py or payment_gateways/stripe_service.py etc.
def create_payment_intent_with_gateway(order: Order, payment_method_hint: str = None, user_ip: str = None):
    # 1. Create a PaymentTransaction record in PENDING state
    # 2. Interact with Stripe/PayPal SDK to create a payment intent/order
    #    - Pass order.total_price, currency, order.id (as metadata), customer info
    # 3. Store gateway_payment_intent_id in PaymentTransaction
    # 4. Return gateway-specific data needed by frontend (e.g., client_secret for Stripe)
    # Example response structure:
    # return {
    #     "success": True,
    #     "transaction_id": new_transaction.id, # Your internal transaction ID
    #     "gateway_data": {"client_secret": "pi_xxxx_secret_yyyy"}, # For Stripe
    #     "message": "Payment intent created."
    # }
    # --- This is a MOCK ---
    with db_transaction.atomic():
        new_transaction = PaymentTransaction.objects.create(
            order=order,
            user=order.user,
            tenant=order.tenant,
            amount=order.total_price,
            currency="USD", # Get from order or settings
            status='PENDING',
            gateway_name=payment_method_hint or "Stripe", # Example
            payment_method_used=payment_method_hint
        )
        # Simulate gateway interaction
        new_transaction.gateway_payment_intent_id = f"pi_mock_{uuid.uuid4().hex[:16]}"
        new_transaction.save()

        order.payment_status = 'AWAITING_ACTION' # Or similar
        order.save(update_fields=['payment_status'])

    return {
        "success": True,
        "transaction_id": str(new_transaction.id),
        "gateway_data": {"client_secret": f"pi_mock_{new_transaction.gateway_payment_intent_id}_secret_mock"},
        "message": "Mock payment intent created."
    }

def process_gateway_webhook(gateway_name: str, payload: dict, signature: str = None):
    # 1. Verify webhook signature (CRITICAL for security)
    # 2. Parse payload to identify event type (e.g., payment_succeeded, payment_failed, refund)
    # 3. Retrieve relevant PaymentTransaction using gateway_transaction_id or gateway_payment_intent_id from payload
    # 4. Update PaymentTransaction status, completed_or_failed_at, gateway_response_payload
    # 5. The PaymentTransaction.save() method will then update the associated Order's payment_status.
    # 6. If successful payment, trigger order fulfillment processes (e.g., notify restaurant POS).
    # Example simplified logic for a successful payment event:
    # if gateway_name == "stripe" and payload.get("type") == "payment_intent.succeeded":
    #     payment_intent = payload.get("data", {}).get("object", {})
    #     intent_id = payment_intent.get("id")
    #     try:
    #         transaction_to_update = PaymentTransaction.objects.get(gateway_payment_intent_id=intent_id)
    #         if transaction_to_update.status == 'PENDING': # Ensure not already processed
    #             transaction_to_update.status = 'SUCCESSFUL'
    #             transaction_to_update.gateway_transaction_id = payment_intent.get("latest_charge") # Or similar ID
    #             transaction_to_update.completed_or_failed_at = timezone.now()
    #             transaction_to_update.gateway_response_payload = payload
    #             transaction_to_update.save() # This will trigger order status update
    #
    #             # --- Integration Point: Trigger order fulfillment ---
    #             # from orders.tasks import process_successful_order_payment
    #             # process_successful_order_payment.delay(transaction_to_update.order.id)
    #
    #             return True, "Webhook processed successfully."
    #     except PaymentTransaction.DoesNotExist:
    #         return False, "Transaction not found for payment intent."
    #     except Exception as e:
    #         return False, f"Error processing webhook: {str(e)}"
    # return False, "Unhandled event type or gateway."
    pass # This needs full implementation per gateway


class InitiatePaymentView(generics.GenericAPIView):
    """
    Endpoint for a client (Flutter app) to initiate a payment for an order.
    POST /api/payments/initiate/
    """
    serializer_class = InitiatePaymentSerializer
    permission_classes = [IsAuthenticated] # Or a custom one allowing guest if order is tied to session

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = serializer.context['order_instance'] # Set by serializer validation

        # Check permission (user owns the order)
        # This could be a permission class on the view, or an explicit check here.
        if request.user != order.user:
             # For guest carts, this check would be based on session matching order's potential session link
            return Response({"error": "You do not have permission to pay for this order."}, status=status.HTTP_403_FORBIDDEN)

        payment_method_hint = serializer.validated_data.get('payment_method_hint')
        user_ip = request.META.get('REMOTE_ADDR')

        # Call your service function to interact with the payment gateway
        result = create_payment_intent_with_gateway(order, payment_method_hint, user_ip)

        if result.get("success"):
            return Response({
                "transaction_id": result["transaction_id"],
                "gateway_data": result["gateway_data"], # e.g., client_secret for Stripe Elements
                "message": result["message"]
            }, status=status.HTTP_201_CREATED)
        else:
            return Response({"error": result.get("message", "Failed to initiate payment.")}, status=status.HTTP_400_BAD_REQUEST)


class StripeWebhookView(views.APIView): # Example for Stripe
    """
    Endpoint to receive webhook events from Stripe.
    POST /api/payments/webhooks/stripe/
    This MUST be secured and validated properly.
    """
    permission_classes = [AllowAny] # Webhooks come from external service

    def post(self, request, *args, **kwargs):
        # webhook_secret = settings.STRIPE_WEBHOOK_SECRET
        # signature = request.META.get('HTTP_STRIPE_SIGNATURE')
        # payload = request.body
        # try:
        #     event = stripe.Webhook.construct_event(
        #         payload, signature, webhook_secret
        #     )
        # except ValueError as e: # Invalid payload
        #     return Response({"error": "Invalid payload"}, status=status.HTTP_400_BAD_REQUEST)
        # except stripe.error.SignatureVerificationError as e:
        #     return Response({"error": "Invalid signature"}, status=status.HTTP_400_BAD_REQUEST)

        # # For testing without full signature verification:
        event_data = request.data # Assuming JSON payload
        
        # Validate with a serializer if desired
        # serializer = StripeWebhookEventSerializer(data=event_data)
        # if not serializer.is_valid():
        #     # Log serializer.errors
        #     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        # validated_event_data = serializer.validated_data

        # Call a service function to process the webhook
        # success, message = process_gateway_webhook("stripe", validated_event_data, signature) # Pass original payload for sig check
        
        # MOCK PROCESSING:
        payment_intent = event_data.get("data", {}).get("object", {})
        intent_id = payment_intent.get("id")
        event_type = event_data.get("type")
        print(f"Received Stripe Webhook: {event_type} for intent {intent_id}")

        if event_type == "payment_intent.succeeded":
            try:
                transaction = PaymentTransaction.objects.get(gateway_payment_intent_id=intent_id)
                if transaction.status != 'SUCCESSFUL': # Avoid reprocessing
                    transaction.status = 'SUCCESSFUL'
                    transaction.gateway_transaction_id = payment_intent.get("latest_charge") or intent_id # Store relevant charge/txn ID
                    transaction.completed_or_failed_at = timezone.now()
                    transaction.gateway_response_payload = event_data # Store the full event
                    transaction.save() # This will trigger order.payment_status update via model's save()
                    print(f"Transaction {transaction.id} marked SUCCESSFUL for order {transaction.order.order_number}")
                    # --- Trigger further order processing ---
                    # from orders.tasks import fulfill_order_task
                    # fulfill_order_task.delay(transaction.order.id)
            except PaymentTransaction.DoesNotExist:
                print(f"ERROR: PaymentTransaction not found for intent_id: {intent_id}")
                return Response({"error": "Transaction not found"}, status=status.HTTP_404_NOT_FOUND)
            except Exception as e:
                print(f"ERROR processing webhook: {e}")
                return Response({"error": "Internal server error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        elif event_type == "payment_intent.payment_failed":
            # Handle failed payment
            pass


        return Response({"status": "received"}, status=status.HTTP_200_OK)


# --- Admin/Informational Views ---
class PaymentTransactionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only endpoint for platform admins to view payment transactions.
    """
    queryset = PaymentTransaction.objects.all().select_related('order', 'user', 'tenant')
    serializer_class = PaymentTransactionSerializer
    permission_classes = [IsAuthenticated, IsPlatformAdminForPaymentAccess] # Or IsPlatformAdmin
    filter_backends = [DjangoFilterBackend]
    filterset_fields = {
        'status': ['exact', 'in'],
        'payment_method_used': ['exact'],
        'gateway_name': ['exact'],
        'order__id': ['exact'],
        'user__email': ['exact', 'icontains'],
        'tenant__name': ['exact', 'icontains'],
        'initiated_at': ['date__gte', 'date__lte', 'date'],
        'amount': ['gte', 'lte']
    }
    search_fields = ['gateway_transaction_id', 'gateway_payment_intent_id', 'order__order_number', 'user__email']
    ordering_fields = ['initiated_at', 'amount', 'status']
    ordering = ['-initiated_at']