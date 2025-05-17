# backend/payments/models.py
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.conf import settings # For AUTH_USER_MODEL
import uuid

# Import Order model from the 'orders' app
from orders.models import Order # Assuming orders.models.Order

class PaymentTransaction(models.Model):
    """
    Represents a single payment transaction attempt for an Order.
    An order might have multiple transaction attempts if the first one fails.
    """
    PAYMENT_METHOD_CHOICES = [
        ('CREDIT_CARD', _('Credit Card')),
        ('DEBIT_CARD', _('Debit Card')),
        ('NET_BANKING', _('Net Banking')),
        ('UPI', _('UPI (India)')), # Unified Payments Interface
        ('WALLET_GPAY', _('Google Pay Wallet')),
        ('WALLET_PHONEPE', _('PhonePe Wallet')),
        ('WALLET_PAYTM', _('Paytm Wallet')),
        ('COD', _('Cash on Delivery')),
        ('STRIPE', _('Stripe')), # Generic if using Stripe for multiple methods
        ('PAYPAL', _('PayPal')),
        ('OTHER', _('Other')),
    ]

    TRANSACTION_STATUS_CHOICES = [
        ('PENDING', _('Pending')),          # Transaction initiated, awaiting gateway response or action
        ('SUCCESSFUL', _('Successful')),    # Payment confirmed by gateway
        ('FAILED', _('Failed')),            # Payment declined or failed at gateway
        ('CANCELLED', _('Cancelled')),      # Transaction cancelled by user or system before completion
        ('REFUND_INITIATED', _('Refund Initiated')),
        ('REFUNDED', _('Refunded')),
        ('PARTIALLY_REFUNDED', _('Partially Refunded')),
        ('REQUIRES_ACTION', _('Requires Action')), # e.g., 3D Secure, OTP
        ('PROCESSING', _('Processing')),         # Gateway is processing
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(
        Order,
        on_delete=models.PROTECT, # Protect order from deletion if payment transactions exist
        related_name='payment_transactions',
        verbose_name=_("related order")
    )
    user = models.ForeignKey( # Denormalized for easier querying, derived from order.user
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='payment_transactions_made',
        verbose_name=_("user who initiated payment")
    )
    tenant = models.ForeignKey( # Denormalized for easier querying, derived from order.tenant
        'users.Tenant', # String reference if Tenant is in 'users' app
        on_delete=models.PROTECT,
        related_name='tenant_payment_transactions',
        verbose_name=_("tenant associated with the order")
    )

    # Payment Gateway Details
    gateway_name = models.CharField(
        _("payment gateway name"), max_length=100, blank=True, null=True,
        help_text=_("e.g., Stripe, PayPal, Razorpay")
    )
    gateway_transaction_id = models.CharField(
        _("gateway transaction ID"), max_length=255, unique=True, null=True, blank=True, db_index=True, # Can be null if txn not yet sent to gateway
        help_text=_("Unique ID provided by the payment gateway for this transaction.")
    )
    # If you store payment intent IDs (e.g., from Stripe PaymentIntents)
    gateway_payment_intent_id = models.CharField(
        _("gateway payment intent ID"), max_length=255, blank=True, null=True, db_index=True
    )

    amount = models.DecimalField(_("transaction amount"), max_digits=12, decimal_places=2)
    currency = models.CharField(_("currency"), max_length=3, default='USD', help_text=_("ISO currency code, e.g., USD, INR, EUR")) # Default to your primary currency

    payment_method_used = models.CharField(
        _("payment method used"), max_length=50, choices=PAYMENT_METHOD_CHOICES,
        blank=True, null=True # Might not be known until user selects it on gateway page
    )
    status = models.CharField(
        _("transaction status"), max_length=30, choices=TRANSACTION_STATUS_CHOICES,
        default='PENDING', db_index=True
    )

    # Gateway Response & Error Handling
    gateway_response_payload = models.JSONField(
        _("gateway response payload"), blank=True, null=True,
        help_text=_("Full response from the payment gateway for record-keeping/debugging.")
    )
    error_message = models.TextField(_("error message"), blank=True, null=True, help_text=_("Error message if the transaction failed."))
    error_code = models.CharField(_("error code"), max_length=100, blank=True, null=True)

    # Timestamps
    initiated_at = models.DateTimeField(_("initiated at"), default=timezone.now)
    last_updated_at = models.DateTimeField(_("last updated at"), auto_now=True) # When the status or details last changed
    completed_or_failed_at = models.DateTimeField(_("completed/failed at"), null=True, blank=True)

    class Meta:
        verbose_name = _("payment transaction")
        verbose_name_plural = _("payment transactions")
        ordering = ['order', '-initiated_at']

    def __str__(self):
        return f"Transaction {self.id} for Order {self.order.order_number} - {self.get_status_display()}"

    def save(self, *args, **kwargs):
        # Ensure user and tenant are set from the order if not provided directly
        if self.order:
            if not self.user_id and self.order.user_id:
                self.user_id = self.order.user_id
            if not self.tenant_id and self.order.tenant_id:
                self.tenant_id = self.order.tenant_id

        # Update Order's payment_status when this transaction is successful or definitively failed
        is_new = self._state.adding
        old_status = None
        if not is_new:
            try:
                old_status = PaymentTransaction.objects.get(pk=self.pk).status
            except PaymentTransaction.DoesNotExist:
                pass # Should not happen if not is_new

        super().save(*args, **kwargs) # Save first to get ID if new

        if self.order and (is_new or self.status != old_status):
            current_order_payment_status = self.order.payment_status
            new_order_payment_status = None

            if self.status == 'SUCCESSFUL':
                new_order_payment_status = 'PAID'
            elif self.status == 'FAILED':
                # Check if there are other pending or successful transactions for this order
                other_successful_txns = self.order.payment_transactions.filter(status='SUCCESSFUL').exists()
                if not other_successful_txns:
                    new_order_payment_status = 'FAILED' # Mark order payment as failed only if no other success
            elif self.status == 'REFUNDED':
                # More complex logic needed for full vs partial refunds on order
                if self.amount == self.order.total_price: # Assuming full refund of order total
                     new_order_payment_status = 'REFUNDED'
                else:
                     new_order_payment_status = 'PARTIALLY_REFUNDED'

            if new_order_payment_status and new_order_payment_status != current_order_payment_status:
                self.order.payment_status = new_order_payment_status
                self.order.payment_gateway_transaction_id = self.gateway_transaction_id # Update order with this successful/final txn ID
                self.order.payment_method = self.payment_method_used
                self.order.save(update_fields=['payment_status', 'payment_gateway_transaction_id', 'payment_method'])
                # Potentially create an OrderStatusHistory entry for payment status change
                # from orders.models import OrderStatusHistory
                # OrderStatusHistory.objects.create(order=self.order, status=f"PAYMENT_{new_order_payment_status}", comment=f"Payment status updated by transaction {self.id}")