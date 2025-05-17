# backend/menu/permissions.py
from rest_framework import permissions
from restaurants.models import Restaurant # To check tenant ownership of the restaurant

class IsTenantAdminAndOwnsRestaurantForMenu(permissions.BasePermission):
    """
    Allows access only to tenant admins for menu items/categories
    belonging to a restaurant owned by their tenant.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'tenant_admin'

    def has_object_permission(self, request, view, obj):
        # obj can be MenuCategory, MenuItem, CustomizationGroup, CustomizationOption
        # We need to trace back to the restaurant and then to the tenant.
        restaurant_obj = None
        if hasattr(obj, 'restaurant'): # MenuCategory, MenuItem
            restaurant_obj = obj.restaurant
        elif hasattr(obj, 'menu_item') and hasattr(obj.menu_item, 'restaurant'): # CustomizationGroup
            restaurant_obj = obj.menu_item.restaurant
        elif hasattr(obj, 'group') and hasattr(obj.group, 'menu_item') and hasattr(obj.group.menu_item, 'restaurant'): # CustomizationOption
            restaurant_obj = obj.group.menu_item.restaurant
        
        if restaurant_obj:
            return restaurant_obj.tenant == request.user.tenant
        return False # Should not happen if objects are correctly fetched

class IsPlatformAdminOrReadOnlyForMenu(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_authenticated and \
               (request.user.is_superuser or request.user.role == 'platform_admin')

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_authenticated and \
               (request.user.is_superuser or request.user.role == 'platform_admin')