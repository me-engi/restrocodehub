import 'package:flutter/material.dart';
import 'package:get/get.dart';
import 'package:restrofrontend/app/data/model/cart_model.dart';
import 'package:restrofrontend/app/data/model/menu_model.dart';
// For MenuItemModel
import '../../../data/providers/order_repository.dart';

class CartController extends GetxController {
  final OrderRepository _orderRepository = Get.find<OrderRepository>();

  var isLoading = false.obs;
  var cart = Rx<CartModel?>(null);

  @override
  void onInit() {
    super.onInit();
    fetchCartDetails();
  }

  Future<void> fetchCartDetails() async {
    isLoading.value = true;
    final fetchedCart = await _orderRepository.fetchCart();
    if (fetchedCart != null) {
      cart.value = fetchedCart;
    } else {
      // Initialize an empty cart structure or handle error
      cart.value = CartModel(items: [], subtotalPrice: 0.0, itemCount: 0);
    }
    isLoading.value = false;
  }

  Future<void> addItem(MenuItemModel menuItem, int quantity, List<String> selectedOptionIds, String restaurantId) async {
    // Basic validation (more robust in AddToCartRequestSerializer and backend)
    if (cart.value?.restaurantId != null && cart.value?.restaurantId != restaurantId) {
        bool? clearCartConfirmed = await Get.dialog<bool>(
            AlertDialog(
                title: const Text("Different Restaurant"),
                content: const Text("Your cart contains items from a different restaurant. Do you want to clear it and add this item?"),
                actions: [
                    TextButton(onPressed: () => Get.back(result: false), child: const Text("Cancel")),
                    TextButton(onPressed: () => Get.back(result: true), child: const Text("Clear & Add")),
                ],
            ),
        );
        if (clearCartConfirmed == true) {
            await clearCurrentCart(showSnackbar: false);
        } else {
            return; // User cancelled
        }
    }


    isLoading.value = true; // Consider a more granular loading state for item add
    final updatedCart = await _orderRepository.addItemToCart(
      menuItemId: menuItem.id,
      quantity: quantity,
      selectedOptionIds: selectedOptionIds,
      restaurantId: restaurantId, // Pass restaurantId to repo
    );
    if (updatedCart != null) {
      cart.value = updatedCart;
      Get.snackbar("Cart Updated", "${menuItem.name} added to cart.", snackPosition: SnackPosition.BOTTOM);
    } else {
      // Error snackbar usually shown by repository/Dio interceptor
      Get.snackbar("Error", "Could not add item to cart.", snackPosition: SnackPosition.BOTTOM);
    }
    isLoading.value = false;
  }

  Future<void> updateItemQuantity(String cartItemId, int newQuantity) async {
    if (newQuantity <= 0) { // Remove item if quantity is 0 or less
      await removeItem(cartItemId);
      return;
    }
    // Consider an item-specific loading state
    final updatedCart = await _orderRepository.updateCartItemQuantity(cartItemId, newQuantity);
    if (updatedCart != null) {
      cart.value = updatedCart;
    }
  }

  Future<void> removeItem(String cartItemId) async {
    // Consider an item-specific loading state
    final success = await _orderRepository.removeCartItem(cartItemId);
    if (success) {
      // Instead of refetching the whole cart, update it locally or fetch again
      await fetchCartDetails(); // Refetch for simplicity
      Get.snackbar("Cart Updated", "Item removed from cart.", snackPosition: SnackPosition.BOTTOM);
    }
  }

  Future<void> clearCurrentCart({bool showSnackbar = true}) async {
    isLoading.value = true;
    final updatedCart = await _orderRepository.clearCart();
    if (updatedCart != null) {
      cart.value = updatedCart;
      if (showSnackbar) {
        Get.snackbar("Cart Cleared", "All items removed from your cart.", snackPosition: SnackPosition.BOTTOM);
      }
    }
    isLoading.value = false;
  }

  // Helper to get an option ID list from a Map<groupId, optionId>
  List<String> getOptionIdsFromMap(Map<String, String> selectedCustomizationsMap) {
      return selectedCustomizationsMap.values.toList();
  }
}