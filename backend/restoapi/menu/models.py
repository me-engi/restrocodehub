# backend/menu/models.py
from django.db import models
from django.utils.translation import gettext_lazy as _
import uuid

# Import Restaurant model from the 'restaurants' app
from restaurants.models import Restaurant # Assuming restaurants.models.Restaurant

class MenuCategory(models.Model):
    """
    Represents a category within a restaurant's menu (e.g., Appetizers, Main Courses, Desserts).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    restaurant = models.ForeignKey(
        Restaurant,
        on_delete=models.CASCADE,
        related_name='menu_categories',
        verbose_name=_("restaurant")
    )
    name = models.CharField(_("category name"), max_length=100)
    description = models.TextField(_("description"), blank=True, null=True)
    display_order = models.PositiveIntegerField(
        _("display order"), default=0, db_index=True,
        help_text=_("Order in which categories appear on the menu (lower numbers first).")
    )
    is_active = models.BooleanField(
        _("is active"), default=True,
        help_text=_("Is this category currently visible on the menu?")
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("menu category")
        verbose_name_plural = _("menu categories")
        ordering = ['restaurant', 'display_order', 'name']
        unique_together = [['restaurant', 'name']] # Category name unique within a restaurant

    def __str__(self):
        return f"{self.name} ({self.restaurant.name})"


class Ingredient(models.Model):
    """
    Represents a raw ingredient. Can be managed centrally or per tenant/restaurant.
    For simplicity, let's make it per Tenant, as ingredient naming and units might vary.
    If ingredients are globally managed by platform admins, remove tenant FK.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey( # Optional: if ingredients are managed per tenant
        'users.Tenant', # String reference to users.Tenant
        on_delete=models.CASCADE,
        related_name='ingredients',
        verbose_name=_("tenant"),
        null=True, blank=True, # Make nullable if ingredients can be global/platform-managed
        help_text=_("Tenant who owns/manages this ingredient definition, if not global.")
    )
    name = models.CharField(_("ingredient name"), max_length=150, db_index=True)
    # unit_of_measure = models.CharField(_("unit"), max_length=50, blank=True, null=True, help_text=_("e.g., kg, g, piece, liter, ml"))
    # is_allergen = models.BooleanField(_("is allergen"), default=False)
    # allergen_description = models.TextField(_("allergen description"), blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("ingredient")
        verbose_name_plural = _("ingredients")
        ordering = ['name']
        unique_together = [['tenant', 'name']] # Ingredient name unique within a tenant (if tenant-scoped)
                                             # Or just unique=True on name if global

    def __str__(self):
        if self.tenant:
            return f"{self.name} ({self.tenant.name})"
        return self.name


class MenuItem(models.Model):
    """
    Represents an individual item on a restaurant's menu.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    restaurant = models.ForeignKey(
        Restaurant,
        on_delete=models.CASCADE,
        related_name='menu_items',
        verbose_name=_("restaurant")
    )
    category = models.ForeignKey(
        MenuCategory,
        on_delete=models.CASCADE, # Or SET_NULL if item can exist without category
        related_name='menu_items',
        verbose_name=_("category")
    )
    name = models.CharField(_("item name"), max_length=200, db_index=True)
    description = models.TextField(_("description"), blank=True, null=True)
    base_price = models.DecimalField(_("base price"), max_digits=10, decimal_places=2)
    image = models.ImageField(_("item image"), upload_to='menu_items/', blank=True, null=True)

    # Availability: This is a complex topic.
    # is_available_from_pos: BooleanField updated by POS sync, reflecting actual stock. (Not directly on this model, but used to derive effective_is_available)
    # is_manually_hidden: BooleanField for tenant admin to temporarily hide an item regardless of POS stock.
    is_manually_hidden_by_admin = models.BooleanField(
        _("manually hidden by admin"), default=False,
        help_text=_("Allows admin to temporarily hide item from menu, overrides POS availability.")
    )
    # effective_is_available: Property method or derived field that considers both POS stock and manual override.

    # For display & AI understanding. Detailed stock deductions happen via POS integration.
    # This could be a simple text field or a ManyToMany to an Ingredient model.
    ingredients_display_text = models.TextField(
        _("ingredients display text"), blank=True, null=True,
        help_text=_("Comma-separated list of main ingredients for display purposes.")
    )
    # For more structured ingredient mapping:
    # ingredients = models.ManyToManyField(Ingredient, through='MenuItemIngredientLink', blank=True)

    # Could add fields like: calories, dietary_tags ( Vegetarian, Vegan, Gluten-Free - ManyToMany to a Tag model)
    # preparation_time_minutes = models.PositiveSmallIntegerField(null=True, blank=True)

    display_order = models.PositiveIntegerField(
        _("display order"), default=0, db_index=True,
        help_text=_("Order within its category (lower numbers first).")
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("menu item")
        verbose_name_plural = _("menu items")
        ordering = ['restaurant', 'category', 'display_order', 'name']
        unique_together = [['restaurant', 'category', 'name']]

    def __str__(self):
        return f"{self.name} ({self.category.name} - {self.restaurant.name})"

    @property
    def effective_is_available(self):
        """
        Determines if the item should be shown as available to customers.
        This needs real-time input from POS inventory. For now, a placeholder.
        """
        if self.is_manually_hidden_by_admin:
            return False
        # In a real system:
        # from pos_integration.services import get_item_availability_from_pos
        # return get_item_availability_from_pos(self.restaurant.id, self.id_from_pos_or_sku)
        return True # Placeholder: Assume available unless manually hidden


class CustomizationGroup(models.Model):
    """
    A group of customization options for a MenuItem (e.g., "Choose Your Size", "Add Toppings", "Select Sauce").
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    menu_item = models.ForeignKey(
        MenuItem,
        on_delete=models.CASCADE,
        related_name='customization_groups',
        verbose_name=_("menu item")
    )
    name = models.CharField(_("group name"), max_length=100, help_text=_("e.g., Size, Toppings, Sauce Choice"))
    # min_selection/max_selection: e.g., for "Choose 2 Toppings", min=2, max=2. For "Add extra toppings", min=0, max=5.
    min_selection = models.PositiveSmallIntegerField(_("minimum selections"), default=0)
    max_selection = models.PositiveSmallIntegerField(_("maximum selections"), default=1, help_text=_("Set to 0 for unlimited (within reason)."))
    display_order = models.PositiveIntegerField(_("display order"), default=0)
    is_required = models.BooleanField(_("is required"), default=False, help_text=_("Must the user make a selection from this group?"))

    class Meta:
        verbose_name = _("customization group")
        verbose_name_plural = _("customization groups")
        ordering = ['menu_item', 'display_order', 'name']
        unique_together = [['menu_item', 'name']]

    def __str__(self):
        return f"{self.name} (for {self.menu_item.name})"


class CustomizationOption(models.Model):
    """
    A specific option within a CustomizationGroup (e.g., "Small", "Medium", "Pepperoni", "Ranch Dressing").
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    group = models.ForeignKey(
        CustomizationGroup,
        on_delete=models.CASCADE,
        related_name='options',
        verbose_name=_("customization group")
    )
    name = models.CharField(_("option name"), max_length=100)
    price_adjustment = models.DecimalField(
        _("price adjustment"), max_digits=8, decimal_places=2, default=0.00,
        help_text=_("Amount to add (or subtract if negative) to the menu item's base price.")
    )
    # For inventory linking if an option adds/removes specific stockable ingredients
    # ingredient_impact = models.ManyToManyField(Ingredient, through='OptionIngredientImpact', blank=True)
    is_default_selected = models.BooleanField(_("is default selected"), default=False)
    is_available = models.BooleanField(_("is available"), default=True) # Option specific availability
    display_order = models.PositiveIntegerField(_("display order"), default=0)

    class Meta:
        verbose_name = _("customization option")
        verbose_name_plural = _("customization options")
        ordering = ['group', 'display_order', 'name']
        unique_together = [['group', 'name']]

    def __str__(self):
        return f"{self.name} (+{self.price_adjustment})"