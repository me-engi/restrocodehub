# backend/pos_integration/serializers.py
from rest_framework import serializers
from .models import RestaurantPOSConfiguration, POSIntegrationLog
from restaurants.models import Restaurant # For validating restaurant ID

class RestaurantPOSConfigurationSerializer(serializers.ModelSerializer):
    restaurant_name = serializers.CharField(source='restaurant.name', read_only=True)
    # API key and secret should NOT be exposed in GET responses if they are sensitive.
    # If needed for an admin UI that can set them, make them write_only.
    # For this example, we assume they are managed securely and not directly via API for GET.
    # api_key = serializers.CharField(write_only=True, required=False, allow_blank=True, style={'input_type': 'password'})
    # api_secret = serializers.CharField(write_only=True, required=False, allow_blank=True, style={'input_type': 'password'})

    class Meta:
        model = RestaurantPOSConfiguration
        fields = [
            'id', 'restaurant', 'restaurant_name', 'pos_system_type', 'is_active',
            'api_endpoint_url', 'pos_location_id', 'additional_settings',
            'last_menu_sync_at', 'last_inventory_sync_at', 'last_order_push_successful_at',
            'last_sync_error', 'created_at', 'updated_at'
            # Exclude api_key, api_secret from default fields list for GET requests
        ]
        read_only_fields = ('id', 'restaurant_name', 'created_at', 'updated_at',
                            'last_menu_sync_at', 'last_inventory_sync_at',
                            'last_order_push_successful_at', 'last_sync_error')
        # `restaurant` is typically set based on context (e.g., tenant admin managing their restaurant's POS config)

    def validate_restaurant(self, value):
        # In a ViewSet nested under a restaurant, this might not be needed as restaurant_id comes from URL.
        # If creating directly, ensure the restaurant exists and user has permission.
        # For now, assume restaurant ID is valid and permission checks happen in the view.
        return value

    # If api_key/secret were writable:
    # def create(self, validated_data):
    #     # If api_key and api_secret are passed, they should be encrypted here before model.save()
    #     # For example:
    #     # if 'api_key' in validated_data: validated_data['api_key'] = encrypt(validated_data['api_key'])
    #     return super().create(validated_data)
    #
    # def update(self, instance, validated_data):
    #     # if 'api_key' in validated_data: validated_data['api_key'] = encrypt(validated_data['api_key'])
    #     return super().update(instance, validated_data)


class POSIntegrationLogSerializer(serializers.ModelSerializer):
    restaurant_name = serializers.CharField(source='restaurant.name', read_only=True, allow_null=True)
    pos_config_details = serializers.CharField(source='pos_configuration.__str__', read_only=True, allow_null=True) # Example
    related_order_number = serializers.CharField(source='related_order.order_number', read_only=True, allow_null=True)
    log_type_display = serializers.CharField(source='get_log_type_display', read_only=True)

    class Meta:
        model = POSIntegrationLog
        fields = [
            'id', 'pos_configuration', 'pos_config_details', 'restaurant', 'restaurant_name',
            'log_type', 'log_type_display', 'related_order', 'related_order_number',
            'timestamp', 'is_success', 'message',
            'request_payload', 'response_payload', 'error_details'
        ]
        read_only_fields = fields # Logs are immutable via API