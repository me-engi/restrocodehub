# backend/restaurants/permissions.py
from rest_framework import permissions

class IsTenantAdminAndOwnsRestaurant(permissions.BasePermission):
    """
    Allows access only to tenant admins for restaurants belonging to their tenant.
    """
    def has_permission(self, request, view): # View-level check
        return request.user and request.user.is_authenticated and request.user.role == 'tenant_admin'

    def has_object_permission(self, request, view, obj): # Object-level check
        # obj is the Restaurant instance
        return obj.tenant == request.user.tenant

class IsPlatformAdminOrReadOnly(permissions.BasePermission):
    """
    Allows platform admins full access, others read-only.
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS: # GET, HEAD, OPTIONS
            return True
        return request.user and request.user.is_authenticated and \
               (request.user.is_superuser or request.user.role == 'platform_admin')

    def has_object_permission(self, request, view, obj): # Object-level check
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_authenticated and \
               (request.user.is_superuser or request.user.role == 'platform_admin')