# backend/restaurants/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Router for Tenant Admin's management of their own restaurants
my_tenant_restaurant_router = DefaultRouter()
my_tenant_restaurant_router.register(r'restaurants', views.MyTenantRestaurantViewSet, basename='my-tenant-restaurant')
# Note: Nested operating hours are handled by @action within MyTenantRestaurantViewSet

# Router for Platform Admin's management of all restaurants
platform_admin_restaurant_router = DefaultRouter()
platform_admin_restaurant_router.register(r'restaurants', views.PlatformAdminRestaurantViewSet, basename='platform-admin-restaurant')


urlpatterns = [
    # --- Customer Facing APIs ---
    path('nearby/', views.NearbyRestaurantListView.as_view(), name='restaurants-nearby-list'),
    # Using slug for public detail view is common and SEO-friendly
    path('<slug:slug>/', views.RestaurantDetailView.as_view(), name='restaurant-detail-slug'),
    path('by-id/<uuid:pk>/', views.RestaurantDetailView.as_view(), name='restaurant-detail-id'), # Alternative by ID

    # --- Tenant Admin APIs (for managing their OWN restaurants) ---
    # These would be mounted under a tenant-specific prefix in the project's main urls.py, e.g., /api/my-org/
    # For now, let's assume a prefix /api/tenant-management/
    path('tenant-management/', include(my_tenant_restaurant_router.urls)),


    # --- Platform Admin APIs (for managing ALL restaurants) ---
    # These would be mounted under a platform-admin-specific prefix, e.g., /api/platform-admin/
    path('platform-admin/', include(platform_admin_restaurant_router.urls)),
]