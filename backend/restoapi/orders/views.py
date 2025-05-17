# backend/orders/views.py
from django.db import transaction as db_transaction # Alias to avoid name conflict
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import viewsets, generics, status, views
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend

from .models import Cart, CartItem, Order, OrderItem, OrderStatusHistory
from .serializers import (
    CartDetailSerializer, AddToCartRequestSerializer, UpdateCartItemRequestSerializer,
    OrderListSerializer, OrderDetailSerializer, OrderCreateRequestSerializer, OrderStaffUpdateSerializer,
    OrderStatusHistoryDisplaySerializer # For potential use if needed separately
)
from menu.models import MenuItem, CustomizationOption
from restaurants.models import Restaurant
from .permissions import IsCartOwner, IsOrderOwner, IsRestaurantStaffForOrder, CanUpdateOrderStatus
from users.permissions import IsPlatformAdmin, IsTenantAdmin # Assuming from users.permissions

# --- Helper Function to Get/Create Cart ---
def get_or_create_active_cart(request):
    """
    Retrieves or creates an active cart for the current user or session.
    An active cart means it's not yet converted to an order.
    """
    cart = None
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
    else:
        session_key = request.session.session_key
        if not session_key:
            request.session.create() # Ensure session exists
            session_key = request.session.session_key
        # For anonymous users, ensure user is None. If a cart exists for this session_key
        # but has a user_id (e.g., user logged out but session cart remained),
        # it might be better to create a new session cart or clear the user_id from it.
        # For simplicity here, we assume session_key implies user is None.
        cart, created = Cart.objects.get_or_create(session_key=session_key, defaults={'user': None})
        if not created and cart.user: # If an old cart for this session now has a user (edge case)
            request.session.create() # Force new session
            cart = Cart.objects.create(session_key=request.session.session_key, user=None)

    return cart

# --- Cart Views ---

class CartDetailView(generics.RetrieveAPIView):
    """
    Retrieve the current user's or session's cart.
    GET /api/orders/cart/
    """
    serializer_class = CartDetailSerializer
    permission_classes = [AllowAny] # Cart can be accessed by anonymous users via session

    def get_object(self):
        cart = get_or_create_active_cart(self.request)
        # Manually check permission for Retrieve as get_object is called before has_object_permission for RetrieveAPIView
        # self.check_object_permissions(self.request, cart) # Not strictly needed if get_or_create_active_cart ensures right cart
        return cart

class AddItemToCartView(views.APIView):
    """
    Add an item to the cart or update its quantity if already exists with same config.
    POST /api/orders/cart/add-item/
    Request: { "menu_item_id": "uuid", "quantity": 1, "selected_option_ids": ["uuid1"], "restaurant_id": "uuid" }
    """
    permission_classes = [AllowAny]
    serializer_class = AddToCartRequestSerializer # For request validation

    @db_transaction.atomic
    def post(self, request, *args, **kwargs):
        cart = get_or_create_active_cart(request)
        serializer = AddToCartRequestSerializer(data=request.data, context={'request': request}) # Pass request for context
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        validated_data = serializer.validated_data
        menu_item = serializer.context['menu_item_instance'] # Fetched during validation
        restaurant = serializer.context['restaurant_instance'] # Fetched during validation
        quantity = validated_data['quantity']
        selected_option_ids = validated_data.get('selected_option_ids', [])

        # --- Restaurant consistency check for cart ---
        if cart.restaurant and cart.restaurant != restaurant:
            return Response({
                "error": "Cannot add items from different restaurants to the same cart. "
                         "Please clear your cart or complete your current order first."
            }, status=status.HTTP_400_BAD_REQUEST)
        elif not cart.restaurant:
            cart.restaurant = restaurant
            # No need to save cart yet, Cart.add_item will update and save cart.updated_at

        try:
            # Use the Cart model's add_item method for robust logic
            cart.add_item(
                menu_item=menu_item,
                quantity=quantity,
                selected_customization_options=selected_option_ids # Pass IDs, add_item resolves to instances
            )
        except ValueError as e: # Catch validation errors from add_item
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e: # Catch unexpected errors
            # Log this exception: logger.error(f"Error adding item to cart: {e}")
            return Response({"error": "An unexpected error occurred."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        cart_serializer = CartDetailSerializer(cart, context={'request': request})
        return Response(cart_serializer.data, status=status.HTTP_200_OK)


class CartItemUpdateDeleteView(generics.UpdateAPIView, generics.DestroyAPIView):
    """
    Update quantity or remove a specific item from the cart.
    PATCH /api/orders/cart/items/{cart_item_id}/ (Update quantity)
    DELETE /api/orders/cart/items/{cart_item_id}/ (Remove item)
    """
    serializer_class = UpdateCartItemRequestSerializer # For request body of update
    permission_classes = [IsCartOwner] # Ensures user owns the cart of the item
    lookup_url_kwarg = 'cart_item_id' # Matches URL pattern

    def get_queryset(self):
        cart = get_or_create_active_cart(self.request)
        return CartItem.objects.filter(cart=cart) # Ensures item belongs to current user's cart

    def get_object(self):
        obj = super().get_object()
        # IsCartOwner permission class will also run has_object_permission on the cart of this item.
        # Or, we can check explicitly:
        # if obj.cart != get_or_create_active_cart(self.request):
        #     raise PermissionDenied("This item does not belong to your active cart.")
        return obj

    def update(self, request, *args, **kwargs): # Handles PUT and PATCH
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        new_quantity = serializer.validated_data.get('quantity')

        if new_quantity == 0: # If quantity is 0, delete the item
            self.perform_destroy(instance)
            return Response(status=status.HTTP_204_NO_CONTENT)
        
        instance.quantity = new_quantity
        instance.save(update_fields=['quantity'])
        
        # Return the updated cart
        cart = get_or_create_active_cart(request)
        cart_serializer = CartDetailSerializer(cart, context={'request': request})
        return Response(cart_serializer.data, status=status.HTTP_200_OK)

    def perform_destroy(self, instance):
        cart = instance.cart
        instance.delete()
        cart.updated_at = timezone.now() # Trigger cart update timestamp
        cart.save(update_fields=['updated_at'])
        # If cart becomes empty, optionally reset its restaurant
        if not cart.items.exists():
            cart.restaurant = None
            cart.save(update_fields=['restaurant'])


class ClearCartView(views.APIView):
    """
    Clear all items from the current user's/session's cart.
    POST /api/orders/cart/clear/
    """
    permission_classes = [AllowAny] # Action is on the current cart

    def post(self, request, *args, **kwargs):
        cart = get_or_create_active_cart(request)
        cart.clear() # Model method
        cart_serializer = CartDetailSerializer(cart, context={'request': request})
        return Response(cart_serializer.data, status=status.HTTP_200_OK)


# --- Order Views ---

class OrderCreateView(generics.CreateAPIView):
    """
    Place an order using items from the current user's/session's cart.
    POST /api/orders/place-order/
    Request body defined by OrderCreateRequestSerializer.
    """
    serializer_class = OrderCreateRequestSerializer
    permission_classes = [IsAuthenticated] # Or AllowAny if guest checkout fully implemented

    @db_transaction.atomic
    def perform_create(self, serializer):
        cart = get_or_create_active_cart(self.request)
        if not cart.items.exists():
            from rest_framework.exceptions import ValidationError
            raise ValidationError({"cart": "Your cart is empty. Cannot place an order."})
        if not cart.restaurant:
            from rest_framework.exceptions import ValidationError
            raise ValidationError({"cart": "Cart is not associated with a restaurant."})

        # Ensure the restaurant in serializer (if any) matches cart's restaurant
        validated_data = serializer.validated_data
        if validated_data.get('restaurant_id') and validated_data['restaurant_id'] != cart.restaurant_id:
            from rest_framework.exceptions import ValidationError
            raise ValidationError({"restaurant_id": "Restaurant ID in request does not match the cart's restaurant."})

        user = self.request.user if self.request.user.is_authenticated else None

        # Prepare customer snapshot details
        customer_name = validated_data.get('customer_name') or (user.name if user else None)
        customer_phone = validated_data.get('customer_phone') or (user.phone_number if user and hasattr(user, 'phone_number') else None)
        customer_email = validated_data.get('customer_email') or (user.email if user else None)

        if not customer_email and not user: # Guest orders must provide an email
            from rest_framework.exceptions import ValidationError
            raise ValidationError({"customer_email": "Email is required for guest orders."})

        # Create the Order
        order = Order.objects.create(
            user=user,
            restaurant=cart.restaurant,
            tenant=cart.restaurant.tenant,
            order_type=validated_data['order_type'],
            status='AWAITING_CONFIRMATION', # Or PENDING_PAYMENT if payment is next
            payment_status='PENDING',
            customer_name_snapshot=customer_name,
            customer_phone_snapshot=customer_phone,
            customer_email_snapshot=customer_email,
            table_number=validated_data.get('table_number'),
            delivery_address_line1=validated_data.get('delivery_address_line1'),
            delivery_address_line2=validated_data.get('delivery_address_line2'),
            delivery_city=validated_data.get('delivery_city'),
            delivery_state_province=validated_data.get('delivery_state_province'),
            delivery_postal_code=validated_data.get('delivery_postal_code'),
            delivery_country=validated_data.get('delivery_country'),
            delivery_instructions=validated_data.get('delivery_instructions'),
            special_instructions_for_restaurant=validated_data.get('special_instructions_for_restaurant'),
            scheduled_for_time=validated_data.get('scheduled_for_time')
            # Order number is auto-generated on Order.save()
        )

        # Create OrderItems from CartItems
        order_items_to_create = []
        for cart_item in cart.items.all():
            order_items_to_create.append(
                OrderItem(
                    order=order,
                    menu_item_snapshot_name=cart_item.menu_item.name,
                    menu_item_original=cart_item.menu_item, # Link to original
                    original_menu_item_id_str=str(cart_item.menu_item.id),
                    quantity=cart_item.quantity,
                    unit_price=cart_item.unit_price_at_addition,
                    selected_customizations_snapshot=cart_item.selected_customizations_snapshot,
                    # item_notes can be added later or from a cart_item field
                )
            )
        OrderItem.objects.bulk_create(order_items_to_create)

        order.calculate_and_set_financials(commit=True) # Calculate totals and save order again

        # Create initial status history
        OrderStatusHistory.objects.create(
            order=order, status=order.status,
            changed_by=user, # Or a system user
            notes="Order placed by customer."
        )

        # Clear the cart after successful order creation
        cart.clear()

        # --- TODO: Trigger payment process if not COD/post-pay ---
        # If validated_data.get('payment_method_hint') == 'ONLINE' or similar:
        #    initiate_payment_for_order(order) -> this would call payments app logic

        # --- TODO: Send order to POS system (e.g., via a Celery task) ---
        # from ..pos_integration.tasks import send_order_to_pos_task
        # send_order_to_pos_task.delay(order.id)

        # --- TODO: Send order confirmation email/notification to customer ---

        # Set the instance for the serializer response
        serializer.instance = order


class OrderListViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Common base for listing and retrieving orders with role-based filtering.
    - Customers see their own orders.
    - Restaurant Staff see orders for their assigned restaurant(s)/tenant.
    - Platform Admins see all orders.
    """
    filter_backends = [DjangoFilterBackend]
    filterset_fields = {
        'status': ['exact', 'in'],
        'order_type': ['exact'],
        'payment_status': ['exact'],
        'created_at': ['date', 'date__gte', 'date__lte'],
        'restaurant': ['exact'] # Useful for platform admin or staff managing multiple restaurants
    }
    search_fields = ['order_number', 'user__email', 'customer_name_snapshot', 'restaurant__name']

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Order.objects.none() # No orders for anonymous users via this endpoint

        if user.is_superuser or user.role == 'platform_admin':
            return Order.objects.all().select_related('user', 'restaurant', 'tenant').prefetch_related('items')
        elif user.role in ['tenant_admin', 'restaurant_manager', 'pos_operator', 'chef']:
            # Staff see orders for all restaurants within their tenant.
            # More granular: filter by specific restaurants they are assigned to if that model exists.
            return Order.objects.filter(tenant=user.tenant).select_related('user', 'restaurant').prefetch_related('items')
        else: # Regular customer
            return Order.objects.filter(user=user).select_related('restaurant').prefetch_related('items')

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return OrderDetailSerializer
        return OrderListSerializer

    def get_permissions(self):
        # All actions here require authentication.
        # Object-level permissions will be checked by IsOrderOwner or IsRestaurantStaffForOrder for retrieve.
        return [IsAuthenticated()]

    # Custom action for a customer to cancel their own PENDING order
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsOrderOwner], url_path='cancel-my-order')
    def cancel_my_order(self, request, pk=None):
        order = self.get_object() # Checks IsOrderOwner
        cancellation_reason = request.data.get('reason', "Cancelled by customer before confirmation.")

        if order.status != 'AWAITING_CONFIRMATION':
            return Response(
                {"error": f"Order cannot be cancelled by you in its current status: {order.get_status_display()}."},
                status=status.HTTP_400_BAD_REQUEST
            )

        with db_transaction.atomic():
            old_status = order.status
            order.status = 'CANCELLED_BY_USER'
            order.cancelled_at = timezone.now()
            order.cancellation_reason = cancellation_reason
            order.save(update_fields=['status', 'cancelled_at', 'cancellation_reason', 'updated_at'])

            OrderStatusHistory.objects.create(
                order=order, status=order.status, changed_by=request.user, notes=cancellation_reason
            )
            # TODO: Notify restaurant POS about cancellation if order was already sent.
        return Response(OrderDetailSerializer(order, context={'request': request}).data)


class OrderStaffUpdateView(generics.UpdateAPIView):
    """
    For restaurant staff/admins to update an order's status and operational details.
    PATCH /api/orders/staff-update/{order_id}/
    """
    queryset = Order.objects.all()
    serializer_class = OrderStaffUpdateSerializer
    permission_classes = [IsAuthenticated, IsRestaurantStaffForOrder, CanUpdateOrderStatus] # Check user role and tenant
    lookup_field = 'id'
    lookup_url_kwarg = 'order_id'

    @db_transaction.atomic
    def perform_update(self, serializer):
        order = serializer.instance # Original order instance
        old_status = order.status
        new_status = serializer.validated_data.get('status', old_status)

        # Business logic for valid status transitions (can be complex)
        # Example: Can only move to PREPARING from CONFIRMED
        valid_transitions = {
            'AWAITING_CONFIRMATION': ['CONFIRMED', 'CANCELLED_BY_RESTAURANT'],
            'CONFIRMED': ['PREPARING', 'CANCELLED_BY_RESTAURANT'],
            'PREPARING': ['READY_FOR_PICKUP', 'OUT_FOR_DELIVERY', 'CANCELLED_BY_RESTAURANT'],
            'READY_FOR_PICKUP': ['COMPLETED', 'OUT_FOR_DELIVERY', 'CANCELLED_BY_RESTAURANT'], # Latter if mistaken
            'OUT_FOR_DELIVERY': ['DELIVERED', 'FAILED_DELIVERY_ATTEMPT'], # FAILED_DELIVERY_ATTEMPT could be a new status
            # ... more ...
        }
        if old_status != new_status and new_status not in valid_transitions.get(old_status, []):
            from rest_framework.exceptions import ValidationError
            raise ValidationError(f"Invalid status transition from '{order.get_status_display()}' to '{new_status}'.")


        # Set timestamp fields based on new status
        now = timezone.now()
        update_fields_for_order = ['status', 'updated_at']
        if new_status != old_status: # Only update if status actually changed
            if new_status == 'CONFIRMED' and not order.confirmed_at:
                order.confirmed_at = now
                update_fields_for_order.append('confirmed_at')
            elif new_status == 'PREPARING' and not order.preparation_started_at:
                order.preparation_started_at = now
                update_fields_for_order.append('preparation_started_at')
            # ... add all other status-timestamp updates ...
            elif new_status == 'COMPLETED' and not order.completed_at:
                order.completed_at = now # Final completion
                update_fields_for_order.append('completed_at')
                # If dine-in or takeaway and paid, this is it.
                # If delivery, this means customer received it.
                if order.order_type == 'DELIVERY' and not order.delivered_at:
                    order.delivered_at = now
                    update_fields_for_order.append('delivered_at')
                elif order.order_type == 'TAKEAWAY' and not order.picked_up_by_customer_at:
                    order.picked_up_by_customer_at = now
                    update_fields_for_order.append('picked_up_by_customer_at')

            elif new_status.startswith('CANCELLED_') and not order.cancelled_at:
                order.cancelled_at = now
                update_fields_for_order.append('cancelled_at')
                # Ensure cancellation_reason is saved if provided by serializer
                if 'cancellation_reason' in serializer.validated_data:
                    update_fields_for_order.append('cancellation_reason')

        # Save other fields from serializer
        updated_order = serializer.save() # This saves what's in OrderStaffUpdateSerializer.Meta.fields

        # Save the status-specific timestamps if status changed
        if old_status != new_status:
            updated_order.save(update_fields=list(set(update_fields_for_order))) # Use set to avoid duplicates

            OrderStatusHistory.objects.create(
                order=updated_order, status=new_status,
                changed_by=self.request.user,
                notes=f"Status changed to {updated_order.get_status_display()} by staff. Reason: {updated_order.cancellation_reason or 'N/A'}"
            )
            # TODO: Notify customer of status change
            # TODO: Update POS if status change originated from your platform admin (if applicable)