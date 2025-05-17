# backend/payments/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Router for platform admin viewing payment transactions
platform_admin_payment_router = DefaultRouter()
platform_admin_payment_router.register(
    r'transactions',
    views.PaymentTransactionViewSet,
    basename='payment-transaction'
)

urlpatterns = [
    # Customer/Client initiated payment
    path('initiate/', views.InitiatePaymentView.as_view(), name='payment-initiate'),

    # Webhook endpoints (these URLs must be configured in your payment gateway dashboard)
    path('webhooks/stripe/', views.StripeWebhookView.as_view(), name='webhook-stripe'),
    # path('webhooks/paypal/', views.PayPalWebhookView.as_view(), name='webhook-paypal'), # Example

    # Platform Admin access to payment transactions
    path('platform-admin/', include(platform_admin_payment_router.urls)),
]