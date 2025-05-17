# backend/restaurants/serializers.py
from rest_framework import serializers
from .models import Restaurant, OperatingHoursRule, SpecialDayOverride
from users.models import Tenant # To select tenant for admin creation

class OperatingHoursRuleSerializer(serializers.ModelSerializer):
    day_of_week_display = serializers.CharField(source='get_day_of_week_display', read_only=True)

    class Meta:
        model = OperatingHoursRule
        fields = ['id', 'day_of_week', 'day_of_week_display', 'open_time', 'close_time', 'is_closed_on_this_day_override']
        # restaurant field will be handled by nested context or set implicitly

    def validate(self, data):
        # Basic validation (can be enhanced)
        is_closed = data.get('is_closed_on_this_day_override', False)
        open_time = data.get('open_time')
        close_time = data.get('close_time')

        if not is_closed:
            if not open_time or not close_time:
                raise serializers.ValidationError("Open time and close time are required if not marked as closed all day.")
            if open_time and close_time and close_time <= open_time:
                raise serializers.ValidationError("Close time must be after open time.")
        elif open_time or close_time:
            raise serializers.ValidationError("If marked as closed all day, open and close times should be blank.")
        return data

class SpecialDayOverrideSerializer(serializers.ModelSerializer):
    class Meta:
        model = SpecialDayOverride
        fields = ['id', 'date', 'is_closed_all_day', 'open_time', 'close_time', 'reason']
        # restaurant field handled by context

    def validate(self, data):
        is_closed = data.get('is_closed_all_day', False)
        open_time = data.get('open_time')
        close_time = data.get('close_time')

        if not is_closed:
            if (open_time and not close_time) or (not open_time and close_time):
                raise serializers.ValidationError("Both open and close times are required if not closed all day and either is provided.")
            if open_time and close_time and close_time <= open_time:
                raise serializers.ValidationError("Special close time must be after special open time.")
        elif open_time or close_time:
             raise serializers.ValidationError("If marked as closed all day, open and close times should be blank.")
        return data


class RestaurantSerializer(serializers.ModelSerializer):
    """
    Serializer for general restaurant information, used for listing and retrieval by customers.
    """
    # For nested operating hours (read-only in this context)
    operating_hours_rules = OperatingHoursRuleSerializer(many=True, read_only=True)
    special_day_overrides = SpecialDayOverrideSerializer(many=True, read_only=True)
    tenant_name = serializers.CharField(source='tenant.name', read_only=True) # Display tenant name
    # distance_km = serializers.FloatField(read_only=True, required=False) # If annotated by nearby view

    class Meta:
        model = Restaurant
        fields = [
            'id', 'tenant', 'tenant_name', 'name', 'slug', 'description', 'phone_number', 'public_email', 'website_url',
            'address_line1', 'address_line2', 'city', 'state_province', 'postal_code', 'country',
            'latitude', 'longitude', 'logo_image', 'banner_image', 'is_operational',
            'operating_hours_rules', 'special_day_overrides',
            'created_at', 'updated_at' # 'distance_km' (if added)
        ]
        read_only_fields = ['id', 'slug', 'tenant_name', 'created_at', 'updated_at', 'operating_hours_rules', 'special_day_overrides']
        # `tenant` field is read-only for customer-facing views, but writable for admin creation.

class RestaurantManageSerializer(serializers.ModelSerializer):
    """
    Serializer for tenant admins or platform admins to create/update restaurants.
    Includes writable nested serializers for operating hours.
    """
    operating_hours_rules = OperatingHoursRuleSerializer(many=True, required=False)
    special_day_overrides = SpecialDayOverrideSerializer(many=True, required=False)
    # tenant field can be set explicitly by platform admin, or implicitly for tenant admin
    tenant = serializers.PrimaryKeyRelatedField(queryset=Tenant.objects.all(), required=False)

    class Meta:
        model = Restaurant
        fields = [
            'id', 'tenant', 'name', 'description', 'phone_number', 'public_email', 'website_url',
            'address_line1', 'address_line2', 'city', 'state_province', 'postal_code', 'country',
            'latitude', 'longitude', 'logo_image', 'banner_image', 'is_operational',
            'operating_hours_rules', 'special_day_overrides'
        ]
        read_only_fields = ['id'] # Slug will be auto-generated

    def create(self, validated_data):
        operating_hours_data = validated_data.pop('operating_hours_rules', [])
        special_days_data = validated_data.pop('special_day_overrides', [])

        # If tenant is not provided in data (e.g., tenant admin creating),
        # it should be set in the view from request.user.tenant
        # If it is provided (platform admin creating), it will be used.
        # The `perform_create` in the view will handle setting the tenant.
        restaurant = Restaurant.objects.create(**validated_data)

        for oh_data in operating_hours_data:
            OperatingHoursRule.objects.create(restaurant=restaurant, **oh_data)
        for sd_data in special_days_data:
            SpecialDayOverride.objects.create(restaurant=restaurant, **sd_data)
        return restaurant

    def update(self, instance, validated_data):
        operating_hours_data = validated_data.pop('operating_hours_rules', None)
        special_days_data = validated_data.pop('special_day_overrides', None)

        # Update Restaurant instance fields
        # instance.tenant = validated_data.get('tenant', instance.tenant) # Tenant usually not changed
        instance.name = validated_data.get('name', instance.name)
        instance.description = validated_data.get('description', instance.description)
        # ... update other restaurant fields ...
        instance.is_operational = validated_data.get('is_operational', instance.is_operational)
        # Add all other updatable fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save() # This will also regenerate slug if name changes

        # Handle nested operating hours (more complex: need to handle create, update, delete)
        # For simplicity, this example replaces all existing rules.
        # A more robust solution would identify existing, new, and deleted rules.
        if operating_hours_data is not None:
            instance.operating_hours_rules.all().delete() # Simple: delete old, create new
            for oh_data in operating_hours_data:
                OperatingHoursRule.objects.create(restaurant=instance, **oh_data)

        if special_days_data is not None:
            instance.special_day_overrides.all().delete() # Simple: delete old, create new
            for sd_data in special_days_data:
                SpecialDayOverride.objects.create(restaurant=instance, **sd_data)

        return instance

class RestaurantSlimSerializer(serializers.ModelSerializer):
    """
    A lightweight serializer for restaurant listings, e.g., in nearby search.
    """
    distance_km = serializers.FloatField(read_only=True, required=False, allow_null=True) # For annotated distance

    class Meta:
        model = Restaurant
        fields = ['id', 'name', 'slug', 'city', 'latitude', 'longitude', 'logo_image', 'is_operational', 'distance_km']