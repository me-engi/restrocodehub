 // For restaurant details if needed

class CustomizationOptionModel {
  final String id;
  final String name;
  final double priceAdjustment;
  final bool isDefaultSelected;
  final bool isAvailable;

  CustomizationOptionModel({
    required this.id,
    required this.name,
    required this.priceAdjustment,
    this.isDefaultSelected = false,
    this.isAvailable = true,
  });

  factory CustomizationOptionModel.fromJson(Map<String, dynamic> json) {
    return CustomizationOptionModel(
      id: json['id'] as String,
      name: json['name'] as String,
      priceAdjustment: (json['price_adjustment'] as num?)?.toDouble() ?? 0.0,
      isDefaultSelected: json['is_default_selected'] as bool? ?? false,
      isAvailable: json['is_available'] as bool? ?? true,
    );
  }
}

class CustomizationGroupModel {
  final String id;
  final String name;
  final int minSelection;
  final int maxSelection;
  final bool isRequired;
  final List<CustomizationOptionModel> options;

  CustomizationGroupModel({
    required this.id,
    required this.name,
    required this.minSelection,
    required this.maxSelection,
    required this.isRequired,
    required this.options,
  });

  factory CustomizationGroupModel.fromJson(Map<String, dynamic> json) {
    return CustomizationGroupModel(
      id: json['id'] as String,
      name: json['name'] as String,
      minSelection: json['min_selection'] as int? ?? 0,
      maxSelection: json['max_selection'] as int? ?? 1,
      isRequired: json['is_required'] as bool? ?? false,
      options: (json['options'] as List<dynamic>? ?? [])
          .map((e) => CustomizationOptionModel.fromJson(e as Map<String, dynamic>))
          .toList(),
    );
  }
}

class MenuItemModel {
  final String id;
  final String name;
  final String? description;
  final double basePrice;
  final String? imageUrl;
  final bool effectiveIsAvailable;
  final String? ingredientsDisplayText;
  final List<CustomizationGroupModel> customizationGroups;

  MenuItemModel({
    required this.id,
    required this.name,
    this.description,
    required this.basePrice,
    this.imageUrl,
    required this.effectiveIsAvailable,
    this.ingredientsDisplayText,
    required this.customizationGroups,
  });

  factory MenuItemModel.fromJson(Map<String, dynamic> json) {
    return MenuItemModel(
      id: json['id'] as String,
      name: json['name'] as String,
      description: json['description'] as String?,
      basePrice: (json['base_price'] as num?)?.toDouble() ?? 0.0,
      imageUrl: json['image'] as String?, // Assuming 'image' key from Django serializer
      effectiveIsAvailable: json['effective_is_available'] as bool? ?? true,
      ingredientsDisplayText: json['ingredients_display_text'] as String?,
      customizationGroups: (json['customization_groups'] as List<dynamic>? ?? [])
          .map((e) => CustomizationGroupModel.fromJson(e as Map<String, dynamic>))
          .toList(),
    );
  }
}

class MenuCategoryModel {
  final String id;
  final String name;
  final String? description;
  final List<MenuItemModel> items;

  MenuCategoryModel({
    required this.id,
    required this.name,
    this.description,
    required this.items,
  });

  factory MenuCategoryModel.fromJson(Map<String, dynamic> json) {
    return MenuCategoryModel(
      id: json['id'] as String,
      name: json['name'] as String,
      description: json['description'] as String?,
      items: (json['menu_items'] as List<dynamic>? ?? []) // Assuming 'menu_items' key from Django serializer
          .map((e) => MenuItemModel.fromJson(e as Map<String, dynamic>))
          .toList(),
    );
  }
}

class FullMenuModel {
  final String restaurantId;
  final String restaurantName;
  final List<MenuCategoryModel> categories;
  // final DateTime? lastUpdatedPos; // Optional

  FullMenuModel({
    required this.restaurantId,
    required this.restaurantName,
    required this.categories,
    // this.lastUpdatedPos,
  });

  factory FullMenuModel.fromJson(Map<String, dynamic> json) {
    return FullMenuModel(
      restaurantId: json['restaurant_id'] as String,
      restaurantName: json['restaurant_name'] as String,
      categories: (json['categories'] as List<dynamic>? ?? [])
          .map((e) => MenuCategoryModel.fromJson(e as Map<String, dynamic>))
          .toList(),
      // lastUpdatedPos: json['last_updated_pos'] != null
      //     ? DateTime.tryParse(json['last_updated_pos'] as String)
      //     : null,
    );
  }
}