# backend/orders/serializers.py
from rest_framework import serializers
from django.db import transaction
from django.utils import timezone
from .models import Cart, CartItem, Order, OrderItem, OrderStatusHistory
from menu.models import MenuItem, CustomizationOption, CustomizationGroup # For validation and price calculation
from restaurants.models import Restaurant # For validation
from users.serializers import UserSlimSerializer # Assuming a slim serializer for user details display

# --- Helper Serializer for Customizations (Display Only in most cases) ---
class OrderItemCustomizationSnapshotSerializer(serializers.Serializer):
    # This mirrors the structure stored in CartItem.selected_customizations_snapshot
    # and OrderItem.selected_customizations_snapshot
    # Primarily for read-only display within OrderItem or CartItem serializers.
    group_name = serializers.CharField(read_only=True)
    option_name = serializers.CharField(read_only=True)
    price_adjustment = serializers.DecimalField(max_digits=8, decimal_places=2, read_only=True)
    # option_id = serializers.UUIDField(read_only=True) # Optional to include for reference
    # group_id = serializers.UUIDField(read_only=True) # Optional

# --- Cart Serializers ---

class CartItemDisplaySerializer(serializers.ModelSerializer):
    """For displaying items within a cart."""
    menu_item_name = serializers.CharField(source='menu_item.name', read_only=True)
    menu_item_image_url = serializers.ImageField(source='menu_item.image', read_only=True, allow_null=True)
    line_total = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    selected_customizations_snapshot = OrderItemCustomizationSnapshotSerializer(many=True, read_only=True)

    class Meta:
        model = CartItem
        fields = [
            'id', 'menu_item', 'menu_item_name', 'menu_item_image_url', 'quantity',
            'selected_customizations_snapshot', 'unit_price_at_addition', 'line_total'
        ]
        read_only_fields = ['id', 'menu_item_name', 'menu_item_image_url', 'line_total', 'unit_price_at_addition', 'selected_customizations_snapshot']
        # menu_item (ID) and quantity are writable for add/update operations.


class CartDetailSerializer(serializers.ModelSerializer):
    """For viewing the entire cart detail."""
    items = CartItemDisplaySerializer(many=True, read_only=True)
    subtotal_price = serializers.DecimalField(source='get_subtotal_price', max_digits=10, decimal_places=2, read_only=True)
    item_count = serializers.IntegerField(source='get_item_count', read_only=True)
    restaurant_name = serializers.CharField(source='restaurant.name', read_only=True, allow_null=True)
    restaurant_slug = serializers.SlugField(source='restaurant.slug', read_only=True, allow_null=True)

    class Meta:
        model = Cart
        fields = [
            'id', 'user', 'session_key', 'restaurant', 'restaurant_name', 'restaurant_slug',
            'items', 'subtotal_price', 'item_count', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'session_key', 'updated_at', 'subtotal_price', 'item_count', 'restaurant_name', 'restaurant_slug']
        # 'restaurant' can be set implicitly when the first item is added.

# --- Serializers for Cart Actions (Request Payloads) ---

class AddToCartRequestSerializer(serializers.Serializer):
    menu_item_id = serializers.UUIDField()
    quantity = serializers.IntegerField(min_value=1, default=1)
    selected_option_ids = serializers.ListField(
        child=serializers.UUIDField(), required=False, default=list,
        help_text="List of CustomizationOption IDs selected by the user."
    )
    restaurant_id = serializers.UUIDField(write_only=True, help_text="Restaurant ID must be provided when adding the first item or changing restaurants.")

    def validate_menu_item_id(self, value):
        try:
            menu_item = MenuItem.objects.select_related('restaurant').get(id=value)
            if not menu_item.effective_is_available: # Using the model property
                raise serializers.ValidationError(f"Menu item '{menu_item.name}' is currently unavailable.")
            self.context['menu_item_instance'] = menu_item # Pass instance to view
        except MenuItem.DoesNotExist:
            raise serializers.ValidationError("Invalid menu item ID.")
        return value

    def validate_restaurant_id(self, value):
        try:
            restaurant = Restaurant.objects.get(id=value, is_operational=True)
            self.context['restaurant_instance'] = restaurant
        except Restaurant.DoesNotExist:
            raise serializers.ValidationError("Invalid or non-operational restaurant ID.")
        return value

    def validate(self, data):
        # Ensure selected options are valid for the menu item
        menu_item = self.context.get('menu_item_instance')
        selected_option_ids = data.get('selected_option_ids', [])

        if menu_item and selected_option_ids:
            valid_options_for_item = CustomizationOption.objects.filter(
                group__menu_item=menu_item,
                id__in=selected_option_ids,
                is_available=True
            )
            if len(valid_options_for_item) != len(set(selected_option_ids)):
                raise serializers.ValidationError("One or more selected customization options are invalid or unavailable for this menu item.")

            # Further validation for min/max selections per group can be added here
            # This involves checking CustomizationGroup rules for the selected options.
            # Example (simplified - needs more robust group validation):
            options_by_group = {}
            for opt in valid_options_for_item.select_related('group'):
                options_by_group.setdefault(opt.group, []).append(opt)

            for group, selected_opts_in_group in options_by_group.items():
                if len(selected_opts_in_group) < group.min_selection:
                    raise serializers.ValidationError(f"Minimum {group.min_selection} selections required for group '{group.name}'.")
                if group.max_selection > 0 and len(selected_opts_in_group) > group.max_selection: # 0 for unlimited
                    raise serializers.ValidationError(f"Maximum {group.max_selection} selections allowed for group '{group.name}'.")
        return data

class UpdateCartItemRequestSerializer(serializers.Serializer):
    quantity = serializers.IntegerField(min_value=0) # min_value=0 allows removing item by setting qty to 0


# --- Order Serializers ---

class OrderItemDisplaySerializer(serializers.ModelSerializer):
    """For displaying items within an order."""
    # menu_item_original_name = serializers.CharField(source='menu_item_original.name', read_only=True, allow_null=True)
    selected_customizations_snapshot = OrderItemCustomizationSnapshotSerializer(many=True, read_only=True)
    line_total = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = OrderItem
        fields = [
            'id', 'menu_item_snapshot_name', #'menu_item_original', 'menu_item_original_name',
            'original_menu_item_id_str', # For frontend to potentially link back if needed
            'quantity', 'unit_price', 'selected_customizations_snapshot', 'item_notes', 'line_total'
        ]

class OrderStatusHistoryDisplaySerializer(serializers.ModelSerializer):
    changed_by_email = serializers.EmailField(source='changed_by.email', read_only=True, allow_null=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = OrderStatusHistory
        fields = ['id', 'status', 'status_display', 'timestamp', 'changed_by_email', 'notes']


class OrderListSerializer(serializers.ModelSerializer):
    """For listing orders (customer's history or staff view)."""
    restaurant_name = serializers.CharField(source='restaurant.name', read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True, allow_null=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    order_type_display = serializers.CharField(source='get_order_type_display', read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'user_email', 'restaurant', 'restaurant_name',
            'status', 'status_display', 'order_type', 'order_type_display',
            'total_price', 'created_at'
        ]

class OrderDetailSerializer(OrderListSerializer): # Extends list serializer
    """For detailed view of an order."""
    items = OrderItemDisplaySerializer(many=True, read_only=True)
    status_history = OrderStatusHistoryDisplaySerializer(many=True, read_only=True)
    tenant_name = serializers.CharField(source='tenant.name', read_only=True)
    payment_status_display = serializers.CharField(source='get_payment_status_display', read_only=True)
    # Use UserSlimSerializer if you want to nest more user details
    # user = UserSlimSerializer(read_only=True)

    class Meta(OrderListSerializer.Meta): # Inherit fields from OrderListSerializer
        fields = OrderListSerializer.Meta.fields + [
            'tenant', 'tenant_name',
            'customer_name_snapshot', 'customer_phone_snapshot', 'customer_email_snapshot',
            'table_number',
            'delivery_address_line1', 'delivery_address_line2', 'delivery_city',
            'delivery_state_province', 'delivery_postal_code', 'delivery_country',
            'delivery_instructions',
            'subtotal_price', 'taxes_amount', 'delivery_fee_amount', 'service_charge_amount',
            'discount_amount', # total_price is already in OrderListSerializer
            'payment_status', 'payment_status_display', 'payment_method_snapshot', 'last_successful_payment_txn_id',
            'special_instructions_for_restaurant', 'internal_notes_for_staff',
            'estimated_preparation_time_minutes', 'estimated_delivery_or_pickup_time',
            'confirmed_at', 'preparation_started_at', 'ready_for_pickup_at',
            'picked_up_by_driver_at', 'delivered_at', 'picked_up_by_customer_at',
            'completed_at', 'cancelled_at', 'cancellation_reason',
            'pos_order_id', 'kds_token_number',
            'updated_at', 'items', 'status_history'
        ]


class OrderCreateRequestSerializer(serializers.Serializer): # For customer placing an order
    """
    Validates data needed to create an order from a cart or direct input.
    The actual creation logic using this data will be in the view.
    """
    cart_id = serializers.UUIDField(required=False, allow_null=True, help_text="ID of the cart to convert to an order. If not provided, implies direct order or items are passed differently.")
    # Direct items can be added here if not using cart_id:
    # direct_items = AddToCartRequestSerializer(many=True, required=False)

    order_type = serializers.ChoiceField(choices=Order.ORDER_TYPE_CHOICES)
    restaurant_id = serializers.UUIDField(help_text="The restaurant for this order. Must match cart's restaurant if cart_id is used.")

    # Customer info (optional if user is authenticated and profile is used)
    customer_name = serializers.CharField(max_length=255, required=False, allow_blank=True)
    customer_phone = serializers.CharField(max_length=30, required=False, allow_blank=True)
    customer_email = serializers.EmailField(required=False, allow_blank=True) # For guest checkout

    # Conditional fields based on order_type
    table_number = serializers.CharField(max_length=50, required=False, allow_blank=True)
    delivery_address_line1 = serializers.CharField(max_length=255, required=False, allow_blank=True)
    delivery_address_line2 = serializers.CharField(max_length=255, required=False, allow_blank=True)
    delivery_city = serializers.CharField(max_length=100, required=False, allow_blank=True)
    delivery_state_province = serializers.CharField(max_length=100, required=False, allow_blank=True)
    delivery_postal_code = serializers.CharField(max_length=20, required=False, allow_blank=True)
    delivery_country = serializers.CharField(max_length=100, required=False, allow_blank=True)
    delivery_instructions = serializers.CharField(required=False, allow_blank=True)
    # delivery_latitude, delivery_longitude (optional)

    special_instructions_for_restaurant = serializers.CharField(required=False, allow_blank=True)
    payment_method_hint = serializers.CharField(required=False, allow_blank=True, help_text="Hint for payment method, e.g., 'COD', 'ONLINE'")
    scheduled_for_time = serializers.DateTimeField(required=False, allow_null=True)

    def validate_restaurant_id(self, value):
        try:
            restaurant = Restaurant.objects.get(id=value, is_operational=True)
            self.context['restaurant_instance'] = restaurant
        except Restaurant.DoesNotExist:
            raise serializers.ValidationError("Invalid or non-operational restaurant ID.")
        return value

    def validate_cart_id(self, value):
        if value: # Only validate if provided
            try:
                cart = Cart.objects.prefetch_related('items').get(id=value)
                if not cart.items.exists():
                    raise serializers.ValidationError("Cannot place an order from an empty cart.")

                # Ensure cart belongs to the request.user or session (handled in view)
                # Ensure cart.restaurant matches the provided restaurant_id (or set restaurant_id from cart)
                self.context['cart_instance'] = cart
            except Cart.DoesNotExist:
                raise serializers.ValidationError("Invalid Cart ID.")
        return value

    def validate(self, data):
        order_type = data.get('order_type')
        restaurant = self.context.get('restaurant_instance')
        cart = self.context.get('cart_instance')

        if cart and restaurant and cart.restaurant != restaurant:
            raise serializers.ValidationError("Cart's restaurant does not match the specified restaurant for the order.")
        if not cart and not data.get('direct_items'): # If not using cart, items must be passed some other way
             pass # For now, we assume cart_id will be primary way

        if order_type == 'DINE_IN' and not data.get('table_number'):
            # Table number might be optional until assigned by staff, depending on workflow
            # raise serializers.ValidationError({"table_number": "Table number is required for dine-in orders."})
            pass
        if order_type == 'DELIVERY':
            required_delivery_fields = ['delivery_address_line1', 'delivery_city', 'delivery_postal_code', 'delivery_country']
            for field in required_delivery_fields:
                if not data.get(field):
                    raise serializers.ValidationError({field: f"{field.replace('_', ' ').title()} is required for delivery orders."})
        return data


class OrderStaffUpdateSerializer(serializers.ModelSerializer):
    """For staff to update order status and related operational fields."""
    class Meta:
        model = Order
        fields = [
            'status', # Staff can change this based on business rules
            'internal_notes_for_staff',
            'pos_order_id',
            'kds_token_number',
            'preparation_time_estimate_minutes',
            'estimated_delivery_or_pickup_time',
            'confirmed_at', # These timestamps might be set by system or staff
            'preparation_started_at',
            'ready_for_pickup_at',
            'picked_up_by_driver_at',
            'delivered_at',
            'picked_up_by_customer_at',
            'completed_at',
            'cancelled_at',
            'cancellation_reason'
        ]
        # Validation for status transitions should be in the view or model's save()