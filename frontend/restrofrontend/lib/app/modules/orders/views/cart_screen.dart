import 'package:flutter/material.dart';
import 'package:get/get.dart';
import '../controllers/cart_controller.dart';
import '../../../routes/app_pages.dart';

class CartScreen extends GetView<CartController> {
  const CartScreen({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("Your Cart")),
      body: Obx(() {
        if (controller.isLoading.value && controller.cart.value == null) {
          return const Center(child: CircularProgressIndicator());
        }
        if (controller.cart.value == null || controller.cart.value!.items.isEmpty) {
          return Center(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                const Icon(Icons.remove_shopping_cart_outlined, size: 80, color: Colors.grey),
                const SizedBox(height: 20),
                const Text("Your cart is empty!", style: TextStyle(fontSize: 18)),
                const SizedBox(height: 20),
                ElevatedButton(
                  onPressed: () => Get.offAllNamed(Routes.HOME), // Go back to home to browse
                  child: const Text("Continue Shopping"),
                )
              ],
            ),
          );
        }

        final cart = controller.cart.value!;
        return Column(
          children: [
            if (cart.restaurantName != null)
              Padding(
                padding: const EdgeInsets.all(12.0),
                child: Text("Ordering from: ${cart.restaurantName}", style: Get.textTheme.titleMedium),
              ),
            Expanded(
              child: ListView.builder(
                itemCount: cart.items.length,
                itemBuilder: (context, index) {
                  final item = cart.items[index];
                  return Card(
                    margin: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                    child: ListTile(
                      leading: item.menuItemImageUrl != null
                          ? SizedBox(
                              width: 60, height: 60,
                              child: Image.network(item.menuItemImageUrl!, fit: BoxFit.cover,
                                errorBuilder: (_, __, ___) => const Icon(Icons.fastfood),
                              ))
                          : const Icon(Icons.fastfood, size: 40),
                      title: Text(item.menuItemName),
                      subtitle: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text("Price: \$${item.unitPriceAtAddition.toStringAsFixed(2)}"),
                           if (item.selectedCustomizationsSnapshot.isNotEmpty)
                            Text(
                              item.selectedCustomizationsSnapshot
                                  .map((cs) => "${cs.groupName}: ${cs.optionName} (+\$${cs.priceAdjustment.toStringAsFixed(2)})")
                                  .join(', '),
                              style: Get.textTheme.bodySmall,
                              maxLines: 2,
                              overflow: TextOverflow.ellipsis,
                            ),
                          Text("Total: \$${item.lineTotal.toStringAsFixed(2)}", style: const TextStyle(fontWeight: FontWeight.bold)),
                        ],
                      ),
                      trailing: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          IconButton(
                            icon: const Icon(Icons.remove_circle_outline),
                            onPressed: () => controller.updateItemQuantity(item.id, item.quantity - 1),
                          ),
                          Text(item.quantity.toString()),
                          IconButton(
                            icon: const Icon(Icons.add_circle_outline),
                            onPressed: () => controller.updateItemQuantity(item.id, item.quantity + 1),
                          ),
                          IconButton(
                            icon: const Icon(Icons.delete_outline, color: Colors.red),
                            onPressed: () => controller.removeItem(item.id),
                          ),
                        ],
                      ),
                    ),
                  );
                },
              ),
            ),
            // Order Summary and Checkout Button
            Padding(
              padding: const EdgeInsets.all(16.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                   Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text("Items:", style: Get.textTheme.titleMedium),
                      Text("${cart.itemCount}", style: Get.textTheme.titleMedium),
                    ],
                  ),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text("Subtotal:", style: Get.textTheme.titleLarge?.copyWith(fontWeight: FontWeight.bold)),
                      Text("\$${cart.subtotalPrice.toStringAsFixed(2)}", style: Get.textTheme.titleLarge?.copyWith(fontWeight: FontWeight.bold)),
                    ],
                  ),
                  const SizedBox(height: 20),
                  ElevatedButton(
                    onPressed: cart.items.isEmpty || cart.restaurantId == null
                      ? null // Disable if cart empty or no restaurant
                      : () {
                          Get.toNamed(Routes.CHECKOUT); // Navigate to Checkout screen
                        },
                    child: const Text("Proceed to Checkout"),
                  ),
                   TextButton(
                      onPressed: () => controller.clearCurrentCart(),
                      child: const Text("Clear Cart", style: TextStyle(color: Colors.redAccent)),
                    )
                ],
              ),
            )
          ],
        );
      }),
    );
  }
}