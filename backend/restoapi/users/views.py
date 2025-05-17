# backend/users/views.py
from django.utils import timezone
from django.core.mail import send_mail # For sending emails
from django.conf import settings
from django.shortcuts import get_object_or_404

from rest_framework import generics, status, viewsets, views
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.decorators import action

from .models import Tenant, User, RefreshToken, ResetPasswordToken # SubscriptionHistory (handled separately or via Tenant)
from .serializers import (
    TenantSerializer, TenantCreateSerializer,
    UserSerializer, UserDetailSerializer, UserCreateSerializer, UserUpdateSerializer,
    LoginSerializer, RefreshTokenSerializer,
    PasswordChangeSerializer, PasswordResetRequestSerializer, PasswordResetConfirmSerializer,
    ActiveSessionSerializer, SubscriptionHistorySerializer
)
from .permissions import IsPlatformAdmin, IsTenantAdmin, IsTenantAdminOrOwnerOfObject, IsOwnerOfObject
from .authentication import generate_access_token, generate_refresh_token # Your custom JWT functions

# --- I. Authentication Views ---

class TenantRegistrationView(generics.CreateAPIView):
    serializer_class = TenantCreateSerializer
    permission_classes = [AllowAny]

    def perform_create(self, serializer):
        # The serializer's create method calls User.objects.sign_up_tenant_and_admin
        # We need to ensure that method is robust or handle the creation more directly here.
        # For now, assuming serializer.save() calls the manager method correctly and returns the admin_user.
        try:
            # This view will directly use the manager method for clarity
            tenant, admin_user = User.objects.sign_up_tenant_and_admin(
                tenant_name=serializer.validated_data['tenant_name'],
                admin_email=serializer.validated_data['admin_email'],
                admin_name=serializer.validated_data['admin_name'],
                admin_password=serializer.validated_data['admin_password']
            )
            # Optionally, log in the new admin user immediately
            # access_token = generate_access_token(admin_user)
            # refresh_token_str = generate_refresh_token(admin_user)
            # RefreshToken.objects.create_token(
            #     user=admin_user,
            #     token_string=refresh_token_str,
            #     expires_at=timezone.now() + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS), # Get from settings
            #     user_agent=self.request.META.get('HTTP_USER_AGENT', ''),
            #     device_ip=self.request.META.get('REMOTE_ADDR', '')
            # )
            # return Response({
            #     "message": "Tenant and admin user created successfully.",
            #     "user": UserDetailSerializer(admin_user).data, # Or just user_id
            #     "tenant_id": str(tenant.id),
            #     "access_token": access_token,
            #     "refresh_token": refresh_token_str
            # }, status=status.HTTP_201_CREATED)
            return Response({
                 "message": "Tenant and admin user created successfully. Please log in.",
                 "user_id": str(admin_user.id),
                 "tenant_id": str(tenant.id)
            }, status=status.HTTP_201_CREATED)

        except ValueError as e: # Catch validation errors from the manager
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e: # Catch other unexpected errors
            # Log the exception e
            return Response({"error": "An unexpected error occurred during signup."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class LoginView(generics.GenericAPIView):
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        password = serializer.validated_data['password']

        try:
            user = User.objects.get(email__iexact=email) # Case-insensitive email
            if not user.is_active:
                return Response({"error": "User account is inactive."}, status=status.HTTP_401_UNAUTHORIZED)
            if not user.check_password(password):
                return Response({"error": "Invalid credentials."}, status=status.HTTP_401_UNAUTHORIZED)
        except User.DoesNotExist:
            return Response({"error": "Invalid credentials."}, status=status.HTTP_401_UNAUTHORIZED)

        # Generate tokens
        access_token = generate_access_token(user)
        refresh_token_str = generate_refresh_token(user)

        # Store refresh token
        RefreshToken.objects.create_token(
            user=user,
            token_string=refresh_token_str,
            expires_at=timezone.now() + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            device_ip=request.META.get('REMOTE_ADDR', '')
        )
        user.last_login = timezone.now()
        user.save(update_fields=['last_login'])

        return Response({
            "access_token": access_token,
            "refresh_token": refresh_token_str,
            "user": UserDetailSerializer(user, context={'request': request}).data # Include user details
        }, status=status.HTTP_200_OK)


class RefreshTokenView(generics.GenericAPIView):
    serializer_class = RefreshTokenSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        refresh_token_str = serializer.validated_data['refresh_token']

        user = RefreshToken.objects.verify_and_get_user(token_string=refresh_token_str)
        if not user:
            return Response({"error": "Invalid or expired refresh token."}, status=status.HTTP_401_UNAUTHORIZED)
        if not user.is_active:
            return Response({"error": "User account is inactive."}, status=status.HTTP_401_UNAUTHORIZED)

        access_token = generate_access_token(user)
        return Response({"access_token": access_token}, status=status.HTTP_200_OK)


class LogoutView(views.APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        # For true stateless JWTs, logout is client-side (deleting token).
        # If using server-side refresh token store for revocation:
        refresh_token_str = request.data.get('refresh_token')
        if refresh_token_str:
            try:
                token_instance = RefreshToken.objects.get(token=refresh_token_str, user=request.user)
                token_instance.delete()
            except RefreshToken.DoesNotExist:
                # Token already invalid or doesn't belong to user, proceed silently
                pass
        # Optionally, add the current access token to a blacklist if you have such a system.
        return Response({"message": "Successfully logged out."}, status=status.HTTP_200_OK)


class PasswordResetRequestView(generics.GenericAPIView):
    serializer_class = PasswordResetRequestSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        try:
            user = User.objects.get(email__iexact=email, is_active=True)
            reset_token_instance = ResetPasswordToken.objects.create_token(user=user)
            
            # --- Send Email ---
            # reset_url = f"{settings.FRONTEND_URL}/reset-password/{reset_token_instance.token}"
            # subject = "Reset Your Culinary AI Concierge Password"
            # message = f"Hi {user.name or user.email},\n\nPlease click the link to reset your password: {reset_url}\n\nIf you did not request this, please ignore this email."
            # try:
            #     send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])
            # except Exception as e:
            #     # Log email sending failure: logger.error(f"Failed to send password reset email to {user.email}: {e}")
            #     # Don't expose this failure to the user for security reasons.
            #     pass
            print(f"Password reset token for {user.email}: {reset_token_instance.token}") # For dev
        except User.DoesNotExist:
            # Don't reveal if user exists or not for security.
            pass
        return Response({"message": "If an account with that email exists, a password reset link has been sent."}, status=status.HTTP_200_OK)


class PasswordResetConfirmView(generics.GenericAPIView):
    serializer_class = PasswordResetConfirmSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        token_str = serializer.validated_data['token']
        new_password = serializer.validated_data['new_password1']

        user = ResetPasswordToken.objects.verify_token_and_get_user(token_string=token_str)
        if not user:
            return Response({"error": "Invalid or expired password reset token."}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()
        ResetPasswordToken.objects.mark_token_as_used(token_string=token_str)
        # Optionally, log out all other sessions for this user
        # RefreshToken.objects.filter(user=user).delete()

        return Response({"message": "Password has been reset successfully."}, status=status.HTTP_200_OK)


class PasswordChangeView(generics.GenericAPIView):
    serializer_class = PasswordChangeSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = request.user
        user.set_password(serializer.validated_data['new_password1'])
        user.save()
        return Response({"message": "Password changed successfully."}, status=status.HTTP_200_OK)


# --- II. Current User ("Me") Views ---

class CurrentUserView(generics.RetrieveUpdateAPIView):
    serializer_class = UserDetailSerializer # Use more detailed serializer for 'me'
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return UserUpdateSerializer # Use a specific serializer for updates
        return super().get_serializer_class()

    def perform_update(self, serializer):
        # Ensure user cannot change their tenant or make themselves admin via this endpoint
        # The UserUpdateSerializer should only allow safe fields.
        serializer.save()


class CurrentUserSessionsView(generics.ListAPIView):
    serializer_class = ActiveSessionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return RefreshToken.objects.get_active_sessions(user=self.request.user)


class RevokeSessionView(views.APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, refresh_token_id, *args, **kwargs):
        try:
            token_instance = RefreshToken.objects.get(id=refresh_token_id, user=request.user)
            token_instance.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except RefreshToken.DoesNotExist:
            return Response({"error": "Session not found or does not belong to you."}, status=status.HTTP_404_NOT_FOUND)


class RevokeAllOtherSessionsView(views.APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        # Get the current session's refresh token if possible (e.g., from a cookie or custom header if not the one being invalidated)
        # This is tricky without knowing how the current refresh token is identified.
        # Assuming we just delete all *other* refresh tokens for the user.
        # A robust way needs the current refresh token to be excluded.
        # For simplicity, let's assume the client deletes its current token after this.
        # Or, if refresh token is passed in body for this specific action:
        current_refresh_token_str = request.data.get('current_refresh_token_to_keep')
        queryset = RefreshToken.objects.filter(user=request.user)
        if current_refresh_token_str:
            queryset = queryset.exclude(token=current_refresh_token_str)
        queryset.delete()
        return Response({"message": "All other sessions revoked."}, status=status.HTTP_200_OK)


# --- III. Tenant Management Views (for Tenant Admins) ---

class MyTenantDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = TenantSerializer
    permission_classes = [IsAuthenticated, IsTenantAdmin]

    def get_object(self):
        # Tenant admin can only see/update their own tenant
        return self.request.user.tenant

    def perform_update(self, serializer):
        # Tenant admin should only update certain fields like 'name', not subscription details directly here
        # Subscription details are typically managed via payment gateway webhooks or specific actions.
        # For now, let's allow name update. The serializer should control editable fields.
        serializer.save()


class TenantUserViewSet(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsTenantAdmin] # Tenant admin manages users in their tenant

    def get_queryset(self):
        # Tenant admin can only see users within their own tenant
        return User.objects.filter(tenant=self.request.user.tenant).exclude(id=self.request.user.id) # Exclude self

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return UserUpdateSerializer # Ensure this serializer restricts role changes if needed
        return UserSerializer

    def perform_create(self, serializer):
        # Serializer's create method handles setting the tenant and password
        serializer.save(tenant=self.request.user.tenant) # Ensure tenant is set correctly

    def perform_update(self, serializer):
        # Ensure admin cannot make a user a superuser or change tenant
        # The serializer should restrict fields.
        # Also, ensure they cannot update their own role to something lesser if that's a business rule.
        instance = serializer.instance
        if instance.tenant != self.request.user.tenant: # Should not happen due to get_queryset
            raise PermissionDenied("Cannot update users outside your tenant.")
        serializer.save()

    def perform_destroy(self, instance):
        if instance.tenant != self.request.user.tenant:
             raise PermissionDenied("Cannot delete users outside your tenant.")
        if instance == self.request.user:
            raise PermissionDenied("You cannot delete your own account via this endpoint.")
        # Soft delete (is_active=False) is often preferred over hard delete
        instance.is_active = False
        instance.save()
        # instance.delete() # For hard delete


class MyTenantSubscriptionView(generics.ListAPIView): # Or RetrieveAPIView if only current status
    serializer_class = SubscriptionHistorySerializer
    permission_classes = [IsAuthenticated, IsTenantAdmin]

    def get_queryset(self):
        return SubscriptionHistory.objects.filter(tenant=self.request.user.tenant).order_by('-event_date')

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        tenant = request.user.tenant
        current_subscription_data = {
            "current_plan_name": tenant.current_plan_name,
            "subscription_id": tenant.subscription_id,
            "subscription_start_date": tenant.subscription_start_date,
            "subscription_end_date": tenant.subscription_end_date,
            "is_active_subscription": tenant.is_active and tenant.subscription_end_date and tenant.subscription_end_date > timezone.now()
        }
        history_serializer = self.get_serializer(queryset, many=True)
        return Response({
            "current_subscription": current_subscription_data,
            "history": history_serializer.data
        })

class ManageSubscriptionView(views.APIView):
    permission_classes = [IsAuthenticated, IsTenantAdmin]

    def post(self, request, *args, **kwargs):
        # This view would typically interact with your payment provider (e.g., Stripe)
        # to create a customer portal session or handle specific actions.
        # Example: Creating a Stripe Billing Portal session
        # tenant = request.user.tenant
        # if not tenant.payment_customer_id:
        #     return Response({"error": "No payment customer ID found for this tenant."}, status=status.HTTP_400_BAD_REQUEST)
        # try:
        #     portal_session = stripe.billing_portal.Session.create(
        #         customer=tenant.payment_customer_id,
        #         return_url=settings.FRONTEND_SUBSCRIPTION_MANAGE_RETURN_URL,
        #     )
        #     return Response({"portal_url": portal_session.url}, status=status.HTTP_200_OK)
        # except Exception as e:
        #     # Log error e
        #     return Response({"error": "Could not create subscription management session."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response({"message": "Subscription management endpoint placeholder. Integrate with payment provider."}, status=status.HTTP_501_NOT_IMPLEMENTED)


# --- IV. Platform Admin Views (Example - usually done via Django Admin or separate API with IsPlatformAdmin) ---
# These are typically ModelViewSets if you build a dedicated API for platform admins.

class PlatformTenantViewSet(viewsets.ModelViewSet):
    queryset = Tenant.objects.all()
    serializer_class = TenantSerializer
    permission_classes = [IsAuthenticated, IsPlatformAdmin]
    # Add search, filtering, etc.

class PlatformUserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().select_related('tenant')
    serializer_class = UserDetailSerializer # Or a more admin-focused serializer
    permission_classes = [IsAuthenticated, IsPlatformAdmin]
    # Add search, filtering by tenant, role etc.

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            # Need a specific PlatformAdminUserUpdateSerializer to handle tenant assignment, superuser status etc.
            return UserDetailSerializer # Placeholder - create a dedicated one
        return super().get_serializer_class()

# ... and so on for SubscriptionHistory if needed via API for platform admins.