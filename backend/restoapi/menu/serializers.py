# backend/menu/serializers.py
from rest_framework import serializers
from .models import MenuCategory, MenuItem, Ingredient, CustomizationGroup, CustomizationOption
from restaurants.serializers import RestaurantSlimSerializer # For context, if needed

class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ['id', 'name', 'tenant'] # Add other fields if any
        read_only_fields = ['id', 'tenant'] # Tenant usually set by system/context

class CustomizationOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomizationOption
        fields = ['id', 'name', 'price_adjustment', 'is_default_selected', 'is_available', 'display_order']

class CustomizationGroupSerializer(serializers.ModelSerializer):
    options = CustomizationOptionSerializer(many=True, read_only=False) # Allow creating/updating options with group

    class Meta:
        model = CustomizationGroup
        fields = ['id', 'name', 'min_selection', 'max_selection', 'is_required', 'display_order', 'options']

class MenuItemSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    restaurant_name = serializers.CharField(source='restaurant.name', read_only=True) # For context
    customization_groups = CustomizationGroupSerializer(many=True, read_only=True) # Read-only here, manage via separate endpoint or nested write
    effective_is_available = serializers.BooleanField(read_only=True) # From model property

    class Meta:
        model = MenuItem
        fields = [
            'id', 'restaurant', 'restaurant_name', 'category', 'category_name', 'name', 'description',
            'base_price', 'image', 'is_manually_hidden_by_admin', 'effective_is_available',
            'ingredients_display_text', 'display_order', 'customization_groups',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'restaurant_name', 'category_name', 'effective_is_available', 'created_at', 'updated_at']
        # 'restaurant' and 'category' will be PrimaryKeyRelatedFields for write operations if not set by context.

class MenuItemManageSerializer(serializers.ModelSerializer): # For tenant admin managing items
    customization_groups = CustomizationGroupSerializer(many=True, required=False)
    # restaurant and category will be set by context or passed as PKs

    class Meta:
        model = MenuItem
        fields = [
            'id', 'restaurant', 'category', 'name', 'description', 'base_price', 'image',
            'is_manually_hidden_by_admin', 'ingredients_display_text', 'display_order',
            'customization_groups'
        ]
        # restaurant and category are writeable here by ID (e.g. PrimaryKeyRelatedField)
        # or set in view perform_create/perform_update

    def _handle_nested_customization_groups(self, menu_item_instance, groups_data):
        # Complex logic: delete old, update existing, create new
        # For simplicity here, we'll delete all and recreate. Not ideal for production updates.
        menu_item_instance.customization_groups.all().delete()
        for group_data in groups_data:
            options_data = group_data.pop('options', [])
            group = CustomizationGroup.objects.create(menu_item=menu_item_instance, **group_data)
            for option_data in options_data:
                CustomizationOption.objects.create(group=group, **option_data)

    def create(self, validated_data):
        groups_data = validated_data.pop('customization_groups', [])
        menu_item = MenuItem.objects.create(**validated_data)
        self._handle_nested_customization_groups(menu_item, groups_data)
        return menu_item

    def update(self, instance, validated_data):
        groups_data = validated_data.pop('customization_groups', None) # If None, don't touch groups

        # Update MenuItem fields
        instance.category = validated_data.get('category', instance.category)
        instance.name = validated_data.get('name', instance.name)
        # ... update other fields ...
        instance.is_manually_hidden_by_admin = validated_data.get('is_manually_hidden_by_admin', instance.is_manually_hidden_by_admin)
        instance.save()

        if groups_data is not None: # If groups_data is provided, update them
            self._handle_nested_customization_groups(instance, groups_data)
        return instance


class MenuCategorySerializer(serializers.ModelSerializer):
    # Option 1: List item IDs
    # menu_items_ids = serializers.PrimaryKeyRelatedField(source='menu_items', many=True, read_only=True)
    # Option 2: Nested menu items (can be verbose for list view)
    menu_items = MenuItemSerializer(many=True, read_only=True) # For detail view of a category
    restaurant_name = serializers.CharField(source='restaurant.name', read_only=True)

    class Meta:
        model = MenuCategory
        fields = ['id', 'restaurant', 'restaurant_name', 'name', 'description', 'display_order', 'is_active', 'menu_items']
        read_only_fields = ['id', 'restaurant_name']
        # restaurant is writable for admin creation

class FullMenuSerializer(serializers.Serializer): # Not a ModelSerializer
    """
    Serializer for the entire menu of a restaurant, structured by categories.
    Used by GET /api/restaurants/{restaurant_id}/menu/
    """
    restaurant_id = serializers.UUIDField(read_only=True)
    restaurant_name = serializers.CharField(read_only=True)
    # last_updated_pos = serializers.DateTimeField(read_only=True) # If you track this
    categories = MenuCategorySerializer(many=True, read_only=True) # MenuCategorySerializer will nest MenuItems