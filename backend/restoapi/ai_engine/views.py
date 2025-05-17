# backend/ai_engine/views.py
from rest_framework import viewsets, status, generics
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny # Import AllowAny
from users.permissions import IsPlatformAdmin # Assuming you have this from users app

from .models import AIModelFamily, AIModelVersion, AIFeedback, NLULog, RecommendationRequestLog
from .serializers import (
    AIModelFamilySerializer, AIModelVersionSerializer,
    AIFeedbackCreateSerializer, AIFeedbackDetailSerializer,
    NLULogSerializer, RecommendationRequestLogSerializer
)

class AIModelFamilyViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing AI Model Families.
    Typically accessed by Platform Admins or MLOps pipelines.
    """
    queryset = AIModelFamily.objects.all()
    serializer_class = AIModelFamilySerializer
    permission_classes = [IsAuthenticated, IsPlatformAdmin] # Only platform admins

class AIModelVersionViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing AI Model Versions.
    Typically accessed by Platform Admins or M_only=True, allow_null=True)
    # Add other fields from the item if needed, or keep it lean

    class Meta:
        model = RecommendedItemLog
        fields = [
            'id', 'recommended_menu_item', 'recommended_menu_item_name', 'rank_in_recommendation',
            'recommendation_score', 'was_displayed', 'was_clicked', 'was_added_to_cart', 'timestamp'
        ]

class RecommendationRequestLogSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True, allow_null=True)
    tenant_name = serializers.CharField(source='tenant.name', read_only=True, allow_null=True)
    restaurant_name = serializers.CharField(source='restaurant.name', read_only=True, allow_null=True)
    ai_model_version_tag = serializers.CharField(source='ai_model_version.version_identifier', read_only=True, allow_null=True)
    trigger_event_type_display = serializers.CharField(source='get_trigger_event_type_display', read_only=True)
    recommended_items_logged = RecommendedItemLogSerializer(many=True, read_only=True) # Nested recommended items

    class Meta:
        model = RecommendationRequestLog
        fields = '__all__'


# --- Feedback Serializers ---
class AIFeedbackSerializer(serializers.ModelSerializer):
    user_providing_feedback_email = serializers.EmailField(source='user_providing_feedback.email', read_only=True,LOps pipelines.
    """
    queryset = AIModelVersion.objects.select_related('model_family').all()
    serializer_class = AIModelVersionSerializer
    permission_classes = [IsAuthenticated, IsPlatformAdmin] # Only platform admins
    filterset_fields = ['model_family', 'serving_status']
    search_fields = ['version_identifier', 'description', 'model_family__name']

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsPlatformAdmin])
    def activate_production(self, request, pk=None):
        """
        Activates this model version for production use within its family.
        """
        instance = self.get_object()
        try:
            instance.activate_for_production()
            return Response({'status': 'success', 'message': f'Model version {instance.version_identifier} activated for production.'}, status=status.HTTP_200_OK)
        except Exception as e:
            # Log error e
            return Response({'status': 'error', 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    # Action to get the currently active production model for a given family_id or family_name
    @action(detail=False, methods=['get'], url_path='active-production', permission_classes=[IsAuthenticated]) # Could be less restrictive if needed internally
    def get_active_production_model(self, request):
        family_id = request.query_params.get('family_id')
        family_name = request.query_params.get('family_name')

        if not family_id and not family_name: allow_null=True)
    processed_by_admin_email = serializers.EmailField(source='processed_by_admin.email', read_only=True, allow_null=True)
    target_type_display = serializers.CharField(source='get_target_type_display', read_only=True)
    processing_status_display = serializers.CharField(source='get_processing_status_display', read_only=True)

    class Meta:
        model = AIFeedback
        fields = '__all__'
        read_only_fields = ['id', 'timestamp', 'user_providing_feedback_email', 'processed_by_admin_email',
                            'target_type_display', 'processing_status_display', 'processed_at']
        # Admins can update: processing_status, processing_notes, processed_by_admin (auto-set)

class AIFeedbackUpdateSerializer(serializers.ModelSerializer): # For admin updating status
    class Meta:
        model = AIFeedback
        fields = ['processing_status', 'processing_notes']


# --- Intent/Entity Definition Serializers (If used via API) ---
class IntentDefinitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = IntentDefinition
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

class EntityTypeDefinitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = EntityTypeDefinition
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']