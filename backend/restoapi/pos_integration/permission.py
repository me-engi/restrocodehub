# backend/pos_integration/permissions.py
from rest_framework import permissions

class IsTenantAdminAndOwnsRestaurantForPOSConfig(permissions.BasePermission):
    """
    Allows tenant admins to manage POS configurations for restaurants within their tenant.
    """
    def has_permission(self, request, view): # View-level, e.g., for list/create
        return request.user and request.user.is_authenticated and request.user.role == 'tenant_admin'

    def has_object_permission(self, request, view, obj): # Object-level, obj is RestaurantPOSConfiguration
        return obj.restaurant.tenant == request.user.tenant

class IsPlatformAdminForPOSAccess(permissions.BasePermission):
    """
    Allows platform admins full access to POS configurations and logs.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and \
               (request.user.is_superuser or request.user.role == 'platform_admin')