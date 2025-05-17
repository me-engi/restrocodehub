# backend/orders/permissions.py
from rest_framework import permissions
from .models import Cart, Order # Assuming Cart and Order are in the same app

class IsCartOwner(permissions.BasePermission):
    """
    Allows access only if the request.user is the owner of the cart,
    or if it's an anonymous cart and the session matches.
    """
    def has_object_permission(self, request, view, obj: Cart):
        if request.user.is_authenticated:
            return obj.user == request.user
        # For anonymous carts, check session_key
        return obj.session_key and obj.session_key == request.session.session_key

class IsOrderOwner(permissions.BasePermission):
    """
    Allows access only if the request.user is the owner of the order.
    """
    def has_object_permission(self, request, view, obj: Order):
        if not request.user or not request.user.is_authenticated:
            return False # Order owner must be authenticated
        return obj.user == request.user

class IsRestaurantStaffForOrder(permissions.BasePermission):
    """
    Allows access if the user is staff of the tenant owning the restaurant of the order.
    Further role checks might be needed for specific actions (e.g., only manager can refund).
    """
    def has_permission(self, request, view): # View-level for listing orders for a restaurant
        return request.user and request.user.is_authenticated and \
               request.user.role in ['tenant_admin', 'restaurant_manager', 'pos_operator', 'chef'] # Add relevant roles

    def has_object_permission(self, request, view, obj: Order): # Object-level for specific order
        if not request.user or not request.user.is_authenticated:
            return False
        # User must belong to the same tenant as the order's restaurant's tenant
        # And have an appropriate role
        return obj.restaurant.tenant == request.user.tenant and \
               request.user.role in ['tenant_admin', 'restaurant_manager', 'pos_operator', 'chef']

class CanUpdateOrderStatus(permissions.BasePermission):
    """
    Allows only restaurant staff/admin or platform admin to update critical order status fields.
    """
    def has_object_permission(self, request, view, obj: Order): # obj is Order
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_superuser or request.user.role == 'platform_admin':
            return True
        return obj.restaurant.tenant == request.user.tenant and \
               request.user.role in ['tenant_admin', 'restaurant_manager', 'pos_operator'] # Define roles that can update status