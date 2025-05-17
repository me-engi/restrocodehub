# backend/menu/admin.py
from django.contrib import admin
from .models import MenuCategory, MenuItem, Ingredient, CustomizationGroup, CustomizationOption

class CustomizationOptionInline(admin.TabularInline):
    model = CustomizationOption
    fk_name = 'group'
    extra = 1
    fields = ('name', 'price_adjustment', 'is_default_selected', 'is_available', 'display_order')
    ordering = ('display_order', 'name')

@admin.register(CustomizationGroup)
class CustomizationGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'menu_item_name_display', 'restaurant_name_display', 'min_selection', 'max_selection', 'is_required', 'display_order')
    list_filter = ('menu_item__restaurant', 'menu_item__category', 'is_required')
    search_fields = ('name', 'menu_item__name', 'menu_item__restaurant__name')
    inlines = [CustomizationOptionInline]
    list_select_related = ('menu_item', 'menu_item__restaurant', 'menu_item__category')
    ordering = ('menu_item__restaurant', 'menu_item', 'display_order', 'name')
    fields = ('menu_item', 'name', 'min_selection', 'max_selection', 'is_required', 'display_order')

    def menu_item_name_display(self, obj):
        return obj.menu_item.name
    menu_item_name_display.short_description = 'Menu Item'
    menu_item_name_display.admin_order_field = 'menu_item__name'

    def restaurant_name_display(self, obj):
        return obj.menu_item.restaurant.name
    restaurant_name_display.short_description = 'Restaurant'

class CustomizationGroupInline(admin.TabularInline):
    model = CustomizationGroup
    fk_name = 'menu_item'
    extra = 0 # Add groups explicitly
    show_change_link = True # Link to CustomizationGroupAdmin to manage options
    fields = ('name', 'min_selection', 'max_selection', 'is_required', 'display_order')
    ordering = ('display_order', 'name')


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'category_name_display', 'restaurant_name_display', 'base_price', 'effective_is_available_display', 'display_order')
    list_filter = ('restaurant', 'category', 'is_manually_hidden_by_admin')
    search_fields = ('name', 'description', 'category__name', 'restaurant__name')
    list_editable = ('display_order', 'is_manually_hidden_by_admin') # Careful with list_editable
    readonly_fields = ('id', 'created_at', 'updated_at')
    fieldsets = (
        (None, {'fields': ('id', 'restaurant', 'category', 'name', 'description')}),
        ('Pricing & Availability', {'fields': ('base_price', 'is_manually_hidden_by_admin')}),
        ('Display & Other', {'fields': ('image', 'ingredients_display_text', 'display_order')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )
    inlines = [CustomizationGroupInline]
    list_select_related = ('restaurant', 'category')
    ordering = ('restaurant', 'category__display_order', 'category__name', 'display_order', 'name')

    def category_name_display(self, obj):
        return obj.category.name
    category_name_display.short_description = 'Category'
    category_name_display.admin_order_field = 'category__name'

    def restaurant_name_display(self, obj):
        return obj.restaurant.name
    restaurant_name_display.short_description = 'Restaurant'
    restaurant_name_display.admin_order_field = 'restaurant__name'

    @admin.display(boolean=True, description='Effective Availability')
    def effective_is_available_display(self, obj):
        return obj.effective_is_available # Call the model property
    # effective_is_available_display.admin_order_field = '???' # Hard to sort by property directly

class MenuItemInline(admin.TabularInline):
    model = MenuItem
    fk_name = 'category'
    extra = 1
    fields = ('name', 'base_price', 'is_manually_hidden_by_admin', 'display_order')
    show_change_link = True
    ordering = ('display_order', 'name')


@admin.register(MenuCategory)
class MenuCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'restaurant_name_display', 'is_active', 'display_order', 'item_count')
    list_filter = ('restaurant', 'is_active')
    search_fields = ('name', 'description', 'restaurant__name')
    list_editable = ('display_order', 'is_active')
    readonly_fields = ('id', 'created_at', 'updated_at')
    fields = ('id', 'restaurant', 'name', 'description', 'display_order', 'is_active', 'created_at', 'updated_at')
    inlines = [MenuItemInline]
    list_select_related = ('restaurant',)
    ordering = ('restaurant', 'display_order', 'name')

    def restaurant_name_display(self, obj):
        return obj.restaurant.name
    restaurant_name_display.short_description = 'Restaurant'
    restaurant_name_display.admin_order_field = 'restaurant__name'

    def item_count(self, obj):
        return obj.menu_items.count()
    item_count.short_description = 'No. of Items'


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'tenant_name_display', 'created_at')
    list_filter = ('tenant',) # If tenant-scoped
    search_fields = ('name', 'tenant__name')
    readonly_fields = ('id', 'created_at', 'updated_at')
    fields = ('id', 'tenant', 'name', 'created_at', 'updated_at') # Add other ingredient fields if any
    list_select_related = ('tenant',) # If tenant-scoped

    def tenant_name_display(self, obj):
        return obj.tenant.name if obj.tenant else _("Global/Platform")
    tenant_name_display.short_description = 'Tenant / Scope'

# CustomizationOption is managed inline via CustomizationGroupAdmin
# If you want a separate admin for CustomizationOption:
# @admin.register(CustomizationOption)
# class CustomizationOptionAdmin(admin.ModelAdmin):
#     list_display = ('name', 'group_name_display', 'price_adjustment', 'is_available', 'display_order')
#     # ...