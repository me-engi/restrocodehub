# backend/restaurants/views.py
from django.db.models import Q, F, ExpressionWrapper, FloatField
from django.utils import timezone
from rest_framework import viewsets, generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from math import radians, sin, cos, sqrt, atan2, asin # For Haversine

from .models import Restaurant, OperatingHoursRule, SpecialDayOverride
from .serializers import (
    RestaurantSerializer, RestaurantManageSerializer, RestaurantSlimSerializer,
    OperatingHoursRuleSerializer, SpecialDayOverrideSerializer
)
from .permissions import IsTenantAdminAndOwnsRestaurant, IsPlatformAdminOrReadOnly
from users.permissions import IsPlatformAdmin, IsTenantAdmin # Assuming these exist

# --- Customer Facing Views ---

class NearbyRestaurantListView(generics.ListAPIView):
    """
    Lists restaurants near a given latitude/longitude.
    Requires 'lat' and 'lon' query parameters.
    Optional 'radius' (in km, default 5) and 'search' (for name) parameters.
    """
    serializer_class = RestaurantSlimSerializer # Use slim serializer for lists
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend] # For potential future filters like cuisine
    # filterset_fields = ['cuisine_tags__name'] # If you add cuisine tags

    def get_queryset(self):
        latitude_str = self.request.query_params.get('lat')
        longitude_str = self.request.query_params.get('lon')
        radius_km_str = self.request.query_params.get('radius', '5')
        search_term = self.request.query_params.get('search', None)

        if not latitude_str or not longitude_str:
            # Potentially return popular restaurants or an error, or an empty list
            # For now, let's return an empty list if no location.
            # Alternatively: raise serializers.ValidationError("Latitude and longitude are required.")
            return Restaurant.objects.none()

        try:
            latitude = float(latitude_str)
            longitude = float(longitude_str)
            radius_km = float(radius_km_str)
        except ValueError:
            return Restaurant.objects.none() # Invalid parameters

        # Base queryset: operational restaurants with location data
        queryset = Restaurant.objects.filter(is_operational=True, latitude__isnull=False, longitude__isnull=False)

        if search_term:
            queryset = queryset.filter(name__icontains=search_term)

        # Haversine distance calculation (for non-PostGIS setups)
        # This is NOT efficient for millions of records. PostGIS is the way.
        # For PostGIS, you'd use Distance functions and spatial indexes.
        
        # Convert user location to radians
        lat1_rad = radians(latitude)
        lon1_rad = radians(longitude)
        R = 6371  # Earth radius in kilometers

        # Annotate with distance. This can be slow without DB level support.
        # It's often better to filter with a bounding box first, then calculate precise distance.
        # For very large datasets, this in-Python loop is a bottleneck.
        restaurants_with_distance = []
        for restaurant in queryset: # This iterates over ALL restaurants if no search term. BE CAREFUL.
            if restaurant.latitude is None or restaurant.longitude is None:
                continue

            lat2_rad = radians(float(restaurant.latitude))
            lon2_rad = radians(float(restaurant.longitude))

            dlon = lon2_rad - lon1_rad
            dlat = lat2_rad - lat1_rad

            a = sin(dlat / 2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon / 2)**2
            c = 2 * asin(sqrt(a)) # Using asin for better precision with small distances
            distance = R * c

            if distance <= radius_km:
                restaurant.distance_km = round(distance, 2) # Annotate the instance
                restaurants_with_distance.append(restaurant)
        
        # Sort by distance
        restaurants_with_distance.sort(key=lambda r: r.distance_km)
        
        return restaurants_with_distance # Returns a list, ListAPIView handles pagination if setup


class RestaurantDetailView(generics.RetrieveAPIView):
    """
    Retrieves details for a single restaurant, including operating hours.
    """
    queryset = Restaurant.objects.filter(is_operational=True).prefetch_related(
        'operating_hours_rules', 'special_day_overrides'
    )
    serializer_class = RestaurantSerializer # Full serializer
    permission_classes = [AllowAny]
    lookup_field = 'slug' # Or 'id' or 'pk'


# --- Tenant Admin Management Views for their OWN Restaurants ---

class MyTenantRestaurantViewSet(viewsets.ModelViewSet):
    """
    Allows Tenant Admins to manage (CRUD) restaurants associated with THEIR tenant.
    """
    serializer_class = RestaurantManageSerializer
    permission_classes = [IsAuthenticated, IsTenantAdmin] # Ensure user is tenant admin

    def get_queryset(self):
        # Tenant admin can only see/manage restaurants belonging to their tenant
        return Restaurant.objects.filter(tenant=self.request.user.tenant).prefetch_related(
            'operating_hours_rules', 'special_day_overrides'
        ).order_by('name')

    def perform_create(self, serializer):
        # Automatically associate the new restaurant with the authenticated user's tenant
        serializer.save(tenant=self.request.user.tenant)

    def perform_update(self, serializer):
        # Ensure the restaurant being updated belongs to the authenticated user's tenant
        # (get_object would have already checked this if queryset is filtered, but extra safety)
        instance = serializer.instance
        if instance.tenant != self.request.user.tenant:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You do not have permission to edit this restaurant.")
        serializer.save()

    def perform_destroy(self, instance):
        if instance.tenant != self.request.user.tenant:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You do not have permission to delete this restaurant.")
        # Consider soft delete (e.g., instance.is_operational = False; instance.save())
        instance.delete()

    # Nested CRUD for OperatingHoursRule
    @action(detail=True, methods=['get', 'post'], url_path='operating-hours', serializer_class=OperatingHoursRuleSerializer)
    def operating_hours(self, request, pk=None):
        restaurant = self.get_object() # Checks permissions
        if request.method == 'POST':
            serializer = OperatingHoursRuleSerializer(data=request.data, many=isinstance(request.data, list))
            if serializer.is_valid():
                serializer.save(restaurant=restaurant)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        # GET
        queryset = OperatingHoursRule.objects.filter(restaurant=restaurant)
        serializer = OperatingHoursRuleSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get', 'put', 'patch', 'delete'], url_path='operating-hours/(?P<rule_pk>[^/.]+)', serializer_class=OperatingHoursRuleSerializer)
    def operating_hour_detail(self, request, pk=None, rule_pk=None):
        restaurant = self.get_object() # Checks permissions
        rule = get_object_or_404(OperatingHoursRule, pk=rule_pk, restaurant=restaurant)
        if request.method == 'GET':
            serializer = OperatingHoursRuleSerializer(rule)
            return Response(serializer.data)
        elif request.method in ['PUT', 'PATCH']:
            serializer = OperatingHoursRuleSerializer(rule, data=request.data, partial=(request.method == 'PATCH'))
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        elif request.method == 'DELETE':
            rule.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    # Similar nested CRUD actions can be created for SpecialDayOverride


# --- Platform Admin Management Views (Full Control) ---

class PlatformAdminRestaurantViewSet(viewsets.ModelViewSet):
    """
    Allows Platform Admins to manage ALL restaurants.
    """
    queryset = Restaurant.objects.all().select_related('tenant').prefetch_related(
        'operating_hours_rules', 'special_day_overrides'
    ).order_by('tenant__name', 'name')
    serializer_class = RestaurantManageSerializer # Uses the more comprehensive serializer
    permission_classes = [IsAuthenticated, IsPlatformAdmin] # Only platform admins
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['tenant', 'city', 'is_operational']
    search_fields = ['name', 'tenant__name', 'city', 'address_line1']

    # Platform admin explicitly sets the tenant during creation.
    # perform_create and perform_update from ModelViewSet are usually sufficient if
    # the serializer handles tenant assignment correctly (RestaurantManageSerializer has tenant as a writable PK field).