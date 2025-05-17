# backend/ai_engine/serializers.py
from rest_framework import serializers
from .models import (
    AIModelFamily, AIModelVersion,
    NLULog, RecommendationLog, RecommendationInteraction,
    AIFeedback
)
from users.serializers import UserSlimSerializer  # Assuming you have this
from restaurants.serializers import RestaurantSlimSerializer  # Assuming you have this
from menu.serializers import MenuItemSlimSerializer  # Assuming you have this

class AIModelFamilySerializer(serializers.ModelSerializer):
    model_type_display = serializers.CharField(
        source='get_model_type_display',
        read_only=True
    )
    versions_count = serializers.IntegerField(
        source='versions.count',
        read_only=True
    )

    class Meta:
        model = AIModelFamily
        fields = [
            'id', 'name', 'model_type', 'model_type_display',
            'description', 'technology_stack', 'versions_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'model_type_display', 'versions_count',
            'created_at', 'updated_at'
        ]

class AIModelVersionSerializer(serializers.ModelSerializer):
    model_family_name = serializers.CharField(
        source='model_family.name',
        read_only=True
    )
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    model_family = serializers.PrimaryKeyRelatedField(
        queryset=AIModelFamily.objects.all()
    )

    class Meta:
        model = AIModelVersion
        fields = [
            'id', 'model_family', 'model_family_name',
            'version_tag', 'description', 'artifact_uri',
            'training_parameters', 'evaluation_metrics',
            'status', 'status_display', 'deployed_at',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'model_family_name', 'status_display',
            'deployed_at', 'created_at', 'updated_at'
        ]

    def validate_model_family(self, value):
        if not value:
            raise serializers.ValidationError("Model family is required.")
        return value

class NLULogSerializer(serializers.ModelSerializer):
    user = UserSlimSerializer(read_only=True)
    tenant_name = serializers.CharField(
        source='tenant.name',
        read_only=True
    )
    restaurant = RestaurantSlimSerializer(read_only=True)
    ai_model_version = AIModelVersionSerializer(read_only=True)
    detected_intent_display = serializers.CharField(
        source='get_detected_intent_display',
        read_only=True
    )

    class Meta:
        model = NLULog
        fields = [
            'id', 'timestamp', 'session_id', 'user',
            'tenant', 'tenant_name', 'restaurant',
            'ai_model_version', 'processing_time_ms',
            'user_query_raw', 'user_query_processed',
            'detected_intent', 'detected_intent_display',
            'intent_confidence', 'detected_entities',
            'fallback_used', 'request_payload',
            'response_payload'
        ]
        read_only_fields = fields

class RecommendationLogSerializer(serializers.ModelSerializer):
    user = UserSlimSerializer(read_only=True)
    tenant_name = serializers.CharField(
        source='tenant.name',
        read_only=True
    )
    restaurant = RestaurantSlimSerializer(read_only=True)
    ai_model_version = AIModelVersionSerializer(read_only=True)
    trigger_type_display = serializers.CharField(
        source='get_trigger_type_display',
        read_only=True
    )
    trigger_item = MenuItemSlimSerializer(read_only=True)

    class Meta:
        model = RecommendationLog
        fields = [
            'id', 'timestamp', 'session_id', 'user',
            'tenant', 'tenant_name', 'restaurant',
            'ai_model_version', 'processing_time_ms',
            'trigger_type', 'trigger_type_display',
            'trigger_item', 'context_items',
            'recommended_items', 'displayed_count',
            'request_payload', 'response_payload'
        ]
        read_only_fields = fields

class RecommendationInteractionSerializer(serializers.ModelSerializer):
    recommendation_log = serializers.PrimaryKeyRelatedField(
        queryset=RecommendationLog.objects.all()
    )
    item = MenuItemSlimSerializer(read_only=True)
    interaction_type_display = serializers.CharField(
        source='get_interaction_type_display',
        read_only=True
    )

    class Meta:
        model = RecommendationInteraction
        fields = [
            'id', 'recommendation_log', 'item',
            'interaction_type', 'interaction_type_display',
            'position', 'timestamp'
        ]
        read_only_fields = ['id', 'item', 'interaction_type_display', 'timestamp']

class AIFeedbackSerializer(serializers.ModelSerializer):
    feedback_type_display = serializers.CharField(
        source='get_feedback_type_display',
        read_only=True
    )
    rating_display = serializers.CharField(
        source='get_rating_display',
        read_only=True
    )
    user = UserSlimSerializer(read_only=True)
    nlu_log = NLULogSerializer(read_only=True)
    recommendation_log = RecommendationLogSerializer(read_only=True)

    class Meta:
        model = AIFeedback
        fields = [
            'id', 'feedback_type', 'feedback_type_display',
            'rating', 'rating_display', 'comment',
            'user', 'session_id', 'nlu_log',
            'recommendation_log', 'created_at',
            'processed'
        ]
        read_only_fields = [
            'id', 'feedback_type_display', 'rating_display',
            'created_at'
        ]

class AIFeedbackCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIFeedback
        fields = [
            'feedback_type', 'rating', 'comment',
            'session_id', 'nlu_log', 'recommendation_log'
        ]

class AIFeedbackUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIFeedback
        fields = ['processed']