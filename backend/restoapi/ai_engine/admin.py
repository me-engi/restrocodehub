# backend/ai_engine/admin.py
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html # For custom display
from .models import (
    AIModelFamily, AIModelVersion,
    NLULog, RecommendationRequestLog, RecommendedItemLog,
    AIFeedback, IntentDefinition, EntityTypeDefinition
)

@admin.register(AIModelFamily)
class AIModelFamilyAdmin(admin.ModelAdmin):
    list_display = ('name', 'description_short', 'technology_stack', 'created_at', 'updated_at')
    search_fields = ('name', 'description', 'technology_stack')
    readonly_fields = ('id', 'created_at', 'updated_at')
    fieldsets = (
        (None, {'fields': ('id', 'name', 'description', 'technology_stack')}),
        (_('Timestamps'), {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )

    def description_short(self, obj):
        return (obj.description[:75] + '...') if obj.description and len(obj.description) > 75 else obj.description
    description_short.short_description = _('Description')


class AIModelVersionInline(admin.TabularInline): # Or StackedInline
    model = AIModelVersion
    fk_name = 'model_family'
    fields = ('version_identifier', 'serving_status', 'description_short', 'deployed_at', 'is_production_link')
    readonly_fields = ('deployed_at', 'is_production_link')
    extra = 0
    show_change_link = True # Link to the full AIModelVersion change page
    ordering = ('-created_at',)

    def description_short(self, obj):
        return (obj.description[:50] + '...') if obj.description and len(obj.description) > 50 else obj.description
    description_short.short_description = _('Description')

    @admin.display(description=_('Set Prod Active'))
    def is_production_link(self, obj):
        if obj.serving_status != 'PRODUCTION_ACTIVE':
            # You'd need to implement a custom admin view/action for this
            # For now, this is a placeholder or visual cue
            return format_html('<a href="javascript:alert(\'Implement activate_production action or view\');">Activate</a>')
        return _("Currently Active")
    is_production_link.allow_tags = True # Deprecated in Django 4, use format_html


@admin.register(AIModelVersion)
class AIModelVersionAdmin(admin.ModelAdmin):
    list_display = ('version_identifier', 'model_family_name', 'serving_status_display', 'artifact_uri_short', 'deployed_at', 'created_at')
    list_filter = ('serving_status', 'model_family', 'created_at', 'deployed_at')
    search_fields = ('version_identifier', 'description', 'artifact_uri', 'model_family__name')
    readonly_fields = ('id', 'created_at', 'updated_at', 'deployed_at')
    actions = ['set_selected_as_production_active', 'set_selected_as_development']
    fieldsets = (
        (None, {'fields': ('id', 'model_family', 'version_identifier', 'description')}),
        (_('Artifact & Configuration'), {'fields': ('artifact_uri', 'training_parameters', 'evaluation_metrics', 'training_data_info')}),
        (_('Deployment'), {'fields': ('serving_status', 'deployed_at')}),
        (_('Timestamps'), {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )
    list_select_related = ('model_family',) # Optimize query

    def model_family_name(self, obj):
        return obj.model_family.name
    model_family_name.short_description = _('Model Family')
    model_family_name.admin_order_field = 'model_family__name'

    def serving_status_display(self, obj):
        return obj.get_serving_status_display()
    serving_status_display.short_description = _('Serving Status')
    serving_status_display.admin_order_field = 'serving_status'

    def artifact_uri_short(self, obj):
        return (obj.artifact_uri[:75] + '...') if obj.artifact_uri and len(obj.artifact_uri) > 75 else obj.artifact_uri
    artifact_uri_short.short_description = _('Artifact URI')

    @admin.action(description=_('Set selected versions to PRODUCTION_ACTIVE'))
    def set_selected_as_production_active(self, request, queryset):
        updated_count = 0
        for version in queryset:
            try:
                version.activate_for_production() # Call your model method
                updated_count += 1
            except Exception as e:
                self.message_user(request, f"Error activating {version}: {e}", level='error')
        if updated_count > 0:
            self.message_user(request, f"{updated_count} model version(s) successfully set to PRODUCTION_ACTIVE.")

    @admin.action(description=_('Set selected versions to DEVELOPMENT'))
    def set_selected_as_development(self, request, queryset):
        updated_count = queryset.update(serving_status='DEVELOPMENT', deployed_at=None)
        self.message_user(request, f"{updated_count} model version(s) set to DEVELOPMENT.")


# --- Log Admins (Generally Read-Only) ---

class BaseLogAdmin(admin.ModelAdmin):
    """Yes, absolutely! An `admin.py` for the `ai_engine` app is crucial for platform administrators to easily manage AI model versions, review logs, and process feedback directly through the Django Admin interface.

Here's a comprehensive `admin.py` for your `ai_engine` models:

**`backend/ai_engine/admin.py`:**

```python
# backend/ai_engine/admin.py
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html # For formatting JSON in admin
import json # For pretty printing JSON

from .models import (
    AIModelFamily, AIModelVersion,
    NLULog, RecommendationRequestLog, RecommendedItemLog,
    AIFeedback, IntentDefinition, EntityTypeDefinition
)

# --- AI Model Family Admin ---
@admin.register(AIModelFamily)
class AIModelFamilyAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'technology_stack', 'created_at', 'updated_at')
    search_fields = ('name', 'description', 'technology_stack')
    list_filter = ('technology_stack', 'created_at')
    readonly_fields = ('id', 'created_at', 'updated_at')

# --- AI Model Version Admin ---
@admin.register(AIModelVersion)
class AIModelVersionAdmin(admin.ModelAdmin):
    list_display = ('version_identifier', 'model_family_name_display', 'serving_status', 'artifact_uri_preview', 'deployed_at', 'created_at')
    list_filter = ('serving_status', 'model_family', 'deployed_at', 'created_at')
    search_fields = ('version_identifier', 'model_family__name', 'description', 'artifact_uri')
    readonly_fields = ('id', 'created_at', 'updated_at', 'deployed_at')
    list_select_related = ('model_family',) # Optimize query for list display
    actions = ['activate_selected_for_production']

    fieldsets = (
        (None, {
            'fields': ('id', 'model_family', 'version_identifier', 'description')
        }),
        (_('Artifact & Configuration'), {
            'fields': ('artifact_uri', 'training_parameters', 'evaluation_metrics', 'training_data_info')
        }),
        (_('Deployment Status'), {
            'fields': ('serving_status', 'deployed_at')
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def model_family_name_display(self, obj):
        return obj.model_family.name
    model_family_name_display.short_description = _('Model Family')
    model_family_name_display.admin_order_field = 'model_family__name'

    def artifact_uri_preview(self, obj):
        if obj.artifact_uri and len(obj.artifact_uri) > 50:
            return f"{obj.artifact_uri[:47]}..."
        return obj.artifact_uri
    artifact_uri_preview.short_description = _('Artifact URI')

    @admin.action(description=_('Activate selected versions for Production'))
    def activate_selected_for_production(self, request, queryset):
        activated_count = 0
        errors = []
        for version in queryset:
            try:
                # Ensure only one active per family logic is handled in the model's method
                version.activate_for_production()
                activated_count += 1
            except Exception as e:
                errors.append(f"Error activating {version}: {str(e)}")
        
        if activated_count:
            self.message_user(request, _(f"{activated_count} model version(s) successfully activated for production."))
        if errors:
            self.message_user(request, _("Errors occurred during activation: ") + "; ".join(errors), level='ERROR')


# --- Base Log Admin (for common log display functionality) ---
class BaseLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'user_display', 'tenant_display', 'restaurant_display', 'session_id_preview', 'ai_model_version_display', 'processing_time_ms_display')
    list_filter = ('timestamp', 'user__email', 'tenant__name', 'restaurant__name', 'ai_model_version__model_family__name')
    search_fields = ('session_id', 'user__email', 'tenant__name', 'restaurant__name')
    readonly_fields = [f.name for f in AILogBase._meta.fields] + ['id'] # Make all base fields read-only
    date_hierarchy = 'timestamp'
    list_select_related = ('user', 'tenant', 'restaurant', 'ai_model_version', 'ai_model_version__model_family')

    def session_id_preview(self, obj):
        if obj.session_id and len(obj.session_id) > 20:
            return f"{obj.session_id[:17]}..."
        return obj.session_id
    session_id_preview.short_description = _('Session ID')

    def user_display(self, obj):
        return obj.user.email if obj.user else _('Anonymous')
    user_display.short_description = _('User')
    user_display.admin_order_field = 'user__email'

    def tenant_display(self, obj):
        return obj.tenant.name if obj.tenant else '-'
    tenant_display.short_description = _('Tenant')
    tenant_display.admin_order_field = 'tenant__name'

    def restaurant_display(self, obj):
        return obj.restaurant.name if obj.restaurant else '-'
    restaurant_display.short_description = _('Restaurant')
    restaurant_display.admin_order_field = 'restaurant__name'

    def ai_model_version_display(self, obj):
        if obj.ai_model_version:
            return f"{obj.ai_model_version.model_family.name} - {obj.ai_model_version.version_identifier}"
        return '-'
    ai_model_version_display.short_description = _('AI Model Version')
    ai_model_version_display.admin_order_field = 'ai_model_version__version_identifier'
    
    def processing_time_ms_display(self, obj):
        return f"{obj.processing_time_ms} ms" if obj.processing_time_ms is not None else '-'
    processing_time_ms_display.short_description = _('Proc. Time')


    def has_add_permission(self, request):
        return False # Logs are created by the system

    def has_change_permission(self, request, obj=None):
        return False # Logs are generally immutable

    def has_delete_permission(self, request, obj=None):
        Yes, absolutely. The Django Admin interface is an excellent tool for managing the `ai_engine` models, especially for internal review, data inspection, and some administrative tasks related to AI model versions and feedback.

Here's a comprehensive `admin.py` for your `ai_engine` app:

**`backend/ai_engine/admin.py`:**

```python
# backend/ai_engine/admin.py
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html # For custom display methods
from django.urls import reverse # For linking
from .models import (
    AIModelFamily, AIModelVersion,
    NLULog, RecommendationRequestLog, RecommendedItemLog,
    AIFeedback, IntentDefinition, EntityTypeDefinition
)

# --- AI Model Family Admin ---
@admin.register(AIModelFamily)
class AIModelFamilyAdmin(admin.ModelAdmin):
    list_display = ('name', 'description_short', 'technology_stack', 'created_at', 'updated_at')
    search_fields = ('name', 'description', 'technology_stack')
    list_filter = ('technology_stack', 'created_at')
    readonly_fields = ('id', 'created_at', 'updated_at')

    def description_short(self, obj):
        return (obj.description[:75] + '...') if obj.description and len(obj.description) > 75 else obj.description
    description_short.short_description = _('Description')


# --- AI Model Version Admin ---
@admin.register(AIModelVersion)
class AIModelVersionAdmin(admin.ModelAdmin):
    list_display = ('version_identifier', 'model_family_link', 'serving_status_display', 'deployed_at', 'created_at')
    list_filter = ('serving_status', 'model_family', 'deployed_at', 'created_at')
    search_fields = ('version_identifier', 'description', 'model_family__name', 'artifact_uri')
    readonly_fields = ('id', 'deployed_at', 'created_at', 'updated_at')
    list_select_related = ('model_family',) # Optimize query for list display
    actions = ['activate_selected_for_production']
    fieldsets = (
        (None, {
            'fields': ('id', 'model_family', 'version_identifier', 'description')
        }),
        (_('Configuration & Artifacts'), {
            'fields': ('artifact_uri', 'training_parameters', 'evaluation_metrics', 'training_data_info')
        }),
        (_('Deployment'), {
            'fields': ('serving_status', 'deployed_at')
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def model_family_link(self, obj):
        if obj.model_family:
            link = reverse("admin:ai_engine_aimodelfamily_change", args=[obj.model_family.id])
            return format_html('<a href="{}">{}</a>', link, obj.model_family.name)
        return "-"
    model_family_link.short_description = _('Model Family')
    model_family_link.admin_order_field = 'model_family__name'

    def serving_status_display(self, obj):
        return obj.get_serving_status_display()
    serving_status_display.short_description = _('Serving Status')
    serving_status_display.admin_order_field = 'serving_status'


    @admin.action(description=_('Activate selected version(s) for Production'))
    def activate_selected_for_production(self, request, queryset):
        activated_count = 0
        for version in queryset:
            try:
                version.activate_for_production()
                activated_count += 1
            except Exception as e:
                self.message_user(request, f"Error activating {version}: {e}", level='ERROR')
        if activated_count > 0:
            self.message_user(request, f"{activated_count} model version(s) successfully activated for production.")

# --- AILogBase Admin (Helper for common log fields if needed, or apply per log type) ---
# class AILogBaseAdmin(admin.ModelAdmin):
#     list_display = ('timestamp', 'user_email_display', 'tenant_name_display', 'restaurant_name_display', 'ai_model_version_link', 'session_id')
#     list_filter = ('timestamp', 'user__tenant', 'ai_model_version__model_family') # General filters
#     search_fields = ('session_id', 'user__email', 'tenant__name', 'restaurant__name')
#     readonly_fields = ('id', 'timestamp', 'session_id', 'user', 'tenant', 'restaurant', 'ai_model_version', 'processing_time_ms', 'request_payload', 'response_payload')
#     date_hierarchy = 'timestamp'
#     list_select_related = ('user', 'tenant', 'restaurant', 'ai_model_version', 'ai_model_version__model_family')

#     def user_email_display(self, obj):
#         return obj.user.email if obj.user else _('Anonymous/System')
#     user_email_display.short_description = _('User')
#     user_email_display.admin_order_field = 'user__email'

#     def tenant_name_display(self, obj):
#         return obj.tenant.name if obj.tenant else '-'
#     tenant_name_display.short_description = _('Tenant')
#     tenant_name_display.admin_order_field = 'tenant__name'

#     def restaurant_name_display(self, obj):
#         return obj.restaurant.name if obj.restaurant else '-'
#     restaurant_name_display.short_description = _('Restaurant')
#     restaurant_name_display.admin_order_field = 'restaurant__name'

#     def ai_model_version_link(self, obj):
#         if obj.ai_model_version:
#             link = reverse("admin:ai_engine_aimodelversion_change", args=[obj.ai_model_version.id])
#             return format_html('<a href="{}">{} ({})</a>', link, obj.ai_model_version.version_identifier, obj.ai_model_version.model_family.name)
#         return "-"
#     ai_model_version_link.short_description = _('AI Model Version')


# --- NLU Log Admin ---
@admin.register(NLULog)
class NLULogAdmin(admin.ModelAdmin): # Consider inheriting from AILogBaseAdmin if you create it
    list_display = ('timestamp', 'user_email_display', 'tenant_name_display', 'user_query_preview', 'detected_intent_name', 'intent_confidence_display', 'ai_model_version_link')
    list_filter = ('timestamp', 'detected_intent_name', 'user__tenant', 'ai_model_version__model_family', 'ai_model_version')
    search_fields = ('user_query_raw', 'user_query_preprocessed', 'detected_intent_name', 'user__email', 'session_id', 'tenant__name')
    readonly_fields = [f.name for f in NLULog._meta.fields] # Make all fields read-only by default
    date_hierarchy = 'timestamp'
    list_select_related = ('user', 'tenant', 'restaurant', 'ai_model_version', 'ai_model_version__model_family')

    fieldOkay, here's a comprehensive `admin.py` for your `ai_engine` app. This will make it easy for platform administrators to manage model versions, view logs, and process feedback directly through the Django Admin interface, which is often sufficient for many internal management tasks.

**`backend/ai_engine/admin.py`:**

```python
# backend/ai_engine/admin.py
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html # For displaying JSON nicely (optional)
import json # For pretty printing JSON

from .models import (
    AIModelFamily, AIModelVersion,
    NLULog, RecommendationRequestLog, RecommendedItemLog,
    AIFeedback, IntentDefinition, EntityTypeDefinition
)

# --- AI Model Family & Version Admin ---
@admin.register(AIModelFamily)
class AIModelFamilyAdmin(admin.ModelAdmin):
    list_display = ('name', 'description_short', 'technology_stack', 'created_at', 'updated_at')
    search_fields = ('name', 'description', 'technology_stack')
    list_filter = ('technology_stack', 'created_at')
    readonly_fields = ('id', 'created_at', 'updated_at')

    def description_short(self, obj):
        return (obj.description[:75] + '...') if obj.description and len(obj.description) > 75 else obj.description
    description_short.short_description = _('Description')

class AIModelVersionInline(admin.TabularInline): # Show versions under their family
    model = AIModelVersion
    fk_name = 'model_family'
    fields = ('version_identifier', 'serving_status', 'deployed_at', 'description_short', 'is_active_for_display')
    readonly_fields = ('deployed_at', 'is_active_for_display')
    extra = 0
    show_change_link = True # Link to the full AIModelVersion change form
    ordering = ('-created_at',)

    def description_short(self, obj):
        return (obj.description[:50] + '...') if obj.description and len(obj.description) > 50 else obj.description
    description_short.short_description = _('Description')

    @admin.display(boolean=True, description=_('Currently Active'))
    def is_active_for_display(self, obj):
        return obj.serving_status == 'PRODUCTION_ACTIVE'

# Re-register AIModelFamily if you want the inline
admin.site.unregister(AIModelFamily) # Unregister the basic one first
@admin.register(AIModelFamily)
class AIModelFamilyAdminWithVersions(AIModelFamilyAdmin): # Inherit from the previous one
    inlines = [AIModelVersionInline]


@admin.register(AIModelVersion)
class AIModelVersionAdmin(admin.ModelAdmin):
    list_display = ('version_identifier', 'model_family_name_display', 'serving_status', 'deployed_at', 'created_at')
    list_filter = ('serving_status', 'model_family', 'deployed_at', 'created_at')
    search_fields = ('version_identifier', 'description', 'model_family__name', 'artifact_uri')
    readonly_fields = ('id', 'created_at', 'updated_at', 'deployed_at')
    actions = ['make_production_active']
    list_select_related = ('model_family',) # Optimize query for list display

    fieldsets = (
        (None, {
            'fields': ('id', 'model_family', 'version_identifier', 'description')
        }),
        (_('Deployment & Status'), {
            'fields': ('serving_status', 'deployed_at', 'artifact_uri')
        }),
        (_('Technical Details'), {
            'fields': ('training_parameters', 'evaluation_metrics', 'training_data_info'),
            'classes': ('collapse',) # Collapsible section
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def model_family_name_display(self, obj):
        return obj.model_family.name
    model_family_name_display.short_description = _('Model Family')
    model_family_name_display.admin_order_field = 'model_family__name'

    @admin.action(description=_('Set selected version(s) to PRODUCTION_ACTIVE'))
    def make_production_active(self, request, queryset):
        # This action needs to be careful if multiple are selected from different families.
        # It's safer to activate one at a time through this action or ensure they are from the same family.
        activated_count = 0
        for version in queryset:
            try:
                # Ensure only one active per family
                AIModelVersion.objects.filter(
                    model_family=version.model_family,
                    serving_status='PRODUCTION_ACTIVE'
                ).exclude(pk=version.pk).update(serving_status='PRODUCTION_INACTIVE')

                version.serving_status = 'PRODUCTION_ACTIVE'
                version.deployed_at = timezone.now()
                version.save(update_fields=['serving_status', 'deployed_at'])
                activated_count += 1
            except Exception as e:
                self.message_user(request, _(f"Error activating {version}: {e}"), level='error')
        if activated_count:
            self.message_user(request, _(f"{activated_count} model version(s) successfully set to PRODUCTION_ACTIVE."), level='success')


# --- Log Admins (Primarily Read-Only in Admin) ---
class BaseLogAdmin(admin.ModelAdmin):
    """Base admin for log models to share common read-only settings."""
    list_display = ('timestamp', 'user_display', 'tenant_display', 'restaurant_display', 'session_id_short', 'ai_model_version_display')
    list_filter = ('timestamp', 'user', 'tenant', 'restaurant', 'ai_model_version__model_family')
    search_fields = ('session_id', 'user__email', 'tenant__name', 'restaurant__name')
    readonly_fields = [f.name for f in NLULog._meta.fields] # Make all fields read-only by default for logs
    date_hierarchy = 'timestamp'
    list_select_related = ('user', 'tenant', 'restaurant', 'ai_model_version', 'ai_model_version__model_family')

    def has_add_permission(self, request):
        return False # Logs are created programmatically

    def has_change_permission(self, request, obj=None):
        return False # Logs are immutable

    def has_delete_permission(self, request, obj=None):
        # Allow deletion by superusers for cleanup, but be cautious
        return request.user.is_superuser

    def user_display(self, obj):
        return obj.user.email if obj.user else _('Anonymous')
    user_display.short_description = _('User')
    user_display.admin_order_field = 'user__email'

    def tenant_display(self, obj):
        return obj.tenant.name if obj.tenant else '-'
    tenant_display.short_description = _('Tenant')
    tenant_display.admin_order_field = 'tenant__name'

    def restaurant_display(self, obj):
        return obj.restaurant.name if obj.restaurant else '-'
    restaurant_display.short_description = _('Restaurant')
    restaurant_display.admin_order_field = 'restaurant__name'

    def session_id_short(self, obj):
        return (obj.session_id[:15] + '...') if obj.session_id and len(obj.session_id) > 15 else obj.session_id
    sessionOkay, here's a comprehensive `admin.py` for your `ai_engine` app. This will provide a powerful interface for platform administrators to manage AI model versions, review logs, and process feedback directly through the Django Admin.

**`backend/ai_engine/admin.py`:**

```python
# backend/ai_engine/admin.py
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html # For displaying JSON nicely
import json # For pretty printing JSON
from django.urls import reverse
from django.utils.safestring import mark_safe

from .models import (
    AIModelFamily, AIModelVersion,
    NLULog, RecommendationRequestLog, RecommendedItemLog,
    AIFeedback, IntentDefinition, EntityTypeDefinition
)

# --- Inlines for better context ---

class AIModelVersionInline(admin.TabularInline):
    model = AIModelVersion
    fk_name = 'model_family'
    fields = ('version_identifier', 'description', 'serving_status', 'deployed_at', 'is_model_active_link')
    readonly_fields = ('deployed_at', 'is_model_active_link')
    extra = 0
    show_change_link = True
    verbose_name = _("Version")
    verbose_name_plural = _("Model Versions")

    def is_model_active_link(self, obj):
        if obj.serving_status == 'PRODUCTION_ACTIVE':
            return _("Yes (Active)")
        link = reverse('admin:ai_engine_aimodelversion_activate_production', args=[obj.pk]) # Custom admin URL
        return mark_safe(f'<a href="{link}" class="button">Activate for Production</a>')
    is_model_active_link.short_description = _('Set Active Production')


class RecommendedItemLogInline(admin.TabularInline):
    model = RecommendedItemLog
    fk_name = 'request_log'
    fields = ('recommended_menu_item_link', 'rank_in_recommendation', 'recommendation_score', 'was_clicked', 'was_added_to_cart')
    readonly_fields = ('recommended_menu_item_link', 'rank_in_recommendation', 'recommendation_score', 'was_clicked', 'was_added_to_cart')
    extra = 0
    can_delete = False
    show_change_link = True # Link to RecommendedItemLog admin if you register it separately
    verbose_name = _("Recommended Item")
    verbose_name_plural = _("Recommended Items Logged")

    def recommended_menu_item_link(self, obj):
        if obj.recommended_menu_item:
            # Assuming MenuItem has an admin change view
            link = reverse('admin:menu_menuitem_change', args=[obj.recommended_menu_item.pk]) # Adjust app_label and model_name
            return mark_safe(f'<a href="{link}">{obj.recommended_menu_item.name}</a>')
        return "-"
    recommended_menu_item_link.short_description = _("Menu Item")

    def has_add_permission(self, request, obj=None):
        return False


class AIFeedbackInlineForNLULog(admin.TabularInline):
    model = AIFeedback
    fk_name = 'nlu_log_context'
    fields = ('feedback_type', 'user_providing_feedback_link', 'rating_score', 'comment_preview', 'processing_status')
    readonly_fields = ('feedback_type', 'user_providing_feedback_link', 'rating_score', 'comment_preview', 'processing_status')
    extra = 0
    can_delete = False
    show_change_link = True
    verbose_name_plural = _("Feedback on this NLU Log")

    def user_providing_feedback_link(self, obj):
        if obj.user_providing_feedback:
            link = reverse('admin:users_user_change', args=[obj.user_providing_feedback.pk]) # Adjust app_label 'users'
            return mark_safe(f'<a href="{link}">{obj.user_providing_feedback.email}</a>')
        return _("Anonymous")
    user_providing_feedback_link.short_description = _("Feedback By")

    def comment_preview(self, obj):
        return (obj.comment[:50] + '...') if obj.comment and len(obj.comment) > 50 else obj.comment
    comment_preview.short_description = _("Comment")

    def has_add_permission(self, request, obj=None):
        return False

# --- ModelAdmins ---

@admin.register(AIModelFamily)
class AIModelFamilyAdmin(admin.ModelAdmin):
    list_display = ('name', 'description_preview', 'technology_stack', 'active_version_count', 'created_at')
    search_fields = ('name', 'description', 'technology_stack')
    readonly_fields = ('id', 'created_at', 'updated_at')
    inlines = [AIModelVersionInline]
    fieldsets = (
        (None, {'fields': ('id', 'name', 'description', 'technology_stack')}),
        (_('Timestamps'), {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )

    def description_preview(self, obj):
        return (obj.description[:75] + '...') if obj.description and len(obj.description) > 75 else obj.description
    description_preview.short_description = _("Description")

    def active_version_count(self, obj):
        return obj.versions.filter(serving_status='PRODUCTION_ACTIVE').count()
    active_version_count.short_description = _("Active Prod. Versions")


@admin.register(AIModelVersion)
class AIModelVersionAdmin(admin.ModelAdmin):
    list_display = ('version_identifier', 'model_family_link', 'serving_status', 'artifact_uri_preview', 'deployed_at', 'created_at')
    list_filter = ('serving_status', 'model_family', 'created_at', 'deployed_at')
    search_fields = ('version_identifier', 'description', 'artifact_uri', 'model_family__name')
    readonly_fields = ('id', 'created_at', 'updated_at', 'deployed_at')
    actions = ['activate_selected_for_production', 'set_status_to_development', 'set_status_to_archived']
    fieldsets = (
        (None, {'fields': ('id', 'model_family', 'version_identifier', 'description', 'serving_status')}),
        (_('Artifact & Configuration'), {'fields': ('artifact_uri', 'training_parameters', 'evaluation_metrics', 'training_data_info')}),
        (_('Timestamps'), {'fields': ('deployed_at', 'created_at', 'updated_at'), 'classes': ('collapse',)}),
    )

    def model_family_link(self, obj):
        link = reverse('admin:ai_engine_aimodelfamily_change', args=[obj.model_family.pk])
        return mark_safe(f'<a href="{link}">{obj.model_family.name}</a>')
    model_family_link.short_description = _("Model Family")
    model_family_link.admin_order_field = 'model_family__name'

    def artifact_uri_preview(self, obj):
        return (obj.artifact_uri[:75] + '...') if obj.artifact_uri and len(obj.artifact_uri) > 75 else obj.artifact_uri
    artifact_uri_preview.short_description = _("Artifact URI")

    @admin.action(description=_('Activate selected version(s) for Production'))
    def activate_selected_for_production(self, request, queryset):
        activated_count = 0
        for instance in queryset:
            try:
                instance.activate_for_production()
                activated_count += 1
            except Exception as e: # Catch any errors during activation
                self.message_user(request, _(f"Error activating {instance}: {e}"), level='error')
        if activated_count > 0:
            self.message_user(request, _(f"{activated_count} model version(s) successfully activated for production."))

    @admin.action(description=_('Set selected version(s) status to Development'))
    def set_status_to_development(self, request, queryset):
        updated_count = queryset.update(serving_status='DEVELOPMENT', deployed_at=None)
        self.message_user(request, _(f"{updated_count} model version(s) status set to Development."))

    @admin.action(description=_('Archive selected version(s)'))
    def set_status_to_archived(self, request, queryset):
        updated_count = queryset.update(serving_status='DEPRECATED', deployed_at=None) # Or a new ARCHIVED status
        self.message_user(request, _(f"{updated_count} model version(sYes, absolutely! An `admin.py` for the `ai_engine` app is crucial for platform administrators to easily view, manage, and understand the AI components and their performance directly through the Django Admin interface.

Here's a comprehensive `admin.py` for your `ai_engine` models:

**`backend/ai_engine/admin.py`:**

```python
# backend/ai_engine/admin.py
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html # For formatting JSON in admin
import json # For pretty printing JSON

from .models import (
    AIModelFamily, AIModelVersion,
    NLULog, RecommendationRequestLog, RecommendedItemLog,
    AIFeedback, IntentDefinition, EntityTypeDefinition
)

# --- AI Model Family & Version Admin ---
@admin.register(AIModelFamily)
class AIModelFamilyAdmin(admin.ModelAdmin):
    list_display = ('name', 'description_short', 'technology_stack', 'created_at', 'updated_at')
    search_fields = ('name', 'description', 'technology_stack')
    list_filter = ('technology_stack', 'created_at')
    readonly_fields = ('id', 'created_at', 'updated_at')

    def description_short(self, obj):
        return (obj.description[:75] + '...') if obj.description and len(obj.description) > 75 else obj.description
    description_short.short_description = _('Description')

class AIModelVersionInline(admin.TabularInline): # Or StackedInline
    model = AIModelVersion
    fk_name = 'model_family'
    fields = ('version_identifier', 'serving_status', 'deployed_at', 'description_short', 'artifact_uri')
    readonly_fields = ('deployed_at',)
    extra = 0
    show_change_link = True # Link to the full AIModelVersion change form

    def description_short(self, obj):
        return (obj.description[:50] + '...') if obj.description and len(obj.description) > 50 else obj.description
    description_short.short_description = _('Version Description')

# Re-register AIModelFamily to include the inline if you want it on the Family page
admin.site.unregister(AIModelFamily) # Unregister the simple one first
@admin.register(AIModelFamily)
class AIModelFamilyAdminWithVersions(AIModelFamilyAdmin): # Inherit from the previous admin
    inlines = [AIModelVersionInline]


@admin.register(AIModelVersion)
class AIModelVersionAdmin(admin.ModelAdmin):
    list_display = ('version_identifier', 'model_family_name', 'serving_status', 'deployed_at', 'created_at')
    list_filter = ('serving_status', 'model_family', 'deployed_at', 'created_at')
    search_fields = ('version_identifier', 'description', 'model_family__name', 'artifact_uri')
    readonly_fields = ('id', 'created_at', 'updated_at', 'deployed_at')
    fieldsets = (
        (None, {
            'fields': ('id', 'model_family', 'version_identifier', 'description')
        }),
        (_('Configuration & Artifacts'), {
            'fields': ('artifact_uri', 'training_parameters_pretty', 'evaluation_metrics_pretty', 'training_data_info')
        }),
        (_('Deployment'), {
            'fields': ('serving_status', 'deployed_at')
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    actions = ['activate_selected_for_production']

    def model_family_name(self, obj):
        return obj.model_family.name
    model_family_name.short_description = _('Model Family')
    model_family_name.admin_order_field = 'model_family__name'

    def training_parameters_pretty(self, obj):
        if obj.training_parameters:
            return format_html("<pre>{}</pre>", json.dumps(obj.training_parameters, indent=2))
        return "-"
    training_parameters_pretty.short_description = _('Training Parameters')

    def evaluation_metrics_pretty(self, obj):
        if obj.evaluation_metrics:
            return format_html("<pre>{}</pre>", json.dumps(obj.evaluation_metrics, indent=2))
        return "-"
    evaluation_metrics_pretty.short_description = _('Evaluation Metrics')

    @admin.action(description=_('Activate selected version(s) for Production'))
    def activate_selected_for_production(self, request, queryset):
        activated_count = 0
        for version in queryset:
            try:
                version.activate_for_production()
                activated_count += 1
            except Exception as e:
                self.message_user(request, _(f"Error activating {version}: {e}"), level='error')
        if activated_count > 0:
            self.message_user(request, _(f"{activated_count} model version(s) successfully activated for production."))
    
    # Ensure JSONFields are shown as pretty-printed in readonly_fields if they are not in fieldsets
    # readonly_fields = ('id', 'created_at', 'updated_at', 'deployed_at', 'training_parameters_pretty', 'evaluation_metrics_pretty')


# --- Log Admins (Primarily Read-Only) ---
class BaseLogAdmin(admin.ModelAdmin):
    """Base admin for log models to share common configurations."""
    list_filter = ('timestamp', 'user', 'tenant', 'restaurant', 'ai_model_version__model_family')
    search_fields = ('session_id', 'user__email', 'tenant__name', 'restaurant__name')
    readonly_fields = [f.name for f in AILogBase._meta.get_fields() if not f.one_to_many and not f.many_to_many] # Make all base fields readonly
    date_hierarchy = 'timestamp'

    def has_add_permission(self, request):
        return False # Logs are created programmatically

    def has_change_permission(self, request, obj=None):
        return False # Logs are generally immutable

    def has_delete_permission(self, request, obj=None):
        # Allow deletion for superusers for cleanup, but be cautious
        return request.user.is_superuser

    def request_payload_pretty(self, obj):
        if obj.request_payload:
            return format_html("<pre>{}</pre>", json.dumps(obj.request_payload, indent=2, sort_keys=True))
        return "-"
    request_payload_pretty.short_description = _('Request Payload')

    def response_payload_pretty(self, obj):
        if obj.response_payload:
            return format_html("<pre>{}</pre>", json.dumps(obj.response_payload, indent=2, sort_keys=True))
        return "-"
    response_payload_pretty.short_description = _('Response Payload')


@admin.register(NLULog)
class NLULogAdmin(BaseLogAdmin):
    list_display = ('timestamp', 'user_email_display', 'tenant_name_display', 'user_query_raw_preview', 'detected_intent_name', 'intent_confidence_display', 'ai_model_version_display')
    search_fields = BaseLogAdmin.search_fields + ('user_query_raw', 'detected_intent_name')
    list_filter = BaseLogAdmin.list_filter + ('detected_intent_name',)
    readonly_fields = BaseLogAdmin.readonly_fields + [
        'user_query_raw', 'user_query_preprocessed', 'detected_intent_name',
        'intent_confidence', 'detected_entities_pretty', 'fallback_strategy_used',
        'nlu_engine_response_pretty'
    ]
    fieldsets = (
        (_('Log Info'), {'fields': readonly_fields[:6]}), # id, timestamp, session_id, user, tenant, restaurant
        (_('NLU Details'), {'fields': ('user_query_raw', 'user_query_preprocessed', 'detected_intent_name', 'intent_confidence', 'detected_entities_pretty', 'fallback_strategy_used', 'nlu_engine_response_pretty')}),
        (_('Technical Info'), {'fields': ('ai_model_version', 'processing_time_ms')}),
    )

    def user_email_display(self, obj): return obj.user.email if obj.user else '-'
    user_email_display.short_description = _('User')
    user_email_display.admin_order_field = 'user__email'

    def tenant_name_display(self, obj): return obj.tenant.name if obj.tenant else '-'
    tenant_name_display.short_description = _('Tenant')

    def user_query_raw_preview(self, obj):
        return (obj.user_query_raw[:75] + '...') if obj.user_query_raw and len(obj.user_query_raw) > 75 else obj.user_query_raw
    user_query_raw_preview.short_description = _('User Query')

    def intent_confidence_display(self, obj):
        return f"{obj.intent_confidence:.2%}" if obj.intent_confidence is not None else '-'
    intent_confidence_display.short_description = _('Confidence')

    def detected_entities_pretty(self, obj):
        if obj.detected_entities:
            return format_html("<pre>{}</pre>", json.dumps(obj.detected_entities, indent=2))
        return "-"
    detected_entities_pretty.short_description = _('Detected Entities')

    def nlu_engine_response_pretty(self, obj):
        if obj.nlu_engine_response:
            return format_html("<pre>{}</pre>", json.dumps(obj.nlu_engine_response, indent=2))
        return "-"
    nlu_engine_response_pretty.short_description =Base class for log admins to provide common read-only behavior."""
    list_filter = ('timestamp', 'user', 'tenant', 'restaurant', 'ai_model_version__model_family')
    search_fields = ('session_id', 'user__email', 'tenant__name', 'restaurant__name')
    readonly_fields = [f.name for f in AILogBase._meta.fields] # Make all base fields read-only
    date_hierarchy = 'timestamp'
    ordering = ('-timestamp',)
    list_per_page = 25

    def has_add_permission(self, request):
        return False # Logs are created by the system

    def has_change_permission(self, request, obj=None):
        return False # Logs are generally immutable

    def has_delete_permission(self, request, obj=None):
        if request.user.is_superuser: # Allow superuser to delete logs if absolutely necessary
            return True
        return False

    def user_display(self, obj):
        return obj.user.email if obj.user else _("Anonymous")
    user_display.short_description = _("User")
    user_display.admin_order_field = 'user__email'

    def tenant_display(self, obj):
        return obj.tenant.name if obj.tenant else '-'
    tenant_display.short_description = _("Tenant")
    tenant_display.admin_order_field = 'tenant__name'

    def model_version_display(self, obj):
        return str(obj.ai_model_version) if obj.ai_model_version else '-'
    model_version_display.short_description = _("AI Version")
    model_version_display.admin_order_field = 'ai_model_version__version_identifier'


@admin.register(NLULog)
class NLULogreturn request.user.is_superuser # Only superusers can delete logs, if ever needed


# --- NLU Log Admin ---
@admin.register(NLULog)
class NLULogAdmin(BaseLogAdmin):
    list_display = BaseLogAdmin.list_display + ('user_query_raw_preview', 'detected_intent_name', 'intent_confidence_display')
    search_fields = BaseLogAdmin.search_fields + ('user_query_raw', 'detected_intent_name')
    readonly_fields = BaseLogAdmin.readonly_fields + [
        'user_query_raw', 'user_query_preprocessed', 'detected_intent_name',
        'intent_confidence', 'detected_entities', 'fallback_strategy_used', 'nlu_engine_response'
    ]
    fieldsets = (
        (_('Log Info (from Base)'), {'fields': BaseLogAdmin.readonly_fields}),
        (_('NLU Specifics'), {'fields': (
            'user_query_raw', 'user_query_preprocessed', 'detected_intent_name',
            'intent_confidence', 'formatted_detected_entities', 'fallback_strategy_used', 'formatted_nlu_engine_response'
        )})
    )

    def user_query_raw_preview(self, obj):
        if obj.user_query_raw and len(obj.user_query_raw) > 50:
            return f"{obj.user_query_raw[:47]}..."
        return obj.user_query_raw
    user_query_raw_preview.short_description = _('User Query')

    def intent_confidence_display(self, obj):
        return f"{obj.intent_confidence:.2%}" if obj.intent_confidence is not None else '-'
    intent_confidence_display.short_description = _('Confidence')

    def formatted_detected_entities(self, obj):
        if obj.detected_entities:
            return format_html("<pre>{}</pre>", jsonsets = (
        (_('Log Info'), {'fields': ('id', 'timestamp', 'session_id', 'processing_time_ms')}),
        (_('Context'), {'fields': ('user', 'tenant', 'restaurant')}),
        (_('NLU Details'), {'fields': ('ai_model_version', 'user_query_raw', 'user_query_preprocessed', 'detected_intent_name', 'intent_confidence', 'detected_entities', 'fallback_strategy_used', 'nlu_engine_response')}),
    )

    def user_query_preview(self, obj):
        return (obj.user_query_raw[:75] + '...') if obj.user_query_raw and len(obj.user_query_raw) > 75 else obj.user_query_raw
    user_query_preview.short_description = _('User Query')

    def intent_confidence_display(self, obj):
        return f"{obj.intent_confidence:.2%}" if obj.intent_confidence is not None else "-"
    intent_confidence_display.short_description = _('Confidence')

    # Shared display methods (could be in AILogBaseAdmin if using it)
    def user_email_display(self, obj):
        return obj.user.email if obj.user else _('Anonymous/System')
    user_email_display.short_description = _('User')
    user_email_display.admin_order_field = 'user__email'

    def tenant_name_display(self, obj):
        return obj.tenant.name if obj.tenant else '-'
    tenant_name_display.short_description = _('Tenant')
    tenant_name_display.admin_order_field = 'tenant__name'

    def ai_model_version_link(self, obj):
        if obj.ai_model_version:
            link = reverse("admin:ai_engine_aimodelversion_change", args=[obj.ai_model_version.id])
            return format_html('<a href="{}">{}</a>', link, obj.ai_model_version)
        return "-"
    ai_model_version_link.short_description = _('AI Model Version')

    def has_add_permission(self, request): return False
    def has_change_permission(self, request, obj=None): return False # Logs are immutable
    def_id_short.short_description = _('Session ID')

    def ai_model_version_display(self, obj):
        if obj.ai_model_version:
            return f"{obj.ai_model_version.model_family.name} - {obj.ai_model_version.version_identifier}"
        return '-'
    ai_model_version_display.short_description = _('AI Model Version')
    ai_model_version_display.admin_order_field = 'ai_model_version__version_identifier'


@admin.register(NLULog)
class NLULogAdmin(BaseLogAdmin):
    list_display = ('timestamp', 'user_query_raw_short', 'detected_intent_name', 'intent_confidence_display', 'user_display', 'tenant_display', 'ai_model_version_display')
    list_filter = BaseLogAdmin.list_filter + ('detected_intent_name',)
    search_fields = BaseLogAdmin.search_fields + ('user_query_raw', 'user_query_preprocessed', 'detected_intent_name', 'detected_entities')
    readonly_fields = [f.name for f in NLULog._meta.fields] # All fields read-only
    fieldsets = (
        (_('Log Info'), {'fields': ('id', 'timestamp', 'session_id', 'user', 'tenant', 'restaurant', 'ai_model_version', 'processing_time_ms')}),
        (_('NLU Details'), {'fields': ('user_query_raw', 'user_query_preprocessed', 'detected_intent_name', 'intent_confidence', 'detected_entities_pretty', 'fallback_strategy_used', 'nlu_engine_response_pretty')}),
    )

    def user_query_raw_short(self, obj):
        return (obj.user_query_raw[:50] + '...') if obj.user_query_raw and len(obj.user_query_raw) > 50 else obj.user_query_raw
    user_query_raw_short.short_description = _('User Query')

    def intent_confidence_display(self, obj):
        return f"{obj.intent_confidence:.2%}" if obj.intent_confidence is not None else '-'
    intent_confidence_display.short_description = _('Confidence')

    def detected) status set to Archived/Deprecated."))

    # For the "Activate for Production" button on individual model version change_form
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<path:object_id>/activate-production/', self.admin_site.admin_view(self.process_activate_production), name='ai_engine_aimodelversion_activate_production'),
        ]
        return custom_urls + urls

    def process_activate_production(self, request, object_id, *args, **kwargs):
        instance = self.get_object(request, object_id)
        if instance:
            try:
                instance.activate_for_production()
                self.message_user(request, _(f"Model version {instance.version_identifier} activated for production."), level='success')
            except Exception as e:
                self.message_user(request, _(f"Error activating {instance.version_identifier}: {e}"), level='error')
        return HttpResponseRedirect(reverse('admin:ai_engine_aimodelversion_changelist'))


@admin.register(NLULog)
class NLULogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'user_link', 'tenant_link', 'user_query_raw_preview', 'detected_intent_name_preview', 'ai_model_version_link', 'processing_time_ms')
    list_filter = ('timestamp', 'detected_intent_name', 'ai_model_version__model_family', 'ai_model_version', 'tenant', 'user')
    search_fields = ('user_query_raw', 'user_query_preprocessed', 'session_id', 'user__email', 'tenant__name', 'detected_intent_name')
    readonly_fields = [f.name for f in NLULog._meta.fields] # All fields read-only
    date_hierarchy = 'timestamp'
    inlines = [AIFeedbackInlineForNLULog]
    fieldsets = (
        (_('Log Info'), {'fields': ('id', 'timestamp', 'session_id', 'processing_time_ms')}),
        (_('Context'), {'fields': ('user_link_ro', 'tenant_link_ro', 'restaurant_link_ro', 'ai_model_version_link_ro')}),
        (_('NLU Processing'), {'fields': ('user_query_raw', 'user_query_preprocessed', 'detected_intent_name', 'intent_confidence', 'pretty_detected_entities', 'fallback_strategy_used', ' _('NLU Engine Response')

    def ai_model_version_display(self, obj):
        return str(obj.ai_model_version) if obj.ai_model_version else '-'
    ai_model_version_display.short_description = _('AI Model Version')


class RecommendedItemLogInline(admin.TabularInline):
    model = RecommendedItemLog
    fields = ('recommended_menu_item_name_link', 'rank_in_recommendation', 'recommendation_score', 'was_clicked', 'was_added_to_cart')
    readonly_fields = ('recommended_menu_item_name_link', 'rank_in_recommendation', 'recommendation_score', 'was_clicked', 'was_added_to_cart')
    extra = 0
    can_delete = False
    show_change_link = False # No separate admin for RecommendedItemLog by default

    def recommended_menu_item_name_link(self, obj):
        if obj.recommended_menu_item:
            # Assuming you have an admin change URL for MenuItem
            # from django.urls import reverse
            # link = reverse("admin:menu_menuitem_change", args=[obj.recommended_menu_item.pk])
            # return format_html('<a href="{}">{}</a>', link, obj.recommended_menu_item.name)
            return obj.recommended_menu_item.name # Simpler for now
        return '-'
    recommended_menu_item_name_link.short_description = _('Recommended Item')

    def has_add_permission(self, request, obj=None): return False


@admin.register(RecommendationRequestLog)
class RecommendationRequestLogAdmin(BaseLogAdmin):
    list_display = ('timestamp', 'user_email_display', 'trigger_event_type_display', 'restaurant_name_display', 'ai_model_version_display')
    search_fields = BaseLogAdmin.search_fields + ('trigger_event_type', 'trigger_context_menu_item__name')
    list_filter = BaseLogAdmin.list_filter + ('trigger_event_type',)
    readonly_fields = BaseLogAdmin.readonly_fields + [
        'trigger_event_type', 'trigger_context_menu_item',
        'trigger_context_cart_items_pretty', 'request_parameters_pretty'
    ]
    fieldsets = (
        (_('Log Info'), {'fields': readonly_fields[:6]}),
        (_('Trigger & Context'), {'fields': ('trigger_event_type', 'trigger_context_menu_item', 'trigger_context_cart_items_pretty', 'request_parameters_pretty')}),
        (_('Technical Info'), {'fields': ('ai_model_version', 'processing_time_ms')}),
    )
    inlines = [RecommendedItemLogInline]

    def user_email_display(self, obj): return obj.user.email if obj.user else '-'
    user_email_displayAdmin(BaseLogAdmin):
    list_display = ('timestamp', 'user_query_preview', 'detected_intent_name_display', 'user_display', 'tenant_display', 'model_version_display', 'processing_time_ms')
    readonly_fields = BaseLogAdmin.readonly_fields + ['user_query_raw', 'user_query_preprocessed', 'detected_intent_name', 'intent_confidence', 'detected_entities', 'fallback_strategy_used', 'nlu_engine_response']
    search_fields = BaseLogAdmin.search_fields + ['user_query_raw', 'detected_intent_name']
    list_filter = BaseLogAdmin.list_filter + ('detected_intent_name',)
    fieldsets = (
        (_('Log Info'), {'fields': ('id', 'timestamp', 'session_id', 'user', 'tenant', 'restaurant')}),
        (_('NLU Processing'), {'fields': ('ai_model_version', 'processing_time_ms', 'user_query_raw', 'user_query_preprocessed')}),
        (_('NLU Results'), {'fields': ('detected_intent_name', 'intent_confidence', 'detected_entities', 'fallback_strategy_used', 'nlu_engine_response')}),
    )

    def user_query_preview(self, obj):
        return (obj.user_query_raw[:75] + '...') if obj.user_query_raw and len(obj.user_query_raw) > 75 else obj.user_query_raw
    user_query_preview.short_description = _('User Query')

    def detected_intent_name_display(self, obj):
        return obj.detected_intent_name or _("(None)")
    detected_intent_name_display.short_description = _('Detected Intent')


@admin.register(RecommendationRequestLog)
class RecommendationRequestLogAdmin(BaseLogAdmin):
    list_display = ('timestamp', 'trigger_event_type_display', 'user_display', 'tenant_display', 'restaurant_display', 'model_version_display', 'processing_time_ms')
    readonly_fields = BaseLogAdmin.readonly_fields + ['trigger_event_type', 'trigger_context_menu_item', 'trigger_context_cart_items', 'request_parameters']
    search_fields = BaseLogAdmin.search_fields + ['trigger_event_type']
    list_filter = BaseLogAdmin.list_filter + ('trigger_event_type',)
    fieldsets = (
        (_('Log Info'), {'fields': ('id', 'timestamp', 'session_id', 'user', 'tenant', 'restaurant')}),
        (_('Recommendation Context'), {'fields': ('ai_model_version', 'processing_time_ms', 'trigger_event_type', 'trigger_context_menu_item', 'trigger_context_cart_items', 'request_parameters')}),
    )
    # To show RecommendedItemLog inline:
    # inlines = [RecommendedItemLogInline] # Define this inline class below

    def trigger_event_type_display(self, obj):
        return obj.get_trigger_event_type_display()
    trigger_event_type_display.short_description = _("Trigger Event")

    def restaurant_display(self, obj):
        return obj.restaurant.name if obj.restaurant else '-'
    restaurant_display.short_description = _("Restaurant")


class RecommendedItemLogInline(admin.TabularInline):
    model = RecommendedItemLog
    fk_name = 'request_log'
    fields = ('recommended_menu_item_name_link', 'rank_in_recommendation', 'recommendation_score', 'was_clicked', 'was_added_to_cart')
    readonly_fields = ('recommended_menu_item_name_link', 'rank_in_recommendation', 'recommendation_score') # Interactions might be editable for correction
    extra = 0
    can_delete = False # Log items usually not deleted
    show_change_link = False # No separate change page for these inline items typically

    def recommended_menu_item_name_link(self, obj):
        if obj.recommended_menu_item:
            # Assuming MenuItem has a get_absolute_url or you construct the admin URL
            from django.urls import reverse
            link = reverse(f"admin:{obj.recommended_menu_item._meta.app_label}_{obj.recommended_menu_item._meta.model_name}_change", args=[obj.recommended_menu_item.pk])
            return format_html('<a href="{}">{}</a>', link, obj.recommended_menu_item.name)
        return '-'
    recommended_menu_item_name_link.short_description = _("Recommended Item")

    def has_add_permission(self, request, obj=None):
        return False

# Add the inline to RecommendationRequestLogAdmin:
# RecommendationRequestLogAdmin.inlines = [RecommendedItemLogInline]


@admin.register(AIFeedback)
class AIFeedbackAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'feedback_type_display', 'user_display', 'rating_display', 'processing_status_display', 'created_at_short')
    list_filter = ('processing_status', 'feedback_type', 'rating_score', 'timestamp', 'user_providing_feedback__tenant')
    search_fields = ('comments', 'user_providing_feedback__email', 'original_ai_output_context', 'user_suggestion_or_correction', 'session_id')
    readonly_fields = ('id', 'timestamp', 'user_providing_feedback', 'session_id', 'related_nlu_log', 'related_recommendation_request_log', 'original_ai_output_context', 'user_suggestion_or_correction', 'rating_score', 'comments', 'processed_at')
    actions = ['mark_as_reviewed', 'mark_as_actioned', 'mark_as_ignored']
    fieldsets = (
        (_('Feedback Details'), {'fields': ('id', 'timestamp', 'feedback_type', 'user_providing_feedback', 'session_id', 'rating_score', 'comments')}),
        (_('Context & AI Output'), {'fields': ('related_nlu_log', 'related_recommendation_request_log', 'original_ai_output_context', 'user_suggestion_or_correction')}),
        (_('Processing'), {'fields': ('processing_status', 'processed_by_admin', 'processed_at', 'processing_notes')}),
    )
    list_select_related = ('user_providing_feedback', 'processed_by_admin') # Optimize query

    def feedback_type_display(self, obj):
        return obj.get_feedback_type_display()
    feedback_type_display.short_description = _("Feedback Type")

    def user_display(self, obj):
        return obj.user_providing_feedback.email if obj.user_providing_feedback else _("Anonymous")
    user_display.short_description = _("Feedback By")

    def rating_display(self, obj):
        return f"{obj.rating_score} / 5" if obj.rating_score else '-'
    rating_display.short_description = _("Rating")

    def processing_status_display(self, obj):
        return obj.get_processing_status_display()
    processing_status_display.short_description = _("Status")

    def created_at_short(self, obj):
        return obj.timestamp.strftime('%Y-%m-%d %H:%M')
    created_at_short.short_description = _('Submitted At')

    def save_model(self, request, obj, form, change):
        # If status is changed by admin, and processed_by is not set, set it
        if change and 'processing_status' in form.changed_data:
            if obj.processing_status != AIFeedback.STATUS_CHOICES[0][0] and not obj.processed_by_admin: # Not NEW and no processor
                obj.processed_by_admin = request.user
                obj.processed_at = timezone.now()
        super().save_model(request, obj, form, change)

    @admin.action(description=_('Mark selected feedback as REVIEWED'))
    def mark_as_reviewed(self, request, queryset):
        queryset.update(processing_status='REVIEWED', processed_by_admin=request.user, processed_at=timezone.now())
        self.message_user(request, f"{queryset.count()} feedback entries marked as REVIEWED.")

    @admin.action(description=_('Mark selected feedback as ACTIONED'))
    def mark_as_actioned(self, request, queryset):
        queryset.update(processing_status='ACTION_TAKEN', processed_by_admin=request.user, processed_at=timezone.now())
        self.message_user(request, f"{queryset.count()} feedback entries marked as ACTIONED.")

    @admin.action(description=_('Mark selected feedback as IGNORED'))
    def mark_as_ignored(self, request, queryset): # Assuming you add 'IGNORED' to STATUS_CHOICES
        queryset.update(processing_status='REJECTED', processed_by_admin=request.user, processed_at=timezone.now()) # Example using REJECTED
        self.message_user(request, f"{queryset.count()} feedback entries marked as IGNORED/REJECTED.")


# --- Optional: Intent and Entity Definition Admins ---
@admin.register(IntentDefinition)
class IntentDefinitionAdmin(admin.ModelAdmin):
    list_display = ('name', 'description_short', 'is_active', 'created_at', 'updated_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'description', 'example_utterances')
    readonly_fields = ('id', 'created_at', 'updated_at')
    fields = ('id', 'name', 'description', 'example_utterances', 'is_active', 'created_at', 'updated_at')

    def description_short(self, obj):
        return (obj.description[:75] + '...') if obj.description and len(obj.description) > 75 else obj.description
    description_short.short_description = _('Description')


@admin.register(EntityTypeDefinition)
class EntityTypeDefinitionAdmin(admin.ModelAdmin):
    list_display = ('name', 'description_short', 'is_active', 'created_at', 'updated_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'description') # Add 'lookup_values' if you use it
    readonly_fields = ('id', 'created_at', 'updated_at')
    fields = ('id', 'name', 'description', 'is_active', 'created_at', 'updated_at') # Add 'regex_pattern', 'lookup_values' if used

    def description_short(self, obj):
        return (obj.description[:75] + '...') if obj.description and len(obj.description) > 75 else obj.description
    description_short.short_description = _('Description')