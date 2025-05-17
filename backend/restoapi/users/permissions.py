# backend/users/permissions.py
from rest_framework import permissions

class IsPlatformAdmin(permissions.BasePermission):
    """
    Allows access only to platform admin users (superuser or specific role).
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and \
               (request.user.is_superuser or request.user.role == 'platform_admin')

class IsTenantAdmin(permissions.BasePermission):
    """
    Allows access only to users who are admins of their tenant.
    Checks request.user.role == 'tenant_admin'.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'tenant_admin'

class IsTenantAdminOrOwnerOfObject(permissions.BasePermission):
    """
    Allows tenant admins to access/modify objects within their tenant,
    or if the request.user is the 'owner' of the object (if applicable, e.g., user profile).
    This is a more generic object-level permission.
    """
    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        # Platform admins can do anything
        if request.user.is_superuser or request.user.role == 'platform_admin':
            return True
        # Tenant admin can manage objects within their tenant
        if request.user.role == 'tenant_admin':
            # Check if the object's tenant matches the user's tenant
            if hasattr(obj, 'tenant') and obj.tenant == request.user.tenant:
                return True
            # If the object is a User, check if that user belongs to the admin's tenant
            if isinstance(obj, request.user.__class__) and obj.tenant == request.user.tenant:
                return True
        # If the object is the user themselves (for /me endpoints)
        if obj == request.user:
            return True
        return False

class IsOwnerOfObject(permissions.BasePermission):
    """
    Allows access only if the request.user is the user associated with the object.
    Used for things like "me" endpoints or a user managing their own refresh tokens.
    """
    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        # If the object is the user themselves
        if obj == request.user:
            return True
        # If the object has a 'user' attribute (like RefreshToken or ResetPasswordToken)
        if hasattr(obj, 'user') and obj.user == request.user:
            return True
        return False