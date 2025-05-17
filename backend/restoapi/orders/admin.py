# backend/payments/admin.py
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from django.utils.html import format_html
import json

from .models import PaymentTransaction

@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(admin.ModelAdmin):
    list_display = (
        'id_short', 'order_link', 'user_email_display', 'tenant_name_display',
        'amount_currency', 'status_display', 'payment_method_display',
        'gateway_name', 'gateway_transaction_id_short', 'initiated_at_short'
    )
    list_filter = ('status', 'payment_method_used', 'gateway_name', 'tenant', 'initiated_at', 'currency')
    search_fields = (
        'id', 'order__order_number', 'user__email', 'tenant__name',
        'gateway_transaction_id', 'gateway_payment_intent_id'
    )
    readonly_fields = [f.name for f in PaymentTransaction._meta.fields] # Make all fields read-only by default
    date_hierarchy = 'initiated_at'
    list_select_related = ('order', 'user', 'tenant')
    ordering = ('-initiated_at',)

    fieldsets = (
        (_('Transaction Core Info'), {
            'fields': ('id', 'order_link_ro', 'user_link_ro', 'tenant_link_ro', ('amount', 'currency'))
        }),
        (_('Status & Method'), {
            'fields': ('status', 'payment_method_used')
        }),
        (_('Gateway Details'), {
            'fields': ('gateway_name', 'gateway_transaction_id', 'gateway_payment_intent_id', 'formatted_gateway_response_payload')
        }),
        (_('Error Info'), {
            'fields': ('error_message', 'error_code'),
            'classes': ('collapse',)
        }),
        (_('Timestamps'), {
            'fields': ('initiated_at', 'last_updated_at', 'completed_or_failed_at'),
            'classes': ('collapse',)
        }),
    )

    def id_short(self, obj):
        return str(obj.id)[:8] + "..."
    id_short.short_description = _("Txn ID")

    def order_link(self, obj):
        if obj.order:
            link = reverse("admin:orders_order_change", args=[obj.order.id]) # Assumes 'orders' app, 'order' model
            return format_html('<a href="{}">{}</a>', link, obj.order.order_number)
        return "-"
    order_link.short_description = _("Order")
    order_link.admin_order_field = 'order__order_number'

    def order_link_ro(self, obj): # Read-only version for fieldsets
        return self.order_link(obj)
    order_link_ro.short_description = _("Order")


    def user_email_display(self, obj):
        return obj.user.email if obj.user else '-'
    user_email_display.short_description = _("User")
    user_email_display.admin_order_field = 'user__email'

    def user_link_ro(self, obj):
        if obj.user:
            link = reverse("admin:users_user_change", args=[obj.user.id]) # Assumes 'users' app, 'user' model
            return format_html('<a href="{}">{}</a>', link, obj.user.email)
        return "-"
    user_link_ro.short_description = _("User")

    def tenant_name_display(self, obj):
        return obj.tenant.name if obj.tenant else '-'
    tenant_name_display.short_description = _("Tenant")
    tenant_name_display.admin_order_field = 'tenant__name'

    def tenant_link_ro(self, obj):
        if obj.tenant:
            link = reverse("admin:users_tenant_change", args=[obj.tenant.id]) # Assumes 'users' app, 'tenant' model
            return format_html('<a href="{}">{}</a>', link, obj.tenant.name)
        return "-"
    tenant_link_ro.short_description = _("Tenant")

    def amount_currency(self, obj):
        return f"{obj.amount} {obj.currency}"
    amount_currency.short_description = _("Amount")

    def status_display(self, obj):
        return obj.get_status_display()
    status_display.short_description = _("Status")
    status_display.admin_order_field = 'status'

    def payment_method_display(self, obj):
        return obj.get_payment_method_used_display() if obj.payment_method_used else '-'
    payment_method_display.short_description = _("Method")

    def gateway_transaction_id_short(self, obj):
        if obj.gateway_transaction_id and len(obj.gateway_transaction_id) > 20:
            return obj.gateway_transaction_id[:17] + "..."
        return obj.gateway_transaction_id
    gateway_transaction_id_short.short_description = _("Gateway Txn ID")

    def initiated_at_short(self, obj):
        return obj.initiated_at.strftime('%Y-%m-%d %H:%M')
    initiated_at_short.short_description = _("Initiated")
    initiated_at_short.admin_order_field = 'initiated_at'

    def formatted_gateway_response_payload(self, obj):
        if obj.gateway_response_payload:
            return format_html("<pre>{}</pre>", json.dumps(obj.gateway_response_payload, indent=2, sort_keys=True))
        return "-"
    formatted_gateway_response_payload.short_description = _('Gateway Response')


    def has_add_permission(self, request):
        return False # Transactions are created programmatically

    def has_change_permission(self, request, obj=None):
        # Allow superuser to change for corrections, but generally immutable
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        # Allow superuser to delete for corrections, but generally immutable
        return request.user.is_superuser