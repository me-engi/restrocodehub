# backend/payments/permissions.py
from rest_framework import permissions
from orders.models import Order

class CanInitiatePaymentForOrder(permissions.BasePermission):
    """
    Allows access only if the user is the owner of the order
    for which payment is being initiated.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            # Could allow for guest payment initiation if order tied to session
            order_id = request.data.get('order_id') # Assuming order_id is in request data
            if order_id and request.session.session_key:
                try:
                    order = Order.objects.get(id=order_id)
                    # If order has no user, it might be a guest order linked to session.
                    # Complex logic: how do you verify guest owns this order via session?
                    # This needs careful design for guest payments.
                    # For now, let's assume authenticated users.
                    return False # Deny anonymous by default for this permission
                except Order.DoesNotExist:
                    return False
            return False
        return True # Authenticated user

    def has_object_permission(self, request, view, obj): # obj is the Order instance
        return obj.user == request.user


class IsPlatformAdminForPaymentAccess(permissions.BasePermission):
    """
    Allows platform admins to view/manage payment transactions.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and \
               (request.user.is_superuser or request.user.role == 'platform_admin')