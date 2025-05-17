# backend/orders/models.py
from django.db import models, transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.conf import settings # For AUTH_USER_MODEL
import uuid

# Assuming these models are correctly defined in their respective apps
# from users.models import User, Tenant # Using string reference below for flexibility
# from restaurants.models import Restaurant
# from menu.models import MenuItem, CustomizationOption

class Cart(models.Model):
    """
    Represents a shopping cart for a user (authenticated or anonymous session).
    A cart is typically associated with one restaurant once an item is added.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField( # An authenticated user has one active cart
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='cart',
        null=True, blank=True, # Allow anonymous carts linked by session
        verbose_name=_("user")
    )
    session_key = models.CharField( # For anonymous/guest carts
        _("session key"), max_length=40, null=True, blank=True, db_index=True, unique=True
    )
    restaurant = models.ForeignKey(
        'restaurants.Restaurant', # String reference
        on_delete=models.SET_NULL, # If restaurant is deleted, cart items might become invalid
        null=True, blank=True, # CartOkay, let's reconstruct the `orders` app, piece by piece, ensuring it's professional and covers the necessary CRUD operations and business logic. We'll build `models.py`, then `serializers.py`, `permissions.py`, `views.py`, `urls.py`, and finally `admin.py`.

 might not have a restaurant until first item added
        related_name='carts_initiated',
        verbose_name=_("restaurant context")
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("shopping cart")
        verbose_name_plural = _("shopping carts")
        ordering = ['-updated_at']
        constraints = [
            models.UniqueConstraint(fields=['user'], condition=models.Q(user__isnull=False), name='unique_active_user_cart', violation_error_message=_("User can only have one active cart.")),
            # session_key is already unique=True
        ]



    def __str__(self):
        if self.user:
            return f"Cart for {self.user.email or self.user.id}"
        elif self.session_key:
            return f"Guest Cart (Session: {self.session_key[:8]}...)"
        return f"Cart {self.id}"

    def get_subtotal_price(self):
        return sum(item.line_total for item in self.items.all())

    def get_item_count(self):
        return sum(item.quantity for item in self.items.all())

    def clear(self):
        with transaction.atomic():
            self.items/models.py
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.conf import settings # For AUTH_USER_MODEL
import uuid

# Assuming these models are correctly defined in their respective apps
from users.models import User, Tenant
from restaurants.models import Restaurant
from menu.models import MenuItem, CustomizationOption

class Cart(models.Model):
    """
    Represents a shopping cart for a user (authenticated or anonymous session).
    A cart is typically associated with one restaurant once an item is added.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField( # A user typically has one active cart
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='cart',
        null=True, blank=True # Allow anonymous carts linked by session
    )
    session_key = models.CharField(
        _("session key"), max_length=40, null=True, blank=True, db_index=True
    )
    restaurant = models.ForeignKey(
        Restaurant,
        on_delete=models.SET_NULL, # If restaurant is deleted, cart might be invalidated or items removed
        null=.all().delete()
            self.restaurant = None # Reset restaurant context
            self.save(update_fields=['restaurant', 'updated_at'])

    def add_item(self, menu_item, quantity: int = 1, selected_customization_options: list = None):
        """
        Adds an item to the cart or updates quantity if it already exists with same customizations.
        selected_customization_options: List of CustomizationOption instancesTrue, blank=True, # Null until first item from a specific restaurant is added
        related_name='carts_initiated'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("shopping cart")
        verbose_name_plural = _("shopping carts")
        ordering = ['-updated_at']
        constraints = [
            models.UniqueConstraint(fields=['user'], condition=models.Q(user__isnull=False), name='unique_active_user_cart'),
            models.UniqueConstraint(fields=['session_key'], condition=models.Q(session_key__isnull=False, user__isnull=True), name='unique_active_session_cart'),
        ]

    def __str__(self):
        if self.user:
            return f"Cart for {self.user.email or self.user.id}"
        elif self.session_key:
            return f"Anonymous Cart (Session: {self.session_key[:8]}...)"
        return f"Cart {self.id}"

    def get_sub or their IDs.
        """
        from menu.models import CustomizationOption # Local import to avoid circularity at module level

        if self.restaurant and self.restaurant != menu_item.restaurant:
            raise ValueError("Cannot add items from different restaurants to the same cart.")
        if not self.restaurant:
            self.restaurant = menu_item.restaurant
            self.save(update_fields=['restaurant'])

        # Calculate price and build snapshot
        current_unit_price = menu_item.base_price
        customizations_snapshot = []
        actual_options = []

        if selected_customization_options:
            option_ids = [opt.id if isinstance(opt, CustomizationOption) else opt for opt in selected_customization_options]
            options_qs = CustomizationOption.objects.filter(
                id__in=option_ids,
                group__menu_item=menu_item,
                is_available=True
            ).select_related('group')

            # Validate all provided option IDs were found and valid for the item
            if len(options_qs) != len(set(option_ids)): # Using set to handle potential duplicates in input
                raise ValueError("Invalid ortotal_price(self):
        return sum(item.line_total for item in self.items.all())

    def clear(self):
        self.items.all().delete()
        self.restaurant = None # Reset restaurant context if cart is cleared
        self.save()


class CartItem(models.Model):
    """
    An item within a shopping cart.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(_("quantity"), default=1)

    # Snapshot of selected customization options at the time of adding to cart
    # Stores a list of dicts: [{'option_id': uuid, 'option_name': str, 'group_id': uuid, 'group_name': str, 'price_adjustment': decimal}]
    selected_customizations_snapshot = models.JSONField(
        _("selected customizations snapshot"), default=list, blank=True
    )
    # Price of one unit of this item INCLUDING customizations, at the time it was added/updated.
    unit_price_at_addition = models.DecimalField(_("unit price at addition"), max_digits=10, decimal_places=2)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("cart item")
        verbose_name_plural = _("cart items")
        # Prevent exact duplicate item config (same menu_item, same customizations)
        # This requires selected_customizations_snapshot to be a canonical (e.g., sorted) string unavailable customization options provided.")

            for option in options_qs:
                current_unit_price += option.price_adjustment
                customizations_snapshot.append({
                    "option_id": str(option.id),
                    "option_name": option.name,
                    "group_id": str(option.group.id),
                    "group_name": option.group.name,
                    "price_adjustment": float(option.price_adjustment)
                })
                actual_options.append(option)

        # Sort snapshot for consistent matching if using JSONField exact match
        customizations_snapshot.sort(key=lambda x: x['option_id'])

        cart_item, created = self.items.get_or_create(
            menu_item=menu_item,
            selected_customizations_snapshot=customizations_snapshot, # This relies on JSON exact match
            defaults={
                'quantity': quantity,
                'unit_price_at_addition': current_unit_price
            }
        )

        if not created:
            cart_item.quantity += quantity
            # Optionally re-verify price if menu_item or option prices could change rapidly
            # For now, we assume unit_price_at_addition is fixed on first add of this specific configuration
        cart_item.save()
        self.updated_at = timezone.now()
        self.save(update_fields=['updated_at'])
        return cart_item


class CartItem(models.Model):
    """ An item within a shopping cart. """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name or to handle in code.
        # For simplicity, direct DB constraint might be hard with JSON. Logic handled in add_to_cart.
        # unique_together = [['cart', 'menu_item', 'selected_customizations_snapshot_str']] # if snapshot is string
        ordering = ['added_at']

    def __str__(self):
        return f"{self.quantity} x {self.menu_item.name} in cart {self.cart_id}"

    @property
    def line_total(self):
        return round(self.unit_price_at_addition * self.quantity, 2)


class Order(models.Model):
    """
    Represents a customer's order placed at a restaurant.
    """
    ORDER_STATUS_CHOICES = [
        ('PENDING_PAYMENT', _('Pending Payment')),
        ('AWAITING_CONFIRMATION', _('Awaiting Restaurant Confirmation')),
        ('CONFIRMED', _('Confirmed / Accepted by Restaurant')),
        ('PREPARING', _('Preparing')),
        ('READY_FOR_PICKUP', _('Ready for Pickup')),
        ('OUT_FOR_DELIVERY', _('Out for Delivery')),
        ('DELIVERED', _('Delivered')), # For delivery orders
        ('COMPLETED', _('Completed')), # For dine-in/takeaway after payment/pickup
        ('CANCELLED_BY_USER', _('Cancelled by User')),
        ('CANCELLED_BY_RESTAURANT', _('Cancelled by Restaurant')),
        ('FAILED', _('Failed (Payment/System Error)')),
    ]
    ORDER_TYPE_CHOICES = [
        ('DINE_IN', _('Dine-In')),
        ('TAKEAWAY', _('Takeaway / Pickup')),
        ('DELIVERY', _('Delivery')),
    ]
    PAYMENT_STATUS_CHOICES = [
        ('PENDING', _('Pending')),
        ('PAID', _('Paid')),
        ('FAILED', _('Failed')),
        ('REFUNDED', _('Refunded')),
        ('PARTIALLY_REFUNDED', _('Partially Refunded')),
        ('AWAITING_ACTION', _('Awaiting Payment Action')), # e.g. 3DS
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order_number = models.CharField(
        _("order number"), max_length=30, unique=True, editable=False, db_index=True,
        help_text=_("='items', verbose_name=_("cart"))
    menu_item = models.ForeignKey(
        'menu.MenuItem', # String reference
        on_delete=models.CASCADE, # If MenuItem is deleted, CartItem is removed.
                                  # Consider SET_NULL + is_active=False if cart item should persist but be unorderable.
        verbose_name=_("menu item")
    )
    quantity = models.PositiveIntegerField(_("quantity"), default=1)
    # Snapshot of selected customizations at the time of adding to cart
    selected_customizations_snapshot = models.JSONField(
        _("selected customizations snapshot"), default=list, blank=True,
        help_text=_("List of {'option_id': uuid, 'option_name': str, 'group_id': uuid, 'group_name': str, 'price_adjustment': decimal}")
    )
    # Price of the item AT THE TIME IT WAS ADDED TO CART (menu_item.base_price + sum of customization_price_adjustments)
    unit_price_at_addition = models.DecimalField(
        _("unit price at addition"), max_digits=10, decimal_places=2,
        help_text=_("Price of one unit of this item with selected customizations when added to cart.")
    )
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("cart item")
        verbose_name_plural = _("cart items")
        # Prevent exact same item config (menu_item + same customizations) multiple times as separate entries; just update quantity.
        # This requires selected_customizations_snapshot to be consistently structured (e.g., sorted).
        # JSONField equality check can be tricky across DBs. It's often handled in Cart.add_item logic.
        # unique_together = [['cart', 'menu_item', 'selected_customizations_snapshot']]
        ordering = ['added_at']

    def __str__(self):
        return f"{self.quantity} x {self.menu_item.name} (in Cart {self.cart_id})"

    @property
    def line_total(self):
        return round(self.quantity * self.unit_price_at_addition, 2)


class Order(models.Model):
    """ Represents a customer's order placed at a restaurant. """
    ORDER_STATUS_CHOICES = [
        ('PENDING_PAYMENT', _('Pending Payment')),
        ('AWAITING_CONFUnique, human-readable order identifier.")
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True, # Allow guest orders, but link if user is known
        related_name='orders_placed'
    )
    # Denormalized for easier querying and because restaurant/tenant might change name later
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.PROTECT,
        related_name='tenant_orders'
    )
    restaurant = models.ForeignKey(
        Restaurant,
        on_delete=models.PROTECT,
        related_name='restaurant_orders'
    )

    status = models.CharField(
        _("order status"), max_length=30, choices=ORDER_STATUS_CHOICES,
        default='AWAITING_CONFIRMATION', db_index=True
    )
    order_type = models.CharField(_("order type"), max_length=20, choices=ORDER_TYPE_CHOICES)

    # Customer info snapshot (especially for guest or if user details change)
    customer_name_snapshot = models.CharField(_("customer name (snapshot)"), max_length=255, blank=True, null=True)
    customer_phone_snapshot = models.CharField(_("customer phone (snapshot)"), max_length=30, blank=True, null=True)
    customer_email_snapshot = models.EmailField(_("customer email (snapshot)"), blank=True, null=True)

    # Dine-In Specific
    table_number = models.CharField(_("table number"), max_length=50, blank=True, null=True)

    # Delivery Specific
    delivery_address_line1 = models.CharField(_("delivery address line 1"), max_length=255, blank=True, null=True)
    delivery_address_line2 = models.CharField(_("delivery address line 2"), max_length=255, blank=True, null=True)
    delivery_city = models.CharField(_("delivery city"), max_length=100, blank=True, null=True)
    delivery_postal_code = models.CharField(_("delivery postal code"), max_length=20, blank=True, null=True)
    delivery_latitude = models.DecimalField(_("delivery latitude"), max_digits=10, decimal_places=7, null=True, blank=True)
    delivery_longitude = models.DecimalField(_("delivery longitude"), max_digits=10, decimal_places=7, null=True, blank=True)
    delivery_instructions = models.TextField(_("delivery instructions"), blank=True, null=True)

    # Financials (calculated from OrderItems at time of order placement)
    subtotal_price = models.DecimalField(_("subtotal price"), max_digits=10, decimal_places=2)
    taxes_amount = models.DecimalField(_("taxes"), max_digits=10, decimal_places=2, default=0.00)
    delivery_fee = models.DecimalField(_("delivery fee"), max_digits=8, decimal_places=2, default=0.00)
    service_fee = models.DecimalField(_("service fee"), max_digits=8, decimal_places=2, default=0.00)
    discount_amount = models.DecimalField(_("discount amount"), max_digits=10, decimal_places=2, default=0.00)
    total_price = models.DecimalField(_("total price (payable)"), max_digits=10, decimal_places=2)

IRMATION', _('Awaiting Restaurant Confirmation')), # Changed from PENDING_CONFIRMATION
        ('CONFIRMED', _('Confirmed / Accepted by Restaurant')),
        ('PREPARING', _('Preparing')),
        ('READY_FOR_PICKUP', _('Ready for Pickup')),
        ('OUT_FOR_DELIVERY', _('Out for Delivery')),
        ('DELIVERED', _('Delivered')), # For delivery orders
        ('COMPLETED', _('Completed')), # For dine-in/takeaway after payment/pickup
        ('CANCELLED_BY_USER', _('Cancelled by User')),
        ('CANCELLED_BY_RESTAURANT', _('Cancelled by Restaurant')),
        ('FAILED_PAYMENT', _('Payment Failed')), # If payment attempt after order placement fails
        ('SYSTEM_CANCELLED', _('System Cancelled')), # e.g., due to timeout or other system reasons
    ]
    ORDER_TYPE_CHOICES = [
        ('DINE_IN', _('Dine-In')),
        ('TAKEAWAY', _('Takeaway / Pickup')),
        ('DELIVERY', _('Delivery')),
    ]
    PAYMENT_STATUS_CHOICES = [
        ('PENDING', _('Pending')),
        ('PAID', _('Paid')),
        ('FAILED', _('Failed')),
        ('REFUNDED', _('Refunded')),
        ('PARTIALLY_REFUNDED', _('Partially Refunded')),
        ('AWAITING_ACTION', _('Awaiting Payment Action')), # e.g. for gateways needing redirect
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order_number = models.CharField(
        _("order number"), max_length=30, unique=True, editable=False, db_index=True,
        help_text=_("Unique, human-readable order identifier, e.g., ORD-YYYYMMDD-XXXXXX")
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL, # Keep order even if user is deleted for records
        null=True, blank=True, # Allow guest orders
        related_name='orders_placed',
        verbose_name=_("customer")
    )
    # Denormalized for easier querying, derived from restaurant.tenant
    tenant = models.ForeignKey(
        'users.Tenant', # String reference
        on_delete=models.PROTECT, # Protect tenant if orders exist
        related_name='tenant_orders',
        verbose_name=_("tenant")
    )
    restaurant = models.ForeignKey(
        'restaurants.Restaurant', # String reference
        on_delete=models.PROTECT, # Protect restaurant if orders exist
        related_name='restaurant_orders',
        verbose_name=_("restaurant")
    )

    status = models.CharField(
        _("order status"), max_length=30, choices=ORDER_STATUS_CHOICES,
        default='AWAITING_CONFIRMATION', db_index=True
    )
    order_type = models.CharField(_("order type"), max_length=20, choices=ORDER_TYPE_CHOICES)

    # Customer info snapshot (especially for guest checkout or if user details change)
    customer_name_snapshot = models.CharField(_("customer name (snapshot)"), max_length=255, blank=True, null=True)
    customer_phone_snapshot = models.CharField(_("customer phone (snapshot)"), max_    # Payment
    payment_status = models.CharField(
        _("payment status"), max_length=30, choices=PAYMENT_STATUS_CHOICES,
        default='PENDING', db_index=True
    )
    payment_method_snapshot = models.CharField(_("payment method (snapshot)"), max_length=50, blank=True, null=True)
    # Last successful/relevant payment transaction ID from payments app
    payment_transaction_ref = models.CharField(_("payment transaction reference"), max_length=255, blank=True, null=True, db_index=True)

    # Notes
    special_instructions_for_restaurant = models.TextField(_("special instructions for restaurant"), blank=True, null=True)
    internal_notes_for_staff = models.TextField(_("internal notes for staff"), blank=True, null=True) # Not visible to customer

    # POS/KDS Integration
    pos_order_id = models.CharField(_("POS Order ID"), max_length=100, blank=True, null=True, db_index=True)
    kds_token_number = models.CharField(_("KDS Token"), max_length=50, blank=True, null=True)

    # Timestamps
    # estimated_preparation_time_minutes: This is better stored dynamically or on the order based on items
    # scheduled_for_time: For pre-orders
    scheduled_for_time = models.DateTimeField(_("scheduled for time"), null=True, blank=True, help_text=_("If the order is scheduled for a future time."))
    preparation_time_estimate_minutes = models.PositiveSmallIntegerField(_("est. prep time (mins) by restaurant"), null=True, blank=True)
    # Actual operational timestamps
    confirmed_at = models.DateTimeField(_("confirmed by restaurant at"), null=True, blank=True)
    preparation_started_at = models.DateTimeField(_("preparation started at"), null=True, blank=True)
    ready_at = models.DateTimeField(_("ready for pickup/delivery at"), null=True, blank=True)
    picked_up_or_dispatched_at = models.DateTimeField(_("picked up / dispatched at"), null=True, blank=True)
    delivered_or_served_at = models.DateTimeField(_("delivered / served at"), null=True, blank=True) # For delivery or dine-in completion
    completed_at = models.DateTimeField(_("order fully completed at"), null=True, blank=True) # Final closure
    cancelled_at = models.DateTimeField(_("cancelled at"), null=True, blank=True)
    cancellation_reason = models.TextField(_("cancellation reason"), blank=True, null=True)

    created_at = models.DateTimeField(_("order placed at"), default=timezone.now, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("order")
        verbose_name_plural = _("orders")
        ordering = ['-created_at']

    def __str__(self):
        return f"Order {self.order_number} for {self.restaurant.name}"

    def _generate_order_number(self):
        # Example: ORD-YYYYMMDD-TenantInitial-ShortUUID (ensure uniqueness)
        # This needs a robust, concurrency-safe way to generate unique numbers.
        # For simplicity, a timestamp + part of UUID.
        timestamp_part = timezone.now().strftime('%Y%m%d%H%M%S')
        unique_part = str(self.id).split('-')[0][:4].upper() # First 4 chars of UUID part
        # A sequence per day per restaurant might be better for human readability
        # For now, this is globally unique enough.
        return f"ORD-{timestamp_part}-{unique_part}"

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = self._generate_order_number()
            # Ensure uniqueness in case of rare collision (unlikely with UUID part)
            while Order.objects.filter(order_number=self.order_number).exists():
                self.order_number = self._generate_order_number() # Regenerate

        # Denormalize tenant from restaurant if not set
        if self.restaurant and not self.tenant_id:
            self.tenant_id = self.restaurant.tenant_id
        super().save(*args, **kwargs)

    def calculate_totals_from_items(self, commit=False):
        """Calculates subtotal, and potentially total (excluding dynamic fees/taxes for now)."""
        subtotal = sum(item.line_total for item in self.items.all())
        self.subtotal_price = round(subtotal, 2)

        # Basic total calculation. Real-world needs tax, delivery fee based on ruleslength=30, blank=True, null=True)
    customer_email_snapshot = models.EmailField(_("customer email (snapshot)"), blank=True, null=True)

    # For Dine-In
    table_number = models.CharField(_("table number"), max_length=50, blank=True, null=True)
    # For Delivery
    delivery_address_line1 = models.CharField(_("delivery address line 1"), max_length=255, blank=True, null=True)
    delivery_address_line2 = models.CharField(_("delivery address line 2"), max_length=255, blank=True, null=True)
    delivery_city = models.CharField(_("delivery city"), max_length=100, blank=True, null=True)
    delivery_state_province = models.CharField(_("delivery state/province"), max_length=100, blank=True, null=True)
    delivery_postal_code = models.CharField(_("delivery postal code"), max_length=20, blank=True, null=True)
    delivery_country = models.CharField(_("delivery country"), max_length=100, blank=True, null=True) # Could be FK
    delivery_instructions = models.TextField(_("delivery instructions"), blank=True, null=True)
    delivery_latitude = models.DecimalField(_("delivery latitude"), max_digits=10, decimal_places=7, null=True, blank=True)
    delivery_longitude = models.DecimalField(_("delivery longitude"), max_digits=10, decimal_places=7, null=True, blank=True)


    # Financials
    subtotal_price = models.DecimalField(_("subtotal price"), max_digits=10, decimal_places=2)
    taxes_amount = models.DecimalField(_("taxes amount"), max_digits=10, decimal_places=2, default=0.00)
    delivery_fee_amount = models.DecimalField(_("delivery fee"), max_digits=8, decimal_places=2, default=0.00)
    service_charge_amount = models.DecimalField(_("service charge"), max_digits=8, decimal_places=2, default=0.00)
    discount_amount = models.DecimalField(_("discount amount"), max_digits=10, decimal_places=2, default=0.00)
    total_price = models.DecimalField(_("total price"), max_digits=10, decimal_places=2) # subtotal + taxes + delivery + service - discount

    # Payment related
    payment_status = models.CharField(
        _("payment status"), max_length=30, choices=PAYMENT_STATUS_CHOICES,
        default='PENDING', db_index=True
    )
    payment_method_snapshot = models.CharField(_("payment method (snapshot)"), max_length=50, blank=True, null=True)
    # The actual PaymentTransaction link is in the payments app.
    # This field can be updated upon successful PaymentTransaction.
    last_successful_payment_txn_id = models.CharField(_("last successful payment txn ID"), max_length=255, blank=True, null=True)


    # Notes
    special_instructions_for_restaurant = models.TextField(_("special instructions for restaurant"), blank=True, null=True)
    internal_notes_for_staff = models.TextField(_("internal notes for staff"), blank=True, null=True)

    # Estimated Times
    estimated_preparation_time_minutes = models.PositiveSmallIntegerField(_("est. prep time (mins)"), null=True, blank=True)
    # This is the time the customer expects it, not necessarily when the driver picks up
    estimated_delivery_or_pickup_time = models.DateTimeField(_("est. delivery/pickup time"), null=True, blank=True)

    # Actual Event Timestamps (set by system or staff actions)
    confirmed_at = models.DateTimeField(_("confirmed by restaurant at"), null=True, blank=True)
    preparation_started_at = models.DateTimeField(_("preparation started at"), null=True, blank=True)
    ready_for_pickup_at = models.DateTimeField(_("ready for pickup at"), null=True, blank=True) # For takeaway or driver pickup
    picked_up_by_driver_at = models.DateTimeField(_("picked up by driver at"), null=True, blank=True) # For delivery
    delivered_at = models.DateTimeField(_("delivered to customer at"), null=True, blank=True) # For delivery
    picked_up_by_customer_at = models.DateTimeField(_("picked up by customer at"), null=True, blank=True) # For takeaway
    completed_at = models.DateTimeField(_("order fully completed at"), null=True, blank=True) # Final completion
    cancelled_at = models.DateTimeField(_("cancelled at"), null=True, blank=True)
    cancellation_reason = models.TextField(_("cancellation reason"), blank=True, null=True)

    # For POS/KDS integration
    pos_order_id = models.CharField(_("POS Order ID"), max_length=100, blank=True, null=True, db_index=True)
    kds_token_number = models.CharField(_("KDS Token Number"), max_length=50, blank=True, null=True)

    created_at = models.DateTimeField(_(", discounts.
        current_total = self.subtotal_price + self.taxes_amount + self.delivery_fee + self.service_fee - self.discount_amount
        self.total_price = round(current_total, 2)

        if commit:
            self.save(update_fields=['subtotal_price', 'total_price'])


class OrderItem(models.Model):
    """
    An item within a placed order. This is a snapshot of the CartItem at the time of order.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items', verbose_name=_("order"))

    # Snapshot of menu item details
    menu_item_original_id = models.UUIDField(_("original menu item ID"), null=True, blank=True, help_text=_("Reference to the original MenuItem.id if it still exists"))
    menu_item_snapshot_name = models.CharField(_("menu item name (snapshot)"), max_length=255)
    menu_item_snapshot_description = models.TextField(_("description (snapshot)"), blank=True, null=True)

    quantity = models.PositiveIntegerField(_("quantity"))
    unit_price = models.DecimalField(
        _("unit price (at time of order)"), max_digits=10, decimal_places=2,
        help_text=_("Price of one unit including its customizations at time of order.")
    )
    selected_customizations_snapshot = models.JSONField(
        _("selected customizations (snapshot)"), default=list, blank=True,
        help_text=_("Snapshot of customizations: [{'group_name': X, 'option_name': Y, 'price_adjustment': Z}, ...]")
    )
    # For KDS/Restaurant: special instructions for this specific item by customer
    item_notes_by_customer = models.TextField(_("item specific notes by customer"), blank=True, null=True)
    # For Restaurant: internal notes for this item (e.g., "customer allergic to nuts, double check")
    item_notes_by_staff = models.TextField(_("item specific notes by staff"), blank=True, null=True)

    class Meta:
        verbose_name = _("order item")
        verbose_name_plural = _("order items")
        ordering = ['order'] # Order by order, then perhaps by an internal sequence or name

    def __str__(self):
        return f"{self.quantity} x {self.menu_item_snapshot_name} (Order: {self.order.order_number})"

    @property
    def line_total(self):
        return round(self.quantity * self.unit_price, 2)


class OrderStatusHistory(models.Model):
    """
    Tracks changes in an order's status for auditing.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='status_history', verbose_name=_("order"))
    status = models.CharField(_("status"), max_length=30, choices=Order.ORDER_STATUS_CHOICES)
    timestamp = models.DateTimeField(_("timestamp"), default=timezone.now)
    changed_by = models.ForeignKey( # User who changed the status (e.g., customer, restaurant staff, system)
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL, null=True, blank=True,
        related_name='order_status_changes_made'
    )
    comment = models.TextField(_("comment/reason for change"), blank=True, null=True)

    class Meta:
        verbose_name = _("order status history")
        verbose_name_plural = _("order status history entries")
        ordering = ['order', '-timestamp']

    def __str__(self):
        changer = self.changed_by.email if self.changed_by else "System"
        return f"Order {self.order.order_number} to {self.get_status_display()} by {changer} at {self.timestamp.strftime('%Y-%m-%d %H:%M')}"