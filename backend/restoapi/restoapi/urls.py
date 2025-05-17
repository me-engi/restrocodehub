# backend/culinary_api/urls.py (or your project's main urls.py)

from django.contrib import admin
from django.urls import path, include
from django.conf import settings # For serving media files during development
from django.conf.urls.static import static # For serving media files during development

# Import routers or views from your apps if you need to mount them specifically here,
# but generally, each app's urls.py will handle its own routing.
# Example: from orders.urls import platform_admin_order_router (if you had such a router)

# API Versioning (Optional but good practice for future)
API_PREFIX = 'api/v1/' # Example: /api/v1/

urlpatterns = [
    # 1. Django Admin Site
    path('admin/', admin.site.urls),

    # 2. Users App (Authentication, User Management, Tenant Management)
    # This assumes users.urls is structured to handle various user-related paths
    path(f'{API_PREFIX}users/', include('users.urls')), # Handles /api/v1/users/auth/, /api/v1/users/me/, /api/v1/users/tenants/my-tenant/ etc.

    # 3. Restaurants App (Customer-facing discovery, Tenant Admin management)
    # Customer facing restaurant discovery and detail
    path(f'{API_PREFIX}restaurants/', include('restaurants.urls.customer')), # e.g., restaurants/urls/customer.py for nearby, detail
    # Tenant Admin management of their own restaurants
    path(f'{API_PREFIX}tenant-admin/restaurants/', include('restaurants.urls.tenant_admin')), # e.g., restaurants/urls/tenant_admin.py for CRUD on their restaurants
    # Platform Admin management of all restaurants
    path(f'{API_PREFIX}platform-admin/restaurants/', include('restaurants.urls.platform_admin')), # e.g., restaurants/urls/platform_admin.py

    # 4. Menu App
    # Customer facing menu view (likely nested under restaurants) - handled by restaurants.urls.customer
    # Tenant Admin management of their menus (nested under restaurants) - handled by restaurants.urls.tenant_admin
    # Platform Admin management of global menu components (e.g., global ingredients if any)
    path(f'{API_PREFIX}platform-admin/menu/', include('menu.urls.platform_admin')), # e.g., menu/urls/platform_admin.py for ingredients

    # 5. Orders App (Cart, Order Placement, Order History, Staff Order Management)
    # Customer cart and order actions
    path(f'{API_PREFIX}orders/', include('orders.urls.customer')), # e.g., orders/urls/customer.py for cart, place order, my history
    # Restaurant Staff management of orders for their restaurant (often nested)
    # This could be part of restaurants.urls.tenant_admin if orders are heavily nested under restaurants
    # Or a separate path for staff if they have a dedicated portal
    path(f'{API_PREFIX}restaurant-staff/orders/', include('orders.urls.staff')), # e.g., orders/urls/staff.py for restaurant orders
    # Platform Admin oversight of all orders
    path(f'{API_PREFIX}platform-admin/orders/', include('orders.urls.platform_admin')), # e.g., orders/urls/platform_admin.py

    # 6. AI Interface App (Runtime AI interactions)
    path(f'{API_PREFIX}ai/', include('ai_interface.urls')), # e.g., /api/v1/ai/chat/, /api/v1/ai/recommendations/

    # 7. AI Engine App (Admin/Management of AI models, logs, feedback)
    # These are primarily for platform admin / MLOps
    path(f'{API_PREFIX}platform-admin/ai-engine/', include('ai_engine.urls')),

    # 8. Payments App
    # Payment initiation by customer, webhooks from gateways
    path(f'{API_PREFIX}payments/', include('payments.urls.customer_facing')), # e.g., payments/urls/customer_facing.py for initiate, webhook
    # Platform Admin viewing payment transactions
    path(f'{API_PREFIX}platform-admin/payments/', include('payments.urls.platform_admin')), # e.g., payments/urls/platform_admin.py for transactions list

    # 9. POS Integration App
    # Webhooks from POS systems
    path(f'{API_PREFIX}pos-integration/', include('pos_integration.urls.webhooks')), # e.g., pos_integration/urls/webhooks.py
    # Platform Admin management of POS configurations and logs
    path(f'{API_PREFIX}platform-admin/pos-integration/', include('pos_integration.urls.platform_admin')), # e.g., pos_integration/urls/platform_admin.py

    # --- Health Check Endpoint (Good Practice) ---
    # path(f'{API_PREFIX}health/', health_check_view, name='health-check'), # You'd need to create this view
]

# --- Serving Media Files during Development ---
# In production, your web server (Nginx) should serve media files.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    # urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) # If using collectstatic