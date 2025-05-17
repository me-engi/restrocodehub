# backend/ai_engine/models.py
import uuid
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.conf import settings  # For settings.AUTH_USER_MODEL

class AIModelFamily(models.Model):
    """
    Represents a family or type of AI model (e.g., NLU, Recommendation).
    Groups different versions of the same conceptual model.
    """
    MODEL_TYPE_CHOICES = [
        ('NLU', _('Natural Language Understanding')),
        ('RECOMMENDATION', _('Recommendation Engine')),
        ('PRICING', _('Dynamic Pricing')),
        ('VOICE', _('Voice Processing')),
        ('OTHER', _('Other')),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(
        _("model family name"),
        max_length=100,
        unique=True,
        help_text=_("Descriptive name for the model family (e.g., 'FoodOrderingNLU')")
    )
    model_type = models.CharField(
        _("model type"),
        max_length=20,
        choices=MODEL_TYPE_CHOICES,
        help_text=_("General category of this model family")
    )
    description = models.TextField(_("description"), blank=True, null=True)
    technology_stack = models.CharField(
        _("technology stack"),
        max_length=100,
        blank=True, null=True,
        help_text=_("Framework/tools used (e.g., 'TensorFlow', 'spaCy')")
    )
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)

    class Meta:
        verbose_name = _("AI model family")
        verbose_name_plural = _("AI model families")
        ordering = ['name']
        indexes = [
            models.Index(fields=['model_type']),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_model_type_display()})"


class AIModelVersion(models.Model):
    """
    Tracks specific versions of AI models within a family.
    """
    STATUS_CHOICES = [
        ('DEVELOPMENT', _('Development')),
        ('STAGING', _('Staging')),
        ('PRODUCTION_ACTIVE', _('Production (Active)')),
        ('PRODUCTION_INACTIVE', _('Production (Inactive)')),
        ('ARCHIVED', _('Archived')),
        ('EVALUATION', _('Evaluation')),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    model_family = models.ForeignKey(
        AIModelFamily,
        on_delete=models.PROTECT,
        related_name='versions',
        verbose_name=_("model family")
    )
    version_tag = models.CharField(
        _("version tag"),
        max_length=100,
        help_text=_("Version identifier (e.g., 'v1.2.0', '2023-12-release')")
    )
    description = models.TextField(_("description"), blank=True, null=True)
    artifact_uri = models.CharField(
        _("artifact URI"),
        max_length=1024,
        blank=True, null=True,
        help_text=_("Path/URI to model file or service endpoint")
    )
    training_parameters = models.JSONField(
        _("training parameters"),
        blank=True, null=True,
        help_text=_("Hyperparameters used for this version")
    )
    evaluation_metrics = models.JSONField(
        _("evaluation metrics"),
        blank=True, null=True,
        help_text=_("Performance metrics from validation/testing")
    )
    status = models.CharField(
        _("status"),
        max_length=20,
        choices=STATUS_CHOICES,
        default='DEVELOPMENT',
        db_index=True
    )
    deployed_at = models.DateTimeField(
        _("deployed at"),
        null=True, blank=True,
        help_text=_("When this version was activated in production")
    )
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)

    class Meta:
        verbose_name = _("AI model version")
        verbose_name_plural = _("AI model versions")
        ordering = ['model_family', '-created_at']
        unique_together = [['model_family', 'version_tag']]
        indexes = [
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.model_family.name} {self.version_tag} ({self.get_status_display()})"

    def set_active_production(self):
        """Activates this version as the active production model."""
        with models.transaction.atomic():
            # Deactivate other active versions in same family
            AIModelVersion.objects.filter(
                model_family=self.model_family,
                status='PRODUCTION_ACTIVE'
            ).exclude(pk=self.pk).update(
                status='PRODUCTION_INACTIVE',
                updated_at=timezone.now()
            )
            # Activate this version
            self.status = 'PRODUCTION_ACTIVE'
            self.deployed_at = timezone.now()
            self.save(update_fields=['status', 'deployed_at', 'updated_at'])


class AILogBase(models.Model):
    """
    Abstract base model for common AI interaction logging fields.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    timestamp = models.DateTimeField(
        _("timestamp"),
        default=timezone.now,
        db_index=True
    )
    session_id = models.CharField(
        _("session ID"),
        max_length=128,
        blank=True, null=True,
        db_index=True
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="%(app_label)s_%(class)s_related",
        verbose_name=_("user")
    )
    tenant = models.ForeignKey(
        'tenants.Tenant',  # String reference to avoid circular imports
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="%(app_label)s_%(class)s_related",
        verbose_name=_("tenant")
    )
    restaurant = models.ForeignKey(
        'restaurants.Restaurant',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="%(app_label)s_%(class)s_related",
        verbose_name=_("restaurant")
    )
    ai_model_version = models.ForeignKey(
        AIModelVersion,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="%(app_label)s_%(class)s_related",
        verbose_name=_("AI model version")
    )
    processing_time_ms = models.PositiveIntegerField(
        _("processing time (ms)"),
        null=True, blank=True
    )
    request_payload = models.JSONField(
        _("request payload"),
        blank=True, null=True
    )
    response_payload = models.JSONField(
        _("response payload"),
        blank=True, null=True
    )

    class Meta:
        abstract = True
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.__class__.__name__} at {self.timestamp}"


class NLULog(AILogBase):
    """
    Logs Natural Language Understanding processing events.
    """
    user_query_raw = models.TextField(
        _("raw user query"),
        help_text=_("Original user input text")
    )
    user_query_processed = models.TextField(
        _("processed query"),
        blank=True, null=True,
        help_text=_("Query after preprocessing")
    )
    detected_intent = models.CharField(
        _("detected intent"),
        max_length=100,
        blank=True, null=True,
        db_index=True
    )
    intent_confidence = models.FloatField(
        _("intent confidence"),
        null=True, blank=True
    )
    detected_entities = models.JSONField(
        _("detected entities"),
        blank=True, null=True,
        help_text=_("Extracted entities in JSON format")
    )
    fallback_used = models.BooleanField(
        _("fallback used"),
        default=False,
        help_text=_("Whether a fallback response was triggered")
    )

    class Meta:
        verbose_name = _("NLU log")
        verbose_name_plural = _("NLU logs")
        db_table = "ai_engine_nlu_logs"

    def __str__(self):
        return f"NLU: {self.user_query_raw[:50]}... -> {self.detected_intent or 'N/A'}"


class RecommendationLog(AILogBase):
    """
    Logs recommendation generation events.
    """
    TRIGGER_TYPES = [
        ('ITEM_VIEW', _('Item View')),
        ('CART_VIEW', _('Cart View')),
        ('HOMEPAGE', _('Homepage')),
        ('POST_ORDER', _('After Order')),
        ('OUT_OF_STOCK', _('Out of Stock')),
        ('USER_PROFILE', _('User Profile')),
    ]

    trigger_type = models.CharField(
        _("trigger type"),
        max_length=20,
        choices=TRIGGER_TYPES,
        db_index=True
    )
    trigger_item = models.ForeignKey(
        'menu.MenuItem',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name=_("trigger item")
    )
    context_items = models.JSONField(
        _("context items"),
        blank=True, null=True,
        help_text=_("Relevant items in context (e.g., cart items)")
    )
    recommended_items = models.JSONField(
        _("recommended items"),
        default=list,
        help_text=_("List of recommended item IDs with metadata")
    )
    displayed_count = models.PositiveIntegerField(
        _("displayed count"),
        null=True, blank=True,
        help_text=_("How many recommendations were shown")
    )

    class Meta:
        verbose_name = _("recommendation log")
        verbose_name_plural = _("recommendation logs")
        db_table = "ai_engine_recommendation_logs"

    def __str__(self):
        return f"Reco: {self.get_trigger_type_display()} -> {len(self.recommended_items)} items"


class RecommendationInteraction(models.Model):
    """
    Tracks user interactions with specific recommendations.
    """
    INTERACTION_TYPES = [
        ('IMPRESSION', _('Impression')),
        ('CLICK', _('Click')),
        ('ADD_TO_CART', _('Add to Cart')),
        ('DISMISS', _('Dismiss')),
    ]

    recommendation_log = models.ForeignKey(
        RecommendationLog,
        on_delete=models.CASCADE,
        related_name='interactions'
    )
    item = models.ForeignKey(
        'menu.MenuItem',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name=_("menu item")
    )
    interaction_type = models.CharField(
        _("interaction type"),
        max_length=20,
        choices=INTERACTION_TYPES
    )
    position = models.PositiveIntegerField(
        _("position"),
        null=True, blank=True,
        help_text=_("Position in recommendation list")
    )
    timestamp = models.DateTimeField(
        _("timestamp"),
        default=timezone.now
    )

    class Meta:
        verbose_name = _("recommendation interaction")
        verbose_name_plural = _("recommendation interactions")
        db_table = "ai_engine_recommendation_interactions"
        indexes = [
            models.Index(fields=['interaction_type']),
            models.Index(fields=['recommendation_log', 'item']),
        ]

    def __str__(self):
        return f"{self.get_interaction_type_display()} on {self.item_id}"


class AIFeedback(models.Model):
    """
    Stores explicit feedback on AI system outputs.
    """
    FEEDBACK_TYPES = [
        ('NLU_INTENT', _('NLU Intent')),
        ('NLU_ENTITIES', _('NLU Entities')),
        ('RECOMMENDATION', _('Recommendation')),
        ('VOICE', _('Voice Processing')),
    ]
    RATINGS = [(i, str(i)) for i in range(1, 6)]  # 1-5 scale

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    feedback_type = models.CharField(
        _("feedback type"),
        max_length=20,
        choices=FEEDBACK_TYPES
    )
    rating = models.PositiveSmallIntegerField(
        _("rating"),
        choices=RATINGS,
        null=True, blank=True
    )
    comment = models.TextField(
        _("comment"),
        blank=True, null=True
    )
    nlu_log = models.ForeignKey(
        NLULog,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='feedback'
    )
    recommendation_log = models.ForeignKey(
        RecommendationLog,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='feedback'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name=_("user")
    )
    created_at = models.DateTimeField(
        _("created at"),
        auto_now_add=True
    )
    processed = models.BooleanField(
        _("processed"),
        default=False,
        help_text=_("Whether feedback has been reviewed")
    )

    class Meta:
        verbose_name = _("AI feedback")
        verbose_name_plural = _("AI feedback entries")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['feedback_type']),
            models.Index(fields=['processed']),
        ]

    def __str__(self):
        return f"Feedback on {self.get_feedback_type_display()} ({self.rating or 'no rating'})"