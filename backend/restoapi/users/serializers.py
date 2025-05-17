# backend/users/serializers.py
from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.utils import timezone
from .models import Tenant, User, RefreshToken, SubscriptionHistory # Assuming ResetPasswordToken is handled by specific views

# --- Tenant Serializers ---
class TenantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tenant
        fields = [
            'id', 'name', 'slug', 'is_active',
            'subscription_id', 'payment_customer_id',
            'subscription_start_date', 'subscription_end_date', 'current_plan_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'slug', 'created_at', 'updated_at', 'subscription_id', 'payment_customer_id', 'subscription_start_date', 'subscription_end_date'] # Some fields managed by payment system


class TenantCreateSerializer(serializers.Serializer): # For the initial tenant/admin signup
    tenant_name = serializers.CharField(max_length=255)
    admin_email = serializers.EmailField()
    admin_name = serializers.CharField(max_length=255)
    admin_password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    admin_password2 = serializers.CharField(write_only=True, required=True, label="Confirm Password")

    def validate(self, attrs):
        if attrs['admin_password'] != attrs['admin_password2']:
            raise serializers.ValidationError({"admin_password2": "Passwords do not match."})
        if User.objects.filter(email=attrs['admin_email']).exists():
            raise serializers.ValidationError({"admin_email": "A user with this email already exists."})
        return attrs

    def create(self, validated_data):
        # Logic will be in the view, using UserManager.sign_up_tenant_and_admin
        # This serializer is mainly for validation and data shaping.
        # The view's perform_create will call the manager method.
        # For DRF to work smoothly, the view usually calls serializer.save()
        # So, we can implement the manager call here.
        tenant, user = User.objects.sign_up_tenant_and_admin(
            tenant_name=validated_data['tenant_name'],
            admin_email=validated_data['admin_email'],
            admin_name=validated_data['admin_name'],
            admin_password=validated_data['admin_password']
        )
        # We need to return something the view can use, perhaps the user or tenant
        # Or, the view handles the manager call and this serializer is just for input.
        # For simplicity, let's assume the view handles it if complex return is needed.
        # If we must return a model instance that matches a ListCreateAPIView expectation:
        return user # Or tenant, depending on what the view expects to return


# --- User Serializers ---
class UserSerializer(serializers.ModelSerializer):
    tenant_name = serializers.CharField(source='tenant.name', read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'email', 'name', 'role', 'tenant', 'tenant_name',
            'is_active', 'is_staff', 'date_joined', 'last_login',
            'photo_url', 'designation', 'phone_number'
        ]
        read_only_fields = ['id', 'tenant', 'tenant_name', 'is_staff', 'date_joined', 'last_login']
        extra_kwargs = {
            'password': {'write_only': True, 'required': False}, # For updates, password is not always required
        }

class UserDetailSerializer(UserSerializer): # For /me endpoint and admin viewing specific user
    # Could add more detailed fields here if needed
    pass

class UserCreateSerializer(serializers.ModelSerializer): # For tenant admin creating users
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True, label="Confirm Password")
    tenant = serializers.PrimaryKeyRelatedField(read_only=True) # Tenant will be set from authenticated admin's tenant

    class Meta:
        model = User
        fields = ['id', 'email', 'name', 'role', 'password', 'password2', 'tenant',
                  'photo_url', 'designation', 'phone_number', 'is_active']
        read_only_fields = ['id', 'tenant']

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password2": "Passwords do not match."})
        # Email uniqueness check might be per tenant or global, depending on User.Meta.unique_together
        # If global, the model's unique=True on email field handles it.
        # If per tenant, you'd add custom validation here:
        # request_user = self.context['request'].user
        # if User.objects.filter(email=attrs['email'], tenant=request_user.tenant).exists():
        #     raise serializers.ValidationError({"email": "This email is already in use within your organization."})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        request_user = self.context['request'].user
        user = User.objects.create_user(
            tenant=request_user.tenant, # Assign to the admin's tenant
            email=validated_data['email'],
            password=validated_data['password'],
            name=validated_data.get('name', ''),
            role=validated_data.get('role', 'staff'), # Default role if not provided
            photo_url=validated_data.get('photo_url'),
            designation=validated_data.get('designation'),
            phone_number=validated_data.get('phone_number'),
            is_active=validated_data.get('is_active', True)
        )
        return user

class UserUpdateSerializer(serializers.ModelSerializer): # For /me or tenant admin updating user
    class Meta:
        model = User
        fields = ['name', 'role', 'photo_url', 'designation', 'phone_number', 'is_active']
        # Email should generally not be updatable easily, or require re-verification.
        # Role can only be updated by tenant admin for other users, not for 'me'.

# --- Auth Serializers (for request bodies) ---
class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

class RefreshTokenSerializer(serializers.Serializer):
    refresh_token = serializers.CharField()

class PasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password1 = serializers.CharField(required=True, validators=[validate_password])
    new_password2 = serializers.CharField(required=True)

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Your old password was entered incorrectly. Please enter it again.")
        return value

    def validate(self, data):
        if data['new_password1'] != data['new_password2']:
            raise serializers.ValidationError({'new_password2': "The two password fields didn't match."})
        return data

class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

class PasswordResetConfirmSerializer(serializers.Serializer):
    token = serializers.CharField()
    new_password1 = serializers.CharField(required=True, validators=[validate_password])
    new_password2 = serializers.CharField(required=True)

    def validate(self, data):
        if data['new_password1'] != data['new_password2']:
            raise serializers.ValidationError({'new_password2': "The two password fields didn't match."})
        # Token validation will happen in the view
        return data

# --- RefreshToken/Session Serializers (for responses) ---
class ActiveSessionSerializer(serializers.ModelSerializer):
    # This is for listing active sessions based on RefreshToken model
    class Meta:
        model = RefreshToken
        fields = ['id', 'user_agent', 'device_ip', 'created_at', 'expires_at', 'last_used_at']


# --- Subscription History Serializer ---
class SubscriptionHistorySerializer(serializers.ModelSerializer):
    tenant_name = serializers.CharField(source='tenant.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = SubscriptionHistory
        fields = [
            'id', 'tenant', 'tenant_name', 'plan_name', 'price_paid',
            'payment_gateway_transaction_id', 'status', 'status_display',
            'event_date', 'starts_on', 'expires_on', 'notes'
        ]