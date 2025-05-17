# backend/ai_engine/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'model-families', views.AIModelFamilyViewSet, basename='ai-model-family')
router.register(r'model-versions', views.AIModelVersionViewSet, basename='ai-model-version')
router.register(r'feedback', views.AIFeedbackViewSet, basename='ai-feedback')

# Read-only log endpoints
router.register(r'logs/nlu', views.NLULogViewSet, basename='nlu-log')
router.register(r'logs/recommendation-requests', views.RecommendationRequestLogViewSet, basename='recommendation-request-log')


urlpatterns = [
    path('', include(router.urls)),
    # Example of a specific utility endpoint not part of a ViewSet, though the action in AIModelVersionViewSet is better
    # path('model-versions    filter_backends = [DjangoFilterBackend]
    filterset_fields = {
        'timestamp': ['date__gte', 'date__lte', 'date'],
        'user__email': ['exact', 'icontains'],
        'tenant__name': ['exact', 'icontains'],
        'restaurant__name': ['exact', 'icontains'],
        'detected_intent_name': ['exact', 'icontains'],
        'ai_model_version__model_family__name': ['exact'],
        'ai_model_version__version_identifier': ['exact'],
        'session_id': ['exact'],
    }
    ordering_fields = ['timestamp', 'user__email', 'detected_intent_name']
    ordering = ['-timestamp']


class RecommendationRequestLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = RecommendationRequestLog.objects.select_related(
        'user', 'tenant', 'restaurant', 'ai_model_version', 'ai_model_version__model_family',
        'trigger_context_menu_item'
    ).prefetch_related('recommended_items_logged', 'recommended_items_logged__recommended_menu_item').all() # Prefetch for nested serializer
    serializer_class = RecommendationRequestLogSerializer
    permission_classes = PERMISSION_CLASSES_FOR_ADMIN_API
    filter_backends = [DjangoFilterBackend]
    filterset_fields = {
        'timestamp': ['date__gte', 'date__lte', 'date'],
        'user__email': ['exact', 'icontains'],
        'tenant__name': ['exact', 'icontains'],
        'restaurant__name': ['exact', 'icontains'],
        'trigger_event_type': ['exact'],
        'ai_model_version__model_family__name': ['exact'],
    }
    ordering_fields = ['timestamp', 'user__email', 'trigger_event_type']
    ordering = ['-timestamp']


# RecommendedItemLog is usually viewed nested within RecommendationRequestLog.
# If a direct listing is needed:
# class RecommendedItemLogViewSet(viewsets.ReadOnlyModelViewSet):
#     queryset = RecommendedItemLog.objects.select_related('request_log', 'recommended_menu_item').all()
#     serializer_class = RecommendedItemLogSerializer
#     permission_classes = PERMISSION_CLASSES_FOR_ADMIN_API
#     filter_backends = [DjangoFilterBackend]
#     filterset_fields = ['request_log__user__email', '/get-active-production/', views.GetActiveProductionModelView.as_view(), name='get-active-production-model'),
]