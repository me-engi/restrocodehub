# backend/users/models.py
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone
from django.utils.translation import gettext_lazy as _ # For internationalization
import uuid # For universally unique tokens or IDs if needed

# --- Tenant Model ---
class Tenant(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False) # Using UUID for tenants
    name = models.CharField(_("tenant name"), max_length=255)
    slug = models.SlugField(_("tenant slug"), max_length=100, unique=True, null=True, blank=True, help_text=_("URL-friendly identifier for the tenant, auto-generated if blank."))
    is_active = models.BooleanField(_("active status"), default=True)

    # Subscription related fields
    subscription_id = models.CharField(_("payment gateway subscription ID"), max_length=255, null=True, blank=True)
    payment_customer_id = models.CharField(_("payment gateway customer ID"), max_length=255, null=True, blank=True)
    subscription_start_date = models.DateTimeField(_("subscription start date"), null=True, blank=True)
    subscription_end_date = models.DateTimeField(_("subscription end date"), null=True, blank=True)
    current_plan_name = models.CharField(_("current plan"), max_length=100, null=True, blank=True)

    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)

    class Meta:
        db_table = 'tenants'
        verbose_name = _("tenant")
        verbose_name_plural = _("tenants")
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug and self.name:
            from django.utils.text import slugify
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while Tenant.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)


# --- Custom User Manager ---
class UserManager(BaseUserManager):
    def create_user(self, email: str, tenant: Tenant, password: str = None, **extra_fields):
        if not email:
            raise ValueError(_('The Email field must be set'))
        if not tenant:
            raise ValueError(_('A User must be associated with a Tenant'))

        email = self.normalize_email(email)
        user = self.model(email=email, tenant=tenant, **extra_fields)
        if password:
            user.set_password(password)
        else:
            # Set unusable password if not provided, e.g., for invited users
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, email: str, password: str = None, **extra_fields):
        # Superusers of the platform might not belong to a regular tenant
        # Or you might create a special "Platform Admin" tenant.
        # For this example, let's make tenant optional for superusers by not requiring it here,
        # but you'd need to make the tenant field on User model nullable or provide a default.
        # A cleaner way: create a dedicated "Platform" tenant for superusers.

        # For now, let's assume a superuser is NOT tied to a specific business tenant.
        # The `tenant` field on the User model would need to be `null=True, blank=True`.
        # However, for SaaS, it's often better that even superusers are users, perhaps in a special tenant.
        # Let's stick to the original idea that all users (even platform admins) might belong to a tenant.
        # So, a superuser would also need a tenant (e.g., a special "System Tenant").

        # Let's assume `tenant` will be passed in `extra_fields` or you handle it.
        # For now, this superuser creation is simplified for platform admins.
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'platform_admin') # A specific role for platform superusers

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))

        # For superusers, we might not require a tenant directly here,
        # or we fetch/create a default "platform" tenant.
        # If User.tenant is not nullable, this needs careful handling.
        # For simplicity here, we'll assume tenant can be null or a default is handled elsewhere.
        # This part needs business logic decision: do platform admins belong to a tenant?
        # Let's assume for now they don't (User.tenant allows null)
        # Or, more robustly, they are created under a specific "Platform Admin Tenant".
        # For this example, we'll just create them and assume `tenant` is nullable for them
        # or passed in `extra_fields` when calling `create_superuser`.
        #
        # A common pattern:
        # platform_tenant, _ = Tenant.objects.get_or_create(name="Platform Administration", slug="platform-admin", defaults={'is_active': True})
        # extra_fields.setdefault('tenant', platform_tenant)

        if 'tenant' not in extra_fields:
             raise ValueError(_('Superuser must be associated with a Tenant (e.g., a Platform Admin Tenant)'))


        return self.create_user(email=email, password=password, **extra_fields)

    def sign_up_tenant_and_admin(self, tenant_name: str, admin_email: str, admin_name: str, admin_password: str):
        """
        Creates a new Tenant and an initial admin User for that tenant.
        This is typically called when a new restaurant/business signs up.
        """
        if not tenant_name or not admin_email or not admin_password:
            raise ValueError(_("Tenant name, admin email, and password are required."))
        if self.model.objects.filter(email=self.normalize_email(admin_email)).exists():
            raise ValueError(_("A user with this email already exists."))

        tenant = Tenant.objects.create(name=tenant_name, is_active=True) # New tenants are active by default
        admin_user = self.create_user(
            email=admin_email,
            tenant=tenant,
            password=admin_password,
            name=admin_name,
            role='tenant_admin', # Role for the initial admin of the tenant
            is_staff=False, # Tenant admins are not Django staff by default
            is_active=True
        )
        return tenant, admin_user


# --- Custom User Model ---
class User(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(_("email address"), unique=True, help_text=_("Used for login and communication."))
    name = models.CharField(_("full name"), max_length=255, blank=True)

    # Role within their Tenant (e.g., 'tenant_admin', 'restaurant_manager', 'pos_operator', 'chef', 'customer')
    # 'platform_admin' for platform superusers.
    role = models.CharField(_("user role"), max_length=50, default='staff')

    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE, # If tenant is deleted, associated users are also deleted.
                                  # Consider models.PROTECT if users should prevent tenant deletion.
        related_name='tenant_users',
        verbose_name=_("associated tenant")
        # null=True, blank=True # Make tenant nullable ONLY if platform admins don't belong to any tenant.
                               # Better to assign them to a "Platform Admin" tenant.
    )

    # Standard Django user fields
    is_active = models.BooleanField(
        _("active"),
        default=True,
        help_text=_(
            "Designates whether this user should be treated as active. "
            "Unselect this instead of deleting accounts."
        ),
    )
    is_staff = models.BooleanField(
        _("staff status"),
        default=False,
        help_text=_("Designates whether the user can log into this admin site (Django Admin). Tenant admins are typically not Django staff."),
    )
    date_joined = models.DateTimeField(_("date joined"), default=timezone.now)
    last_login = models.DateTimeField(_("last login"), null=True, blank=True)

    # Additional fields from your original model
    photo_url = models.URLField(_("photo URL"), max_length=512, null=True, blank=True)
    designation = models.CharField(_("designation"), max_length=255, null=True, blank=True)
    phone_number = models.CharField(_("phone number"), max_length=20, null=True, blank=True)

    objects = UserManager() # Attach the custom manager

    USERNAME_FIELD = 'email' # Use email for login
    REQUIRED_FIELDS = ['name', 'tenant'] # Fields prompted for when creating a user via createsuperuser
                                         # If tenant is auto-assigned for superuser, remove 'tenant' from here.

    class Meta:
        db_table = 'users'
        verbose_name = _("user")
        verbose_name_plural = _("users")
        ordering = ['email']
        unique_together = [['email', 'tenant']] # Optional: if email should only be unique PER tenant
                                                # If email is globally unique, just `unique=True` on email field is enough.
                                                # Global uniqueness for email is more common.

    def __str__(self):
        return self.email

    def get_full_name(self):
        return self.name

    def get_short_name(self):
        return self.name.split(' ')[0] if self.name else ''

    # `set_password` and `check_password` are provided by AbstractBaseUser.
    # `groups` and `user_permissions` are provided by PermissionsMixin.


# --- Refresh Token Manager ---
class RefreshTokenManager(models.Manager):
    def create_token(self, user: User, token_string: str, expires_at: timezone.datetime,
                     user_agent: str = None, device_ip: str = None) -> 'RefreshToken':
        if not user or not token_string or not expires_at:
            raise ValueError(_("User, token string, and expiry are required to create a refresh token."))
        return self.create(
            user=user,
            token=token_string,
            expires_at=expires_at,
            user_agent=user_agent,
            device_ip=device_ip
        )

    def verify_and_get_user(self, token_string: str) -> User | None:
        try:
            refresh_token_instance = self.get(token=token_string, expires_at__gt=timezone.now())
            # Optionally, you might want to mark the token as used or implement one-time use logic here.
            return refresh_token_instance.user
        except RefreshToken.DoesNotExist:
            return None

    def cleanup_expired_tokens(self, user: User = None):
        """Deletes all expired refresh tokens, optionally for a specific user."""
        queryset = self.filter(expires_at__lt=timezone.now())
        if user:
            queryset = queryset.filter(user=user)
        count, _ = queryset.delete()
        return count

    def get_active_sessions(self, user: User):
        """Lists active (non-expired) refresh tokens for a user, representing active sessions."""
        return self.filter(user=user, expires_at__gt=timezone.now()).values(
            'id', 'user_agent', 'device_ip', 'created_at', 'expires_at'
        )


# --- Refresh Token Model ---
class RefreshToken(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='refresh_tokens_set', verbose_name=_("user"))
    token = models.CharField(_("token string"), max_length=512, unique=True, db_index=True) # Ensure token is unique and indexed
    user_agent = models.TextField(_("user agent"), null=True, blank=True)
    device_ip = models.GenericIPAddressField(_("device IP address"), null=True, blank=True)
    expires_at = models.DateTimeField(_("expires at"))
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    last_used_at = models.DateTimeField(_("last used at"), null=True, blank=True) # Optional: for tracking activity

    objects = RefreshTokenManager()

    class Meta:
        db_table = 'refresh_tokens'
        verbose_name = _("refresh token")
        verbose_name_plural = _("refresh tokens")
        ordering = ['-created_at']

    def __str__(self):
        return f"Refresh token for {self.user.email} (Expires: {self.expires_at.strftime('%Y-%m-%d %H:%M')})"

    def is_expired(self) -> bool:
        return self.expires_at < timezone.now()


# --- Reset Password Token Manager ---
class ResetPasswordTokenManager(models.Manager):
    def create_token(self, user: User, token_duration_hours: int = 24) -> 'ResetPasswordToken':
        # Invalidate any existing, unused tokens for this user
        self.filter(user=user, is_used=False, expires_at__gt=timezone.now()).update(expires_at=timezone.now()) # Expire them

        token_string = uuid.uuid4().hex # Generate a secure, random token
        expires_at = timezone.now() + timezone.timedelta(hours=token_duration_hours)
        return self.create(user=user, token=token_string, expires_at=expires_at)

    def verify_token_and_get_user(self, token_string: str) -> User | None:
        try:
            reset_token_instance = self.get(token=token_string, is_used=False, expires_at__gt=timezone.now())
            return reset_token_instance.user
        except ResetPasswordToken.DoesNotExist:
            return None

    def mark_token_as_used(self, token_string: str):
        self.filter(token=token_string).update(is_used=True)


# --- Reset Password Token Model ---
class ResetPasswordToken(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reset_password_tokens_set', verbose_name=_("user"))
    token = models.CharField(_("token string"), max_length=100, unique=True, db_index=True)
    expires_at = models.DateTimeField(_("expires at"))
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    is_used = models.BooleanField(_("is used"), default=False)

    objects = ResetPasswordTokenManager()

    class Meta:
        db_table = 'reset_password_tokens'
        verbose_name = _("reset password token")
        verbose_name_plural = _("reset password tokens")
        ordering = ['-created_at']

    def __str__(self):
        return f"Reset token for {self.user.email}"

    def is_expired(self) -> bool:
        return self.expires_at < timezone.now()


# --- Subscription History Model ---
class SubscriptionHistory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.PROTECT, related_name='subscription_history_entries', verbose_name=_("tenant")) # Protect: Don't delete tenant if history exists
    plan_name = models.CharField(_("plan name"), max_length=100)
    price_paid = models.DecimalField(_("price paid"), max_digits=10, decimal_places=2, null=True, blank=True)
    payment_gateway_transaction_id = models.CharField(_("payment gateway transaction ID"), max_length=255, null=True, blank=True)
    
    STATUS_CHOICES = [
        ('active', _('Active')),
        ('expired', _('Expired')),
        ('cancelled', _('Cancelled')),
        ('payment_failed', _('Payment Failed')),
        ('pending_activation', _('Pending Activation')),
        ('trial', _('Trial Period')),
    ]
    status = models.CharField(_("status"), max_length=50, choices=STATUS_CHOICES, default='pending_activation')

    event_date = models.DateTimeField(_("event date"), default=timezone.now, help_text=_("Date this subscription event occurred (e.g., payment, cancellation)."))
    starts_on = models.DateTimeField(_("period starts on"))
    expires_on = models.DateTimeField(_("period expires on"))

    notes = models.TextField(_("notes"), blank=True, null=True, help_text=_("Internal notes regarding this subscription entry."))

    class Meta:
        db_table = 'subscription_history'
        verbose_name = _("subscription history entry")
        verbose_name_plural = _("subscription history entries")
        ordering = ['-event_date']

    def __str__(self):
        return f"Subscription for {self.tenant.name} ({self.plan_name}) - Status: {self.get_status_display()}"