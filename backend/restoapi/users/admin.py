# backend/users/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin # If you were using Django's User
from django.utils.translation import gettext_lazy as _
from .models import Tenant, User, RefreshToken, ResetPasswordToken, SubscriptionHistory

# --- Tenant Admin ---
@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'is_active', 'current_plan_name', 'subscription_end_date', 'created_at')
    list_filter = ('is_active', 'current_plan_name', 'created_at', 'subscription_end_date')
    search_fields = ('name', 'slug', 'payment_customer_id', 'subscription_id')
    readonly_fields = ('id', 'created_at', 'updated_at', 'slug') # Slug is auto-generated but can be made editable if needed
    fieldsets = (
        (_('Tenant Information'), {
            'fields': ('id', 'name', 'slug', 'is_active')
        }),
        (_('Subscription Details'), {
            'fields': ('current_plan_name', 'subscription_id', 'payment_customer_id', 'subscription_start_date', 'subscription_end_date')
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    # If you want to show related users or subscription history inlined:
    # inlines = [UserInline, SubscriptionHistoryInline] # Define these inline classes below


# --- User Admin (for your custom User model) ---
# We need a custom UserAdmin because we are not using Django's default User model directly.
class UserSubscriptionHistoryInline(admin.TabularInline): # Or StackedInline
    model = SubscriptionHistory
    fk_name = 'tenant' # Since SubscriptionHistory links to Tenant, and User links to Tenant
    extra = 0
    readonly_fields = ('id', 'plan_name', 'price_paid', 'payment_gateway_transaction_id', 'status', 'event_date', 'starts_on', 'expires_on', 'notes')
    can_delete = False # Usually, history is not deleted from here
    verbose_name = _("Subscription Event")
    verbose_name_plural = _("Subscription History (for Tenant)")

    def has_add_permission(self, request, obj=None):
        return False # Don't add history from User admin directly

    def get_queryset(self, request):
        # This inline is better suited for TenantAdmin.
        # For UserAdmin, it's harder to link directly unless you filter by user.tenant.
        # For now, this is more of an example if you were to put it in TenantAdmin.
        qs = super().get_queryset(request)
        if hasattr(self.parent_object, 'tenant'): # If shown under a User, get user's tenant
            return qs.filter(tenant=self.parent_object.tenant)
        return qs.none() # Or handle appropriately if parent_object is not a User with a tenant

class UserTenantInline(admin.TabularInline): # To show users under a Tenant
    model = User
    fk_name = 'tenant'
    fields = ('email', 'name', 'role', 'is_active', 'date_joined')
    readonly_fields = ('email', 'name', 'role', 'date_joined')
    extra = 0
    can_delete = True # Allow deactivating/removing users from a tenant (soft delete is better)
    show_change_link = True # Allow clicking to the User's change form

    def has_add_permission(self, request, obj=None):
        return True # Allow adding users to a tenant from Tenant admin


@admin.register(User)
class UserAdmin(admin.ModelAdmin): # Not inheriting from BaseUserAdmin for full custom model control
    list_display = ('email', 'name', 'tenant_name_display', 'role', 'is_active', 'is_staff', 'is_superuser', 'date_joined', 'last_login')
    list_filter = ('is_active', 'is_staff', 'is_superuser', 'role', 'tenant', 'date_joined')
    search_fields = ('email', 'name', 'tenant__name')
    ordering = ('-date_joined', 'email')
    readonly_fields = ('id', 'date_joined', 'last_login')

    fieldsets = (
        (None, {'fields': ('id', 'email', 'password')}), # Password field will show "******** Change" link
        (_('Personal info'), {'fields': ('name', 'photo_url', 'designation', 'phone_number')}),
        (_('Tenant & Role'), {'fields': ('tenant', 'role')}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )

    # If you want to use the form from Django's UserAdmin for password handling, etc.
    # you would inherit from BaseUserAdmin and customize add_fieldsets/fieldsets.
    # For a fully custom model without AbstractUser, this is simpler.
    # You'll need to handle password changes carefully or provide a custom form.
    # For simplicity, Django admin handles password hashing if you set the password field.

    def tenant_name_display(self, obj):
        return obj.tenant.name if obj.tenant else '-'
    tenant_name_display.short_description = _('Tenant')
    tenant_name_display.admin_order_field = 'tenant__name' # Allows sorting by tenant name

    # To make password field non-editable directly but show "change password" form:
    # (Django does this by default for the password field from AbstractBaseUser)
    # If you need a custom form for user creation/change to handle password and tenant assignment better:
    # from django.contrib.auth.forms import UserCreationForm, UserChangeForm (customized for your model)
    # form = YourCustomUserChangeForm
    # add_form = YourCustomUserCreationForm

# --- Refresh Token Admin ---
@admin.register(RefreshToken)
class RefreshTokenAdmin(admin.ModelAdmin):
    list_display = ('user_email_display', 'token_preview', 'device_ip', 'user_agent_preview', 'expires_at', 'created_at', 'is_token_expired')
    list_filter = ('user__tenant', 'expires_at', 'created_at')
    search_fields = ('user__email', 'token', 'device_ip', 'user_agent')
    readonly_fields = ('id', 'user', 'token', 'user_agent', 'device_ip', 'expires_at', 'created_at', 'last_used_at')
    date_hierarchy = 'created_at'

    def user_email_display(self, obj):
        return obj.user.email
    user_email_display.short_description = _('User Email')
    user_email_display.admin_order_field = 'user__email'

    def token_preview(self, obj):
        return f"{obj.token[:20]}..." if obj.token else '-'
    token_preview.short_description = _('Token (Preview)')

    def user_agent_preview(self, obj):
        return f"{obj.user_agent[:50]}..." if obj.user_agent else '-'
    user_agent_preview.short_description = _('User Agent (Preview)')

    @admin.display(boolean=True, description=_('Is Expired?'))
    def is_token_expired(self, obj):
        return obj.is_expired()

    def has_add_permission(self, request):
        return False # Refresh tokens are created programmatically

    def has_change_permission(self, request, obj=None):
        return False # Refresh tokens are generally not changed, only deleted


# --- Reset Password Token Admin ---
@admin.register(ResetPasswordToken)
class ResetPasswordTokenAdmin(admin.ModelAdmin):
    list_display = ('user_email_display', 'token_preview', 'expires_at', 'created_at', 'is_used', 'is_token_expired')
    list_filter = ('user__tenant', 'is_used', 'expires_at', 'created_at')
    search_fields = ('user__email', 'token')
    readonly_fields = ('id', 'user', 'token', 'expires_at', 'created_at', 'is_used')
    date_hierarchy = 'created_at'

    def user_email_display(self, obj):
        return obj.user.email
    user_email_display.short_description = _('User Email')
    user_email_display.admin_order_field = 'user__email'

    def token_preview(self, obj):
        return f"{obj.token[:20]}..." if obj.token else '-'
    token_preview.short_description = _('Token (Preview)')

    @admin.display(boolean=True, description=_('Is Expired?'))
    def is_token_expired(self, obj):
        return obj.is_expired()

    def has_add_permission(self, request):
        return False # Reset tokens are created programmatically

    def has_change_permission(self, request, obj=None):
        # Potentially allow marking as used, but usually done by the system
        return False # Or limit to specific fields if any are editable by admin


# --- Subscription History Admin ---
@admin.register(SubscriptionHistory)
class SubscriptionHistoryAdmin(admin.ModelAdmin):
    list_display = ('tenant_name_display', 'plan_name', 'status_display', 'event_date', 'starts_on', 'expires_on', 'price_paid')
    list_filter = ('status', 'plan_name', 'tenant', 'event_date', 'expires_on')
    search_fields = ('tenant__name', 'plan_name', 'payment_gateway_transaction_id', 'notes')
    readonly_fields = ('id', 'tenant', 'plan_name', 'price_paid', 'payment_gateway_transaction_id', 'status', 'event_date', 'starts_on', 'expires_on') # Most fields are record of an event
    date_hierarchy = 'event_date'
    fieldsets = (
        (None, {
            'fields': ('id', 'tenant', 'plan_name', 'status')
        }),
        (_('Financials & Dates'), {
            'fields': ('price_paid', 'payment_gateway_transaction_id', 'event_date', 'starts_on', 'expires_on')
        }),
        (_('Additional Information'), {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
    )

    def tenant_name_display(self, obj):
        return obj.tenant.name
    tenant_name_display.short_description = _('Tenant')
    tenant_name_display.admin_order_field = 'tenant__name'

    def status_display(self, obj):
        return obj.get_status_display()
    status_display.short_description = _('Status')
    status_display.admin_order_field = 'status'

    def has_add_permission(self, request):
        # Subscription history is typically created programmatically via payment webhooks or actions
        return False

    def has_change_permission(self, request, obj=None):
        # History entries are records of past events, so they shouldn't usually be changed.
        # Maybe allow changing 'notes' or 'status' in specific admin scenarios.
        # For now, let's make them mostly read-only in admin.
        if request.user.is_superuser: # Only superusers can potentially change for corrections
            return True # Or return specific fields like self.fields = ('notes',)
        return False


# If you want inlines on TenantAdmin for Users and SubscriptionHistory:
class UserInlineForTenantAdmin(admin.TabularInline):
    model = User
    fk_name = 'tenant'
    fields = ('email', 'name', 'role', 'is_active')
    readonly_fields = ('email', 'name') # Role and is_active might be editable here
    extra = 0
    show_change_link = True
    verbose_name_plural = _("Tenant Users")

class SubscriptionHistoryInlineForTenantAdmin(admin.TabularInline):
    model = SubscriptionHistory
    fk_name = 'tenant'
    fields = ('plan_name', 'get_status_display', 'event_date', 'starts_on', 'expires_on', 'price_paid')
    readonly_fields = fields # History is read-only here
    extra = 0
    can_delete = False
    show_change_link = False
    verbose_name_plural = _("Subscription History")

    def has_add_permission(self, request, obj=None):
        return False

# Then, modify TenantAdmin:
# @admin.register(Tenant)
# class TenantAdmin(admin.ModelAdmin):
#     ... (other attributes)
#     inlines = [UserInlineForTenantAdmin, SubscriptionHistoryInlineForTenantAdmin]