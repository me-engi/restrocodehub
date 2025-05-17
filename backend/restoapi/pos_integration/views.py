# backend/pos_integration/views.py
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status, generics, views
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend

from .models import RestaurantPOSConfiguration, POSIntegrationLog
from .serializers import RestaurantPOSConfigurationSerializer, POSIntegrationLogSerializer
from restaurants.models import Restaurant # For context
from .permissions import IsTenantAdminAndOwnsRestaurantForPOSConfig, IsPlatformAdminForPOSAccess
from users.permissions import IsPlatformAdmin, IsTenantAdmin # From users app

# --- Placeholder for actual POS interaction services ---
# These would live in pos_integration/services/square_service.py, toast_service.py etc.
# from .services import pos_service_factory

# def get_pos_service(pos_config: RestaurantPOSConfiguration):
#     return pos_service_factory.get_service(pos_config.pos_system_type, pos_config)


class RestaurantPOSConfigurationViewSet(viewsets.ModelViewSet):
    """
    Manages POS configurations for restaurants.
    Tenant Admins manage configs for their own restaurants.
    Platform Admins manage all configs.
    """
    serializer_class = RestaurantPOSConfigurationSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser or user.role == 'platform_admin':
            return RestaurantPOSConfiguration.objects.select_related('restaurant', 'restaurant__tenant').all()
        elif user.role == 'tenant_admin' and hasattr(user, 'tenant') and user.tenant:
            return RestaurantPOSConfiguration.objects.select_related('restaurant').filter(restaurant__tenant=user.tenant)
        return RestaurantPOSConfiguration.objects.none()

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy', 'trigger_menu_sync', 'trigger_inventory_sync']:
            # Tenant admin can manage their own, Platform admin can manage all
            # The IsTenantAdminAndOwnsRestaurantForPOSConfig checks object ownership for update/delete.
            # For create, we need to ensure tenant admin creates for their own restaurant.
            return [IsAuthenticated(), (IsTenantAdmin | IsPlatformAdmin)()] # Simplified union for now
        return [IsAuthenticated(), IsPlatformAdmin()] # List/retrieve by platform admin

    def perform_create(self, serializer):
        user = self.request.user
        restaurant_id = self.request.data.get('restaurant') # Expect restaurant ID in request
        restaurant = get_object_or_404(Restaurant, pk=restaurant_id)

        if user.role == 'tenant_admin':
            if restaurant.tenant != user.tenant:
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied("You can only configure POS for restaurants within your tenant.")
        elif not (user.is_superuser or user.role == 'platform_admin'):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You do not have permission to perform this action.")
        
        # Check if a config already exists for this restaurant
        if RestaurantPOSConfiguration.objects.filter(restaurant=restaurant).exists():
            from rest_framework.exceptions import ValidationError
            raise ValidationError({"restaurant": "A POS configuration already exists for this restaurant."})

        serializer.save(restaurant=restaurant)

    # --- Example Actions to Trigger Syncs (would call service functions) ---
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, (IsTenantAdminAndOwnsRestaurantForPOSConfig | IsPlatformAdmin)])
    def trigger_menu_sync(self, request, pk=None):
        pos_config = self.get_object() # Checks object permissions
        if not pos_config.is_active:
            return Response({"error": "POS integration is not active for this restaurant."}, status=status.HTTP_400_BAD_REQUEST)
        
        # service = get_pos_service(pos_config)
        # success, message = service.sync_menu_from_pos() # Your actual service call
        success, message = True, "Mock menu sync triggered successfully." # Mock

        POSIntegrationLog.objects.create(
            pos_configuration=pos_config, log_type='MENU_SYNC_TO_PLATFORM',
            is_success=success, message=message
        )
        if success:
            pos_config.last_menu_sync_at = timezone.now()
            pos_config.last_sync_error = None
            pos_config.save(update_fields=['last_menu_sync_at', 'last_sync_error'])
            return Response({"message": message}, status=status.HTTP_200_OK)
        else:
            pos_config.last_sync_error = message
            pos_config.save(update_fields=['last_sync_error'])
            return Response({"error": message}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, (IsTenantAdminAndOwnsRestaurantForPOSConfig | IsPlatformAdmin)])
    def trigger_inventory_sync(self, request, pk=None):
        pos_config = self.get_object()
        # ... similar logic to trigger_menu_sync ...
        return Response({"message": "Inventory sync placeholder."}, status=status.HTTP_501_NOT_IMPLEMENTED)


class POSIntegrationLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only endpoint for platform admins to view POS integration logs.
    """
    queryset = POSIntegrationLog.objects.select_related(
        'pos_configuration__restaurant', 'restaurant', 'related_order'
    ).all()
    serializer_class = POSIntegrationLogSerializer
    permission_classes = [IsAuthenticated, IsPlatformAdmin] # Only platform admins
    filter_backends = [DjangoFilterBackend]
    filterset_fields = {
        'log_type': ['exact', 'in'],
        'is_success': ['exact'],
        'restaurant': ['exact'],
        'pos_configuration__pos_system_type': ['exact'],
        'timestamp': ['date__gte', 'date__lte', 'date'],
        'related_order__order_number': ['exact', 'icontains']
    }
    search_fields = ['message', 'error_details', 'restaurant__name', 'related_order__order_number']
    ordering_fields = ['timestamp', 'log_type', 'is_success']
    ordering = ['-timestamp']


# --- Webhook Views (Example) ---
# Each POS system would have its own webhook view due to different payload structures and security.
class GenericPOSWebhookView(views.APIView):
    permission_classes = [AllowAny] # Webhooks are from external systems, security via signature

    def post(self, request, pos_system_name: str, restaurant_id: uuid.UUID, *args, **kwargs):
        """
        Generic handler for incoming POS webhooks.
        URL: /api/pos-integration/webhooks/{pos_system_name}/{restaurant_id}/
        """
        try:
            pos_config = RestaurantPOSConfiguration.objects.get(
                restaurant_id=restaurant_id,
                pos_system_type__iexact=pos_system_name, # Match POS system type case-insensitively
                is_active=True
            )
        except RestaurantPOSConfiguration.DoesNotExist:
            return Response({"error": "Active POS configuration not found for this restaurant and system type."}, status=status.HTTP_404_NOT_FOUND)

        # 1. Verify Webhook Signature (CRITICAL - specific to each POS)
        # webhook_secret = pos_config.additional_settings.get('webhook_secret')
        # if not verify_signature(request.body, request.headers, webhook_secret):
        #     POSIntegrationLog.objects.create(pos_configuration=pos_config, log_type='ERROR', message="Webhook signature verification failed.")
        #     return Response({"error": "Invalid signature"}, status=status.HTTP_403_FORBIDDEN)

        payload = request.data # Assuming JSON payload
        event_type = payload.get('event_type') # Or however the POS indicates event type

        # 2. Process the event based on pos_system_name and event_type
        # service = get_pos_service(pos_config)
        # success, message = service.handle_webhook_event(event_type, payload)
        success, message = True, f"Mock webhook event '{event_type}' processed for {pos_system_name}." # Mock

        POSIntegrationLog.objects.create(
            pos_configuration=pos_config,
            log_type=f'{pos_system_name.upper()}_WEBHOOK', # Make log_type more specific
            is_success=success,
            message=message,
            request_payload=payload # Store received payload
        )

        if success:
            return Response({"status": "webhook received and processed"}, status=status.HTTP_200_OK)
        else:
            return Response({"error": message}, status=status.HTTP_400_BAD_REQUEST)