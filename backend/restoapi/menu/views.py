# backend/menu/views.py
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend

from .models import MenuCategory, MenuItem, Ingredient, CustomizationGroup, CustomizationOption
from .serializers import (
    MenuCategorySerializer, MenuItemSerializer, MenuItemManageSerializer, FullMenuSerializer,
    IngredientSerializer, CustomizationGroupSerializer, CustomizationOptionSerializer
)
from restaurants.models import Restaurant # For fetching restaurant context
from .permissions import IsTenantAdminAndOwnsRestaurantForMenu, IsPlatformAdminOrReadOnlyForMenu
from users.permissions import IsPlatformAdmin, IsTenantAdmin # From users app

# --- Customer Facing Menu View ---

class RestaurantFullMenuView(generics.RetrieveAPIView):
    """
    API endpoint to retrieve the full menu for a specific restaurant,
    structured by categories and items.
    Accessed via /api/restaurants/{restaurant_slug_or_id}/menu/ (defined in restaurants.urls)
    """
    permission_classes = [AllowAny]
    # queryset is not used directly as we build a custom response
    
    def get_object(self):
        # Determine if lookup is by slug or ID based on URL conf
        # This view is typically part of restaurants.urls, so restaurant_pk is passed.
        restaurant_pk_or_slug = self.kwargs.get('restaurant_pk_or_slug')
        try:
            # Try UUID first
            from uuid import UUID
            restaurant_id = UUID(restaurant_pk_or_slug)
            return get_object_or_404(Restaurant, id=restaurant_id, is_operational=True)
        except ValueError:
            # Try slug
            return get_object_or_404(Restaurant, slug=restaurant_pk_or_slug, is_operational=True)


    def retrieve(self, request, *args, **kwargs):
        restaurant = self.get_object()
        categories_qs = MenuCategory.objects.filter(
            restaurant=restaurant, is_active=True
        ).prefetch_related(
            'menu_items', # All items for this category
            'menu_items__customization_groups', # All groups for each item
            'menu_items__customization_groups__options' # All options for each group
        ).order_by('display_order', 'name')

        # Further filter menu_items within categories for availability if needed
        # This can be complex if availability is dynamic. For now, serializer handles effective_is_available.
        # You might want to filter out items where effective_is_available is False before serializing.

        menu_data = {
            "restaurant_id": restaurant.id,
            "restaurant_name": restaurant.name,
            # "last_updated_pos": get_pos_sync_timestamp_for_restaurant(restaurant), # Placeholder
            "categories": categories_qs # Pass queryset to serializer
        }
        serializer = FullMenuSerializer(menu_data, context={'request': request})
        return Response(serializer.data)

# --- Ingredient Management (Platform Admin or Tenant Admin) ---
class IngredientViewSet(viewsets.ModelViewSet):
    serializer_class = IngredientSerializer
    permission_classes = [IsAuthenticated, IsPlatformAdmin] # Or a custom perm for tenant admins to manage their own
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['tenant', 'name'] # If tenant is on Ingredient model
    search_fields = ['name']

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser or user.role == 'platform_admin':
            return Ingredient.objects.all()
        elif user.role == 'tenant_admin' and hasattr(user, 'tenant') and user.tenant is not None:
            # If ingredients are tenant-scoped
            return Ingredient.objects.filter(tenant=user.tenant)
        return Ingredient.objects.none() # No access for others

    def perform_create(self, serializer):
        user = self.request.user
        if user.role == 'tenant_admin' and hasattr(user, 'tenant') and user.tenant:
            serializer.save(tenant=user.tenant)
        elif user.is_superuser or user.role == 'platform_admin':
            # Platform admin must specify tenant if ingredient is tenant-scoped and not nullable
            # Or, if tenant is nullable for global ingredients, this works.
            serializer.save() # Tenant might be in request.data
        else:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You do not have permission to create ingredients.")


# --- Menu Management (Tenant Admin for their Restaurant(s)) ---
# These ViewSets would be nested under a specific restaurant context.
# e.g., /api/my-tenant-space/restaurants/{restaurant_id}/menu-categories/
#        /api/my-tenant-space/restaurants/{restaurant_id}/menu-items/

class BaseRestaurantMenuComponentViewSet(viewsets.ModelViewSet):
    """Base ViewSet for components tied to a specific restaurant, ensuring tenant ownership."""
    permission_classes = [IsAuthenticated, IsTenantAdminAndOwnsRestaurantForMenu]

    def get_restaurant(self):
        restaurant_id = self.kwargs.get('restaurant_pk') # From URL
        restaurant = get_object_or_404(Restaurant, pk=restaurant_id)
        # Check object permission on the restaurant for the tenant admin
        self.check_object_permissions(self.request, restaurant)
        return restaurant

    def get_queryset(self):
        # This method must be overridden in subclasses
        raise NotImplementedError("get_queryset() must be implemented by subclasses")

    def perform_create(self, serializer):
        serializer.save(restaurant=self.get_restaurant())

    def perform_update(self, serializer):
        # Restaurant shouldn't change on update for these components
        serializer.save() # `restaurant` is part of the instance

    # perform_destroy default is fine, object permission check on restaurant happens.


class RestaurantMenuCategoryViewSet(BaseRestaurantMenuComponentViewSet):
    serializer_class = MenuCategorySerializer

    def get_queryset(self):
        restaurant = self.get_restaurant()
        return MenuCategory.objects.filter(restaurant=restaurant).order_by('display_order', 'name')


class RestaurantMenuItemViewSet(BaseRestaurantMenuComponentViewSet):
    serializer_class = MenuItemManageSerializer # Use manage serializer for CRUD

    def get_queryset(self):
        restaurant = self.get_restaurant()
        return MenuItem.objects.filter(restaurant=restaurant).select_related('category').prefetch_related(
            'customization_groups', 'customization_groups__options'
        ).order_by('category__display_order', 'category__name', 'display_order', 'name')

    # Nested CRUD for CustomizationGroups and Options would go here as @action
    # similar to OperatingHours in restaurants.views, or use separate ViewSets
    # e.g., /api/my-tenant-space/menu-items/{item_id}/customization-groups/


class RestaurantCustomizationGroupViewSet(viewsets.ModelViewSet): # Assumes MenuItem context in URL
    serializer_class = CustomizationGroupSerializer
    permission_classes = [IsAuthenticated, IsTenantAdminAndOwnsRestaurantForMenu] # Custom permission needed

    def get_menu_item(self):
        menu_item_id = self.kwargs.get('menu_item_pk')
        menu_item = get_object_or_404(MenuItem, pk=menu_item_id)
        # Check permission based on menu_item.restaurant.tenant
        self.check_object_permissions(self.request, menu_item) # Pass menu_item to permission
        return menu_item

    def get_queryset(self):
        menu_item = self.get_menu_item()
        return CustomizationGroup.objects.filter(menu_item=menu_item).prefetch_related('options').order_by('display_order')

    def perform_create(self, serializer):
        serializer.save(menu_item=self.get_menu_item())


class RestaurantCustomizationOptionViewSet(viewsets.ModelViewSet): # Assumes Group context in URL
    serializer_class = CustomizationOptionSerializer
    permission_classes = [IsAuthenticated, IsTenantAdminAndOwnsRestaurantForMenu] # Custom permission needed

    def get_customization_group(self):
        group_id = self.kwargs.get('group_pk')
        group = get_object_or_404(CustomizationGroup, pk=group_id)
        # Check permission based on group.menu_item.restaurant.tenant
        self.check_object_permissions(self.request, group) # Pass group to permission
        return group

    def get_queryset(self):
        group = self.get_customization_group()
        return CustomizationOption.objects.filter(group=group).order_by('display_order')

    def perform_create(self, serializer):
        serializer.save(group=self.get_customization_group())