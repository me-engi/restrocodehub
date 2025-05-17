# backend/orders/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers as nested_routers
from . import views

# --- Cart URLs ---
# The cart is mostly a singleton resource per user/session.
cart_urlpatterns = [
    path('', views.CartDetailView.as_view(), name='cart-detail'), # GET current cart
    path('add-item/', views.AddItemToCartView.as_view(), name='cart-add-item'), # POST to add
    path('clear/', views.ClearCartView.as_view(), name='cart-clear'),          # POST to clear
    path('items/<uuid:cart_item_id>/', views.CartItemUpdateDeleteView.as_view(), name='cart-item-detail'), # PATCH/PUT to update qty, DELETE to remove
]

# --- Order URLs ---
# Using a ViewSet for orders as it has list, retrieve, and custom actions
order_router = DefaultRouter()
# This router is for customer facing and general staff access to orders.
# Specific staff management of orders for THEIR restaurant might be nested.
order_router.register(r'orders', views.OrderListViewSet, basename='order')


# --- URL Patterns ---
urlpatterns = [
    path('cart/', include(cart_urlpatterns)),

    # Customer placing an order
    path('place-order/', views.OrderCreateView.as_view(), name='order-create'),

    # General Order Access (list for self/staff, retrieve for self/staff)
    # Includes /orders/ and /orders/{pk}/
    # Also includes /orders/{pk}/cancel-my-order/ action for customers
    path('', include(order_router.urls)),

    # Staff updating order status (specific endpoint)
    path('staff-update/<uuid:order_id>/', views.OrderStaffUpdateView.as_view(), name='order-staff-update'),

    # --- URLs for Restaurant Staff/Admin to manage orders for a specific restaurant ---
    # These should be nested under a restaurant route, typically defined in `restaurants.urls.py`
    # For example, if restaurants.urls has:
    #   `restaurants_router = routers.DefaultRouter()`
    #   `restaurants_router.register(r'restaurants', RestaurantViewSet, basename='restaurant')`
    #   `orders_for_restaurant_router = nested_routers.NestedSimpleRouter(restaurants_router, r'restaurants', lookup='restaurant')`
    #   `orders_for_restaurant_router.register(r'orders', RestaurantSpecificOrderViewSet, basename='restaurant-orders')`
    # Then, `RestaurantSpecificOrderViewSet` would be a ViewSet in `orders.views`
    # filtered by `self.kwargs['restaurant_pk']`.
    # For now, we're using the single OrderListViewSet with queryset filtering based on role.
]