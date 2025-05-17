// lib/app/data/models/cart_model.dart
// (You already have CartItemDisplaySerializer and CartDetailSerializer, so models would mirror that)

// Re-using MenuItemModel for display within cart if detailed enough
import 'menu_model.dart'; // Assuming MenuItemModel is here

class CartItemModel {
  final String id;
  final String menuItemId; // Reference to the actual MenuItem
  final String menuItemName;
  final String? menuItemImageUrl;
  int quantity;
  final double unitPriceAtAddition;
  final List<OrderItemCustomizationSnapshotModel> selectedCustomizationsSnapshot; // Re-use if defined
  final double lineTotal;

  CartItemModel({
    required this.id,
    required this.menuItemId,
    required this.menuItemName,
    this.menuItemImageUrl,
    required this.quantity,
    required this.unitPriceAtAddition,
    required this.selectedCustomizationsSnapshot,
    required this.lineTotal,
  });

  factory CartItemModel.fromJson(Map<String, dynamic> json) {
    return CartItemModel(
      id: json['id'] as String,
      menuItemId: json['menu_item'] as String, // Assuming menu_item is just the ID here
      menuItemName: json['menu_item_name'] as String,
      menuItemImageUrl: json['menu_item_image_url'] as String?,
      quantity: json['quantity'] as int,
      unitPriceAtAddition: (json['unit_price_at_addition'] as num).toDouble(),
      selectedCustomizationsSnapshot: (json['selected_customizations_snapshot'] as List<dynamic>? ?? [])
          .map((e) => OrderItemCustomizationSnapshotModel.fromJson(e as Map<String, dynamic>))
          .toList(),
      lineTotal: (json['line_total'] as num).toDouble(),
    );
  }
}

class CartModel {
  final String? id;
  final String? userId;
  final String? sessionKey;
  final String? restaurantId;
  final String? restaurantName;
  final String? restaurantSlug;
  final List<CartItemModel> items;
  final double subtotalPrice;
  final int itemCount;
  final DateTime? updatedAt;

  CartModel({
    this.id,
    this.userId,
    this.sessionKey,
    this.restaurantId,
    this.restaurantName,
    this.restaurantSlug,
    required this.items,
    required this.subtotalPrice,
    required this.itemCount,
    this.updatedAt,
  });

  factory CartModel.fromJson(Map<String, dynamic> json) {
    return CartModel(
      id: json['id'] as String?,
      userId: json['user'] as String?,
      sessionKey: json['session_key'] as String?,
      restaurantId: json['restaurant'] as String?,
      restaurantName: json['restaurant_name'] as String?,
      restaurantSlug: json['restaurant_slug'] as String?,
      items: (json['items'] as List<dynamic>? ?? [])
          .map((e) => CartItemModel.fromJson(e as Map<String, dynamic>))
          .toList(),
      subtotalPrice: (json['subtotal_price'] as num?)?.toDouble() ?? 0.0,
      itemCount: json['item_count'] as int? ?? 0,
      updatedAt: json['updated_at'] != null ? DateTime.tryParse(json['updated_at']) : null,
    );
  }
}

// Re-use OrderItemCustomizationSnapshotModel from menu_model.dart or define here
class OrderItemCustomizationSnapshotModel {
  final String groupName;
  final String optionName;
  final double priceAdjustment;

  OrderItemCustomizationSnapshotModel({
    required this.groupName,
    required this.optionName,
    required this.priceAdjustment,
  });

  factory OrderItemCustomizationSnapshotModel.fromJson(Map<String, dynamic> json) {
    return OrderItemCustomizationSnapshotModel(
      groupName: json['group_name'] as String,
      optionName: json['option_name'] as String,
      priceAdjustment: (json['price_adjustment'] as num?)?.toDouble() ?? 0.0,
    );
  }
}