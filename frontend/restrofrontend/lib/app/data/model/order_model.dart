// lib/app/data/models/order_model.dart
import 'cart_model.dart'; // For OrderItemCustomizationSnapshotModel if re-used

class OrderItemModel {
  final String id;
  final String menuItemSnapshotName;
  final String? originalMenuItemIdStr;
  final int quantity;
  final double unitPrice;
  final List<OrderItemCustomizationSnapshotModel> selectedCustomizationsSnapshot;
  final String? itemNotes;
  final double lineTotal;

  OrderItemModel({
    required this.id,
    required this.menuItemSnapshotName,
    this.originalMenuItemIdStr,
    required this.quantity,
    required this.unitPrice,
    required this.selectedCustomizationsSnapshot,
    this.itemNotes,
    required this.lineTotal,
  });

  factory OrderItemModel.fromJson(Map<String, dynamic> json) {
    return OrderItemModel(
      id: json['id'] as String,
      menuItemSnapshotName: json['menu_item_snapshot_name'] as String,
      originalMenuItemIdStr: json['original_menu_item_id_str'] as String?,
      quantity: json['quantity'] as int,
      unitPrice: (json['unit_price'] as num).toDouble(),
      selectedCustomizationsSnapshot:
          (json['selected_customizations_snapshot'] as List<dynamic>? ?? [])
              .map((e) => OrderItemCustomizationSnapshotModel.fromJson(e as Map<String, dynamic>))
              .toList(),
      itemNotes: json['item_notes'] as String?,
      lineTotal: (json['line_total'] as num).toDouble(),
    );
  }
}

class OrderStatusHistoryModel {
  final String status;
  final String statusDisplay;
  final DateTime timestamp;
  final String? changedByEmail;
  final String? notes;

  OrderStatusHistoryModel({
    required this.status,
    required this.statusDisplay,
    required this.timestamp,
    this.changedByEmail,
    this.notes,
  });

  factory OrderStatusHistoryModel.fromJson(Map<String, dynamic> json) {
    return OrderStatusHistoryModel(
      status: json['status'] as String,
      statusDisplay: json['status_display'] as String,
      timestamp: DateTime.parse(json['timestamp'] as String),
      changedByEmail: json['changed_by_email'] as String?,
      notes: json['notes'] as String?,
    );
  }
}

class OrderListModel { // For displaying in a list
  final String id;
  final String orderNumber;
  final String? userEmail;
  final String restaurantName;
  final String status;
  final String statusDisplay;
  final String orderType;
  final String orderTypeDisplay;
  final double totalPrice;
  final DateTime createdAt;

  OrderListModel({
    required this.id,
    required this.orderNumber,
    this.userEmail,
    required this.restaurantName,
    required this.status,
    required this.statusDisplay,
    required this.orderType,
    required this.orderTypeDisplay,
    required this.totalPrice,
    required this.createdAt,
  });

   factory OrderListModel.fromJson(Map<String, dynamic> json) {
    return OrderListModel(
      id: json['id'] as String,
      orderNumber: json['order_number'] as String,
      userEmail: json['user_email'] as String?,
      restaurantName: json['restaurant_name'] as String,
      status: json['status'] as String,
      statusDisplay: json['status_display'] as String,
      orderType: json['order_type'] as String,
      orderTypeDisplay: json['order_type_display'] as String,
      totalPrice: (json['total_price'] as num).toDouble(),
      createdAt: DateTime.parse(json['created_at'] as String),
    );
  }
}

class OrderDetailModel extends OrderListModel {
  final String? tenantName;
  final String? customerNameSnapshot;
  final String? customerPhoneSnapshot;
  final String? customerEmailSnapshot;
  final String? tableNumber;
  final String? deliveryAddressLine1;
  // ... (all other delivery fields)
  final double subtotalPrice;
  final double taxesAmount;
  final double deliveryFeeAmount;
  final double serviceChargeAmount;
  final double discountAmount;
  final String paymentStatus;
  final String paymentStatusDisplay;
  final String? paymentMethodSnapshot;
  final String? specialInstructionsForRestaurant;
  final DateTime? estimatedDeliveryOrPickupTime;
  // ... (all other timestamp fields: confirmed_at, etc.)
  final List<OrderItemModel> items;
  final List<OrderStatusHistoryModel> statusHistory;

  OrderDetailModel({
    required super.id,
    required super.orderNumber,
    super.userEmail,
    required super.restaurantName,
    required super.status,
    required super.statusDisplay,
    required super.orderType,
    required super.orderTypeDisplay,
    required super.totalPrice,
    required super.createdAt,
    this.tenantName,
    this.customerNameSnapshot,
    this.customerPhoneSnapshot,
    this.customerEmailSnapshot,
    this.tableNumber,
    this.deliveryAddressLine1,
    // ...
    required this.subtotalPrice,
    required this.taxesAmount,
    required this.deliveryFeeAmount,
    required this.serviceChargeAmount,
    required this.discountAmount,
    required this.paymentStatus,
    required this.paymentStatusDisplay,
    this.paymentMethodSnapshot,
    this.specialInstructionsForRestaurant,
    this.estimatedDeliveryOrPickupTime,
    // ...
    required this.items,
    required this.statusHistory,
  });

  factory OrderDetailModel.fromJson(Map<String, dynamic> json) {
    return OrderDetailModel(
      id: json['id'] as String,
      orderNumber: json['order_number'] as String,
      userEmail: json['user_email'] as String?,
      restaurantName: json['restaurant_name'] as String,
      status: json['status'] as String,
      statusDisplay: json['status_display'] as String,
      orderType: json['order_type'] as String,
      orderTypeDisplay: json['order_type_display'] as String,
      totalPrice: (json['total_price'] as num).toDouble(),
      createdAt: DateTime.parse(json['created_at'] as String),
      tenantName: json['tenant_name'] as String?,
      customerNameSnapshot: json['customer_name_snapshot'] as String?,
      customerPhoneSnapshot: json['customer_phone_snapshot'] as String?,
      customerEmailSnapshot: json['customer_email_snapshot'] as String?,
      tableNumber: json['table_number'] as String?,
      deliveryAddressLine1: json['delivery_address_line1'] as String?,
      // ... map all other fields ...
      subtotalPrice: (json['subtotal_price'] as num).toDouble(),
      taxesAmount: (json['taxes_amount'] as num?)?.toDouble() ?? 0.0,
      deliveryFeeAmount: (json['delivery_fee_amount'] as num?)?.toDouble() ?? 0.0,
      serviceChargeAmount: (json['service_charge_amount'] as num?)?.toDouble() ?? 0.0,
      discountAmount: (json['discount_amount'] as num?)?.toDouble() ?? 0.0,
      paymentStatus: json['payment_status'] as String,
      paymentStatusDisplay: json['payment_status_display'] as String,
      paymentMethodSnapshot: json['payment_method_snapshot'] as String?,
      specialInstructionsForRestaurant: json['special_instructions_for_restaurant'] as String?,
      estimatedDeliveryOrPickupTime: json['estimated_delivery_or_pickup_time'] != null
          ? DateTime.tryParse(json['estimated_delivery_or_pickup_time'] as String)
          : null,
      // ... map other timestamp fields ...
      items: (json['items'] as List<dynamic>? ?? [])
          .map((e) => OrderItemModel.fromJson(e as Map<String, dynamic>))
          .toList(),
      statusHistory: (json['status_history'] as List<dynamic>? ?? [])
          .map((e) => OrderStatusHistoryModel.fromJson(e as Map<String, dynamic>))
          .toList(),
    );
  }
}

class PaginatedOrdersResponse {
  final int count;
  final String? next;
  final String? previous;
  final List<OrderListModel> results;

  PaginatedOrdersResponse({
    required this.count,
    this.next,
    this.previous,
    required this.results,
  });

  factory PaginatedOrdersResponse.fromJson(Map<String, dynamic> json) {
    return PaginatedOrdersResponse(
      count: json['count'] as int,
      next: json['next'] as String?,
      previous: json['previous'] as String?,
      results: (json['results'] as List<dynamic>)
          .map((e) => OrderListModel.fromJson(e as Map<String, dynamic>))
          .toList(),
    );
  }
}