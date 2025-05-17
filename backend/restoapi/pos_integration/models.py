# backend/pos_integration/models.py
from django.db import models
from django.utils.translation import gettext_lazy as _
import uuid
from django.conf import settings

# from restaurants.models import Restaurant # Using string reference

# Supported POS Systems (this could also be a separate model if very dynamic)
POS_SYSTEM_CHOICES = [
    ('GENERIC_API', _('Generic API Interface')),
    ('SQUARE', _('Square POS')),
    ('TOAST', _('Toast POS')),
    ('CLOVER', _('Clover POS')),
    ('PETPOOJA', _('Petpooja POS')), # Example Indian POS
    ('URBANPIPER', _('UrbanPiper Aggregator')), # Example Aggregator
    ('MANUAL', _('Manual / No Integration')), # For restaurants without direct integration
    ('CUSTOM', _('Custom Integration')),
]

class RestaurantPOSConfiguration(models.Model):
    """
    Stores POS integration specific settings for each restaurant.
    One restaurant will have one active POS configuration.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    restaurant = models.OneToOneField(
        'restaurants.Restaurant', # String reference
        on_delete=models.CASCADE,
        related_name='pos_configuration',
        verbose_name=_("restaurant")
    )
    pos_system_type = models.CharField(
        _("POS system type"),
        max_length=50,
        choices=POS_SYSTEM_CHOICES,
        default='MANUAL'
    )
    is_active = models.BooleanField(
        _("is integration active"), default=False,
        help_text=_("Enable/disable data synchronization with this POS.")
    )
    api_key = models.CharField(_("API key"), max_length=512, blank=True, null=True, help_text=_("Encrypted API key for the POS system."))
    api_secret = models.CharField(_("API secret/token"), max_length=512, blank=True, null=True, help_text=_("Encrypted API secret or token, if applicable."))
    api_endpoint_url = models.URLField(_("API endpoint URL"), max_length=512, blank=True, null=True, help_text=_("Base URL for the POS API."))
    # Store specific identifiers used by the POS system for this restaurant
    pos_location_id = models.CharField(_("POS location/store ID"), max_length=100, blank=True, null=True)
    # Additional JSON field for system-specific settings
    additional_settings = models.JSONField(
        _("additional settings"), default=dict, blank=True,
        help_text=_("POS system specific configurations, e.g., webhook secret, menu sync preferences.")
    )
    # Sync Status
    last_menu_sync_at = models.DateTimeField(_("last menu sync at"), null=True, blank=True)
    last_inventory_sync_at = models.DateTimeField(_("last inventory sync at"), null=True, blank=True)
    last_order_push_successful_at = models.DateTimeField(_("last successful order push at"), null=True, blank=True)
    last_sync_error = models.TextField(_("last sync error message"), blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("restaurant POS configuration")
        verbose_name_plural = _("restaurant POS configurations")
        ordering = ['restaurant__name']

    def __str__(self):
        return f"POS Config for {self.restaurant.name} ({self.get_pos_system_type_display()})"

    def save(self, *args, **kwargs):
        # Placeholder for encrypting api_key and api_secret before saving
        # if self.api_key: self.api_key = encrypt(self.api_key)
        # if self.api_secret: self.api_secret = encrypt(self.api_secret)
        super().save(*args, **kwargs)

    # Placeholder for decrypting for use (never expose decrypted in serializers/API responses)
    # def get_decrypted_api_key(self):
    #     return decrypt(self.api_key) if self.api_key else None


class POSIntegrationLog(models.Model):
    """
    Logs significant events related to POS integration actions.
    e.g., attempts to sync menu, push order, receive status update.
    """
    LOG_TYPE_CHOICES = [
        ('ORDER_PUSH', _('Order Push to POS')),
        ('ORDER_STATUS_PULL', _('Order Status Pull from POS')),
        ('ORDER_STATUS_WEBHOOK', _('Order Status Webhook from POS')),
        ('MENU_SYNC_TO_PLATFORM', _('Menu Sync from POS to Platform')),
        ('INVENTORY_SYNC_TO_PLATFORM', _('Inventory Sync from POS to Platform')),
        ('ERROR', _('Integration Error')),
        ('INFO', _('Informational')),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    pos_configuration = models.ForeignKey(
        RestaurantPOSConfiguration,
        on_delete=models.SET_NULL, # Keep log even if config is deleted (or PROTECT)
        null=True, blank=True, # Might be a general log not tied to a specific config
        related_name='integration_logs'
    )
    restaurant = models.ForeignKey( # Denormalized for easier querying
        'restaurants.Restaurant',
        on_delete=models.SET_NULL, null=True, blank=True,
        related_name='pos_integration_logs'
    )
    log_type = models.CharField(_("log type"), max_length=30, choices=LOG_TYPE_CHOICES, db_index=True)
    # Related objects (optional, based on log_type)
    related_order = models.ForeignKey(
        'orders.Order', # String reference
        on_delete=models.SET_NULL, null=True, blank=True,
        related_name='pos_integration_logs'
    )
    # related_menu_item = models.ForeignKey('menu.MenuItem', ...)

    timestamp = models.DateTimeField(_("timestamp"), default=timezone.now, db_index=True)
    is_success = models.BooleanField(_("was successful?"), null=True, blank=True) # Null if just info
    message = models.TextField(_("message / details"))
    request_payload = models.JSONField(_("request payload to POS"), null=True, blank=True)
    response_payload = models.JSONField(_("response payload from POS"), null=True, blank=True)
    error_details = models.TextField(_("error details"), blank=True, null=True)

    class Meta:
        verbose_name = _("POS integration log")
        verbose_name_plural = _("POS integration logs")
        ordering = ['-timestamp']

    def __str__(self):
        status = "Success" if self.is_success else ("Failed" if self.is_success == False else "Info")
        return f"{self.get_log_type_display()} for {self.restaurant.name if self.restaurant else 'N/A'} - {status} at {self.timestamp.strftime('%Y-%m-%d %H:%M')}"

    def save(self, *args, **kwargs):
        if self.pos_configuration and not self.restaurant_id:
            self.restaurant_id = self.pos_configuration.restaurant_id
        super().save(*args, **kwargs)