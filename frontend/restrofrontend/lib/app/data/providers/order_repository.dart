import 'package:dio/dio.dart';
import 'package:get/get.dart';
import 'package:restrofrontend/app/data/model/cart_model.dart';
import 'package:restrofrontend/app/data/model/order_model.dart';

import '../../shared/constants/api_constants.dart';
 // You'll create this

class OrderRepository {
  final Dio _dio = Get.find<Dio>(); // Uses globally registered Dio instance

  // --- Cart Methods ---
  Future<CartModel?> fetchCart() async {
    try {
      final response = await _dio.get(ApiConstants.cartDetailEndpoint);
      if (response.statusCode == 200 && response.data != null) {
        return CartModel.fromJson(response.data as Map<String, dynamic>);
      }
    } catch (e) {
      print("Error fetching cart: $e");
      // Snackbar handled by global Dio interceptor
    }
    return null;
  }

  Future<CartModel?> addItemToCart({
    required String menuItemId,
    required int quantity,
    required List<String> selectedOptionIds,
    required String restaurantId,
  }) async {
    try {
      final response = await _dio.post(
        ApiConstants.cartAddItemEndpoint,
        data: {
          'menu_item_id': menuItemId,
          'quantity': quantity,
          'selected_option_ids': selectedOptionIds,
          'restaurant_id': restaurantId,
        },
      );
      if (response.statusCode == 200 || response.statusCode == 201 && response.data != null) { // 200 if updated, 201 if new cart_item
        return CartModel.fromJson(response.data as Map<String, dynamic>);
      }
    } catch (e) {
      print("Error adding item to cart: $e");
    }
    return null;
  }

  Future<CartModel?> updateCartItemQuantity(String cartItemId, int quantity) async {
    try {
      final response = await _dio.patch( // Or PUT
        ApiConstants.cartUpdateItemEndpoint(cartItemId),
        data: {'quantity': quantity},
      );
      if (response.statusCode == 200 && response.data != null) {
        return CartModel.fromJson(response.data as Map<String, dynamic>);
      }
    } catch (e) {
      print("Error updating cart item quantity: $e");
    }
    return null;
  }

  Future<bool> removeCartItem(String cartItemId) async {
    try {
      final response = await _dio.delete(ApiConstants.cartRemoveItemEndpoint(cartItemId));
      return response.statusCode == 204; // Or 200 with updated cart
    } catch (e) {
      print("Error removing cart item: $e");
      return false;
    }
  }

  Future<CartModel?> clearCart() async {
    try {
      final response = await _dio.post(ApiConstants.cartDetailEndpoint + "clear/"); // Assuming POST for clear
      // Or DELETE on ApiConstants.cartDetailEndpoint
      if (response.statusCode == 200 && response.data != null) {
        return CartModel.fromJson(response.data as Map<String, dynamic>);
      }
    } catch (e) {
      print("Error clearing cart: $e");
    }
    return null;
  }

  // --- Order Methods ---
  Future<OrderDetailModel?> placeOrder(Map<String, dynamic> orderData) async {
    try {
      final response = await _dio.post(
        ApiConstants.placeOrderEndpoint,
        data: orderData,
      );
      if (response.statusCode == 201 && response.data != null) {
        return OrderDetailModel.fromJson(response.data as Map<String, dynamic>);
      }
    } on DioException catch (e) {
       if (e.response?.data != null && e.response!.data is Map) {
        String errorMessage = "Order placement failed.";
        (e.response!.data as Map).forEach((key, value) {
          if (value is List && value.isNotEmpty) {
            errorMessage = value.first;
          } else if (value is String) {
            errorMessage = value;
          }
        });
         Get.snackbar("Order Error", errorMessage, snackPosition: SnackPosition.BOTTOM);
      } else {
        Get.snackbar("Order Error", e.message ?? "Could not place order.", snackPosition: SnackPosition.BOTTOM);
      }
    } catch (e) {
      print("Error placing order: $e");
       Get.snackbar("Order Error", "An unexpected error occurred.", snackPosition: SnackPosition.BOTTOM);
    }
    return null;
  }

  Future<PaginatedOrdersResponse?> fetchOrderHistory({int page = 1}) async {
    try {
      final response = await _dio.get(
        ApiConstants.myOrderHistoryEndpoint,
        queryParameters: {'page': page},
      );
      if (response.statusCode == 200 && response.data != null) {
        return PaginatedOrdersResponse.fromJson(response.data as Map<String, dynamic>);
      }
    } catch (e) {
      print("Error fetching order history: $e");
    }
    return null;
  }

  Future<OrderDetailModel?> fetchOrderDetail(String orderId) async {
    try {
      final response = await _dio.get(ApiConstants.orderDetailEndpoint(orderId));
      if (response.statusCode == 200 && response.data != null) {
        return OrderDetailModel.fromJson(response.data as Map<String, dynamic>);
      }
    } catch (e) {
      print("Error fetching order detail for $orderId: $e");
    }
    return null;
  }

   Future<OrderDetailModel?> cancelMyOrder(String orderId, String reason) async {
    try {
      final response = await _dio.post(
        ApiConstants.cancelMyOrderEndpoint(orderId),
        data: {'reason': reason},
      );
      if (response.statusCode == 200 && response.data != null) {
        return OrderDetailModel.fromJson(response.data as Map<String, dynamic>);
      }
    } catch (e) {
      print("Error cancelling order $orderId: $e");
    }
    return null;
  }
}