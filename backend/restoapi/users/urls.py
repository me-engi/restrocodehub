# backend/users/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Router for tenant admin managing users within their tenant
tenant_user_router = DefaultRouter()
tenant_user_router.register(r'users', views.TenantUserViewSet, basename='tenant-user')

# Router for platform admin (example)
platform_admin_router = DefaultRouter()
platform_admin_router.register(r'tenants', views.PlatformTenantViewSet, basename='platform-tenant')
platform_admin_router.register(r'users', views.PlatformUserViewSet, basename='platform-user')


urlpatterns = [
    # I. Authentication
    path('auth/register/tenant/', views.TenantRegistrationView.as_view(), name='tenant-register'),
    path('auth/login/', views.LoginView.as_view(), name='user-login'),
    path('auth/token/refresh/', views.RefreshTokenView.as_view(), name='token-refresh'),
    path('auth/logout/', views.LogoutView.as_view(), name='user-logout'),
    path('auth/password/reset/request/', views.PasswordResetRequestView.as_view(), name='password-reset-request'),
    path('auth/password/reset/confirm/', views.PasswordResetConfirmView.as_view(), name='password-reset-confirm'),
    path('auth/password/change/', views.PasswordChangeView.as_view(), name='password-change'),

    # II. Current User ("Me")
    path('users/me/', views.CurrentUserView.as_view(), name='current-user-detail'),
    path('users/me/sessions/', views.CurrentUserSessionsView.as_view(), name='current-user-sessions'),
    path('users/me/sessions/<uuid:refresh_token_id>/revoke/', views.RevokeSessionView.as_view(), name='revoke-specific-session'),
    path('users/me/sessions/revoke-all-others/', views.RevokeAllOtherSessionsView.as_view(), name='revoke-all-other-sessions'),

    # III. Tenant Management (for Tenant Admins)
    path('tenants/my-tenant/', views.MyTenantDetailView.as_view(), name='my-tenant-detail'),
    path('tenants/my-tenant/subscription/', views.MyTenantSubscriptionView.as_view(), name='my-tenant-subscription'),
    path('tenants/my-tenant/subscription/manage/', views.ManageSubscriptionView.as_view(), name='manage-my-subscription'),
    path('tenants/my-tenant/', include(tenant_user_router.urls)), # for /api/tenants/my-tenant/users/

    # IV. Platform Admin (Example - mount this under a specific admin path in project urls.py)
    # path('platform-admin/', include(platform_admin_router.urls)),
]