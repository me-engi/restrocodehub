# backend/pos_integration/admin.py
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from django.utils.html import format_html
import json

from .models import RestaurantPOSConfiguration, POSIntegrationLog

@admin.register(RestaurantPOSConfiguration)
class RestaurantPOSConfigurationAdmin(admin.ModelAdmin):
    list_display = ('restaurant_name_display', 'pos_system_type_display', 'is_active', 'last_menu_sync_at', 'last_sync_error_short', 'updated_at')
    list_filter = ('pos_system_type', 'is_active', 'restaurant__tenant')
    search_fields = ('restaurant__name', 'pos_location_id', 'api_endpoint_url')
    readonly_fields = ('id', 'created_at', 'updated_at', 'last_menu_sync_at', 'last_inventory_sync_at', 'last_order_push_successful_at')
    fieldsets = (
        (None, {'fields': ('id', 'restaurant', ('pos_system_type', 'is_active'))}),
        (_('API Credentials & Identifiers (Store Securely!)'), {
            'fields': ('api_key', 'api_secret', 'api_endpoint_url', 'pos_location_id'),
            'description': _("API Keys and Secrets are sensitive. Ensure they are encrypted at rest if stored directly, or manage them via a secrets manager.")
        }),
        (_('Additional Settings'), {'fields': ('additional_settings_pretty',)}),
        (_('Sync Status'), {'fields': ('last_menu_sync_at', 'last_inventory_sync_at', 'last_order_push_successful_at', 'last_sync_error')}),
        (_('Timestamps'), {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )
    list_select_related = ('restaurant', 'restaurant__tenant')
    raw_id_fields = ('restaurant',) # For easier selection if many restaurants

    def restaurant_name_display(self, obj):
        if obj.restaurant:
            link = reverse("admin:restaurants_restaurant_change", args=[obj.restaurant.id]) # Adjust app_label if needed
            return format_html('<a href="{}">{}</a>', link, obj.restaurant.name)
        return "-"
    restaurant_name_display.short_description = _('Restaurant')
    restaurant_name_display.admin_order_field = 'restaurant__name'

    def pos_system_type_display(self, obj):
        return obj.get_pos_system_type_display()
    pos_system_type_display.short_description = _('POS Type')

    def last_sync_error_short(self, obj):
        return (obj.last_sync_error[:75] + '...') if obj.last_sync_error and len(obj.last_sync_error) > 75 else obj.last_sync_error
    last_sync_error_short.short_description = _('Last Sync Error')

    def additional_settings_pretty(self, obj):
        if obj.additional_settings:
            return format_html("<pre>{}</pre>", json.dumps(obj.additional_settings, indent=2, sort_keys=True))
        return "-"
    additional_settings_pretty.short_description = _('Additional Settings (JSON)')


@admin.register(POSIntegrationLog)
class POSIntegrationLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp_short', 'log_type_display', 'restaurant_name_display', 'is_success_display', 'message_preview', 'related_order_link')
    list_filter = ('log_type', 'is_success', 'restaurant', 'timestamp')
    search_fields = ('restaurant__name', 'related_order__order_number', 'message', 'error_details')
    readonly_fields = [f.name for f in POSIntegrationLog._meta.fields] # All fields read-only
    date_hierarchy = 'timestamp'
    list_select_related = ('pos_configuration__restaurant', 'restaurant', 'related_order')
    fieldsets = (
        (None, {'fields': ('id', 'timestamp', 'pos_configuration', 'restaurant', 'log_type', 'is_success')}),
        (_('Related Objects'), {'fields': ('related_order_link_ro',)}), # related_menu_item etc.
        (_('Payloads & Messages'), {'fields': ('message', 'formatted_request_payload', 'formatted_response_payload', 'error_details')}),
    )

    def timestamp_short(self, obj):
        return obj.timestamp.strftime('%Y-%m-%d %H:%M')
    timestamp_short.short_description = _('Timestamp')
    timestamp_short.admin_order_field = 'timestamp'

    def log_type_display(self, obj):
        return obj.get_log_type_display()
    log_type_display.short_description = _('Log Type')

    def restaurant_name_display(self, obj):
        return obj.restaurant.name if obj.restaurant else (obj.pos_configuration.restaurant.name if obj.pos_configuration else '-')
    restaurant_name_display.short_description = _('Restaurant')

    @admin.display(boolean=True, description=_('Success?'))
    def is_success_display(self, obj):
        return obj.is_success
    is_success_display.admin_order_field = 'is_success'

    def message_preview(self, obj):
        return (obj.message[:75] + '...') if obj.message and len(obj.message) > 75 else obj.message
    message_preview.short_description = _('Message')

    def related_order_link(self, obj):
        if obj.related_order:
            link = reverse("admin:orders_order_change", args=[obj.related_order.id]) # Adjust app_label
            return format_html('<a href="{}">{}</a>', link, obj.related_order.order_number)
        return "-"
    related_order_link.short_description = _('Related Order')

    def related_order_link_ro(self, obj): # Read-only version for fieldsets
        return self.related_order_link(obj)
    related_order_link_ro.short_description = _('Related Order')


    def formatted_request_payload(self, obj):
        if obj.request_payload:
            return format_html("<pre>{}</pre>", json.dumps(obj.request_payload, indent=2, sort_keys=True))
        return "-"
    formatted_request_payload.short_description = _('Request Payload (JSON)')

    def formatted_response_payload(self, obj):
        if obj.response_payload:
            return format_html("<pre>{}</pre>", json.dumps(obj.response_payload, indent=2, sort_keys=True))
        return "-"
    formatted_response_payload.short_description = _('Response Payload (JSON)')

    def has_add_permission(self, request): return False
    def has_change_permission(self, request, obj=None): return False # Logs are immutable
    def has_delete_permission(self, request, obj=None): return request.user.is_superuser # Only superusers can delete logs