# backend/menu/urls.py
from django.urls import path, include
from rest_framework_nested import routers # For nested resources
from . import views

# Router for ingredients (could be global admin or tenant admin if ingredients are tenant-scoped)
# Let's assume it's for platform admins for now, or a dedicated tenant admin section.
# If global, this router would be included in the main project urls.py under an admin prefix.
ingredient_router = routers.DefaultRouter()
ingredient_router.register(r'ingredients', views.IngredientViewSet, basename='ingredient')

# --- Routers for Tenant Admin menu management (nested under a restaurant) ---
# These will be included by the restaurants app's router for tenant management.
# e.g. /api/my-tenant-space/restaurants/{restaurant_pk}/menu-categories/
#      /api/my-tenant-space/restaurants/{restaurant_pk}/menu-items/

# This file might not have top-level urlpatterns if all its views are nested.
# Or, if IngredientViewSet is managed here:
urlpatterns = [
    # path('management/', include(ingredient_router.urls)), # If ingredients are managed via /api/menu/management/ingredients/
]

# --- Nested Routers (to be registered from restaurants.urls) ---
# In restaurants/urls.py, you would register these.
# This demonstrates how you'd set up nested routing for clarity.

# Create routers that will be nested under 'restaurants'
# This is for the MyTenantRestaurantViewSet in restaurants.views
# (Example of how you would structure it if these viewsets are included from restaurants router)

# This is conceptual, the actual registration of these nested viewsets happens in how
# you structure your MyTenantRestaurantViewSet in restaurants/views.py and its router.
# The BaseRestaurantMenuComponentViewSet shows one way by taking restaurant_pk from kwargs.

# Simpler way for now is that your main restaurant management router in restaurants/urls.py
# would include patterns for these, passing the restaurant_pk.

# If you want truly independent routers for menu components for a restaurant:
# This would be included by something like:
# path('restaurants/<uuid:restaurant_pk>/', include(restaurant_menu_router.urls))

restaurant_menu_router = routers.DefaultRouter()
restaurant_menu_router.register(r'categories', views.RestaurantMenuCategoryViewSet, basename='restaurant-menucategory')
restaurant_menu_router.register(r'items', views.RestaurantMenuItemViewSet, basename='restaurant-menuitem')

# Further nesting for customization groups under menu items
items_router = routers.NestedSimpleRouter(restaurant_menu_router, r'items', lookup='menu_item')
items_router.register(r'customization-groups', views.RestaurantCustomizationGroupViewSet, basename='menuitem-customizationgroup')

# Further nesting for customization options under groups
groups_router = routers.NestedSimpleRouter(items_router, r'customization-groups', lookup='group')
groups_router.register(r'options', views.RestaurantCustomizationOptionViewSet, basename='customizationgroup-option')

# The urlpatterns for THIS menu/urls.py might only contain the ingredient router if it's standalone.
# The nested ones are more illustrative of how you'd connect them if building a fully nested API structure.
# Most likely, the views for menu categories, items, etc., for a *specific restaurant*
# will be accessed via URLs that include the restaurant_id, and those URLs will be defined
# as part of the `restaurants` app's URL configuration or a tenant management specific URL configuration.

# For now, let's assume the main menu viewing API is in restaurants.urls.
# And menu management APIs are nested. So this urls.py can focus on global menu components
# like Ingredients if they are managed globally.
urlpatterns = [
    # This would be for platform admin managing all ingredients (if not tenant-scoped)
    # or tenant admin managing their own (if tenant-scoped and accessed via a tenant prefix)
    path('admin/ingredients/', include(ingredient_router.urls)), # Example path for ingredient management
]