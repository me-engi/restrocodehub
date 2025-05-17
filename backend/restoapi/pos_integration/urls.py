# backend/pos_integration/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Router for managing POS Configurations (by Tenant Admins for their own, or Platform Admins for all)
# This could be nested under a restaurant if a tenant admin is accessing it.
# /api/my-tenant-space/restaurants/{restaurant_pk}/pos-config/
# Or a direct path for platform admins.
# For simplicity, let's define a router that can be included as needed.
pos_config_router = DefaultRouter()
pos_config_router.register(
    r'configurations', # e.g., /api/pos-integration/platform-admin/configurations/
    views.RestaurantPOSConfigurationViewSet,
    basename='pos-configuration'
)

# Router for viewing POS Integration Logs (Platform Admin only)
pos_log_router = DefaultRouter()
pos_log_router.register(
    r'logs',
    views.POSIntegrationLogViewSet,
    basename='pos-integration-log'
)

urlpatterns = [
    # Generic Webhook Endpoint
    # The client (POS system) needs to be configured to send to this specific URL.
    # The pos_system_name and restaurant_id help route it.
    path('webhooks/<str:pos_system_name>/<uuid:restaurant_id>/',
         views.GenericPOSWebhookView.as_view(),
         name='pos-webhook-generic'),

    # --- APIs typically for Platform Admins or specific Tenant Admin dashboards ---
    # These would be mounted under appropriate prefixes in your project's main urls.py
    # Example:
    path('management/', include(pos_config_router.urls)), # For platform admin managing all configs
    path('monitoring/', include(pos_log_router.urls)),     # For platform admin viewing all logs

    # Note: Tenant admin access to their specific POS config might be better handled
    # as a detail route on the MyTenantRestaurantViewSet in `restaurants.views`
    # e.g. /api/my-tenant-space/restaurants/{restaurant_pk}/pos-configuration/ (GET, PUT)
]