import 'package:flutter/material.dart';
import 'package:get/get.dart';
import 'package:restrofrontend/app/data/model/menu_model.dart';
import 'package:restrofrontend/app/modules/auth/controllers/resturent_menu_controller.dart';
// import 'package:cached_network_image/cached_network_image.dart';



class RestaurantMenuScreen extends GetView<RestaurantMenuController> {
  const RestaurantMenuScreen({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(controller.restaurant.name), // Restaurant name from arguments
        actions: [
          // Cart Icon - TODO: Link to a CartController or CartService
          IconButton(
            icon: Stack(
              children: [
                const Icon(Icons.shopping_cart_outlined),
                // Obx(() => controller.cartItemCount.value > 0
                //     ? Positioned(
                //         right: 0,
                //         child: Container(
                //           padding: EdgeInsets.all(1),
                //           decoration: BoxDecoration(
                //             color: Colors.red,
                //             borderRadius: BorderRadius.circular(6),
                //           ),
                //           constraints: BoxConstraints(minWidth: 12, minHeight: 12),
                //           child: Text(
                //             '${controller.cartItemCount.value}',
                //             style: TextStyle(color: Colors.white, fontSize: 8),
                //             textAlign: TextAlign.center,
                //           ),
                //         ),
                //       )
                //     : SizedBox.shrink()),
              ],
            ),
            onPressed: () {
              // TODO: Get.toNamed(Routes.CART);
              Get.snackbar("Cart", "Navigate to Cart Screen (TODO)", snackPosition: SnackPosition.BOTTOM);
            },
          ),
        ],
      ),
      body: Obx(() {
        if (controller.isLoadingMenu.value) {
          return const Center(child: CircularProgressIndicator());
        }
        if (controller.errorMessage.value != null) {
          return Center(
            child: Padding(
              padding: const EdgeInsets.all(16.0),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const Icon(Icons.error_outline, color: Colors.red, size: 50),
                  const SizedBox(height: 10),
                  Text(controller.errorMessage.value!, textAlign: TextAlign.center),
                  const SizedBox(height: 10),
                  ElevatedButton(onPressed: controller.fetchMenu, child: const Text("Retry"))
                ],
              ),
            )
          );
        }
        if (controller.fullMenu.value == null || controller.fullMenu.value!.categories.isEmpty) {
          return const Center(child: Text("Menu not available or empty."));
        }

        final menu = controller.fullMenu.value!;
        return ListView.builder(
          itemCount: menu.categories.length,
          itemBuilder: (context, categoryIndex) {
            final category = menu.categories[categoryIndex];
            if (!category.items.any((item) => item.effectiveIsAvailable)) { // Skip category if all items unavailable
                 return const SizedBox.shrink();
            }
            return ExpansionTile( // Or just a Column with a header
              title: Text(category.name, style: Get.textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.bold)),
              initiallyExpanded: true, // Or based on some logic
              childrenPadding: const EdgeInsets.symmetric(horizontal: 8.0),
              children: category.items
                  .where((item) => item.effectiveIsAvailable) // Only show available items
                  .map((item) => _buildMenuItemCard(item, controller))
                  .toList(),
            );
          },
        );
      }),
      // AI Chat FAB can be added here as well, similar to HomeScreen
    );
  }

  Widget _buildMenuItemCard(MenuItemModel item, RestaurantMenuController controller) {
    return Card(
      margin: const EdgeInsets.symmetric(vertical: 8.0),
      elevation: 1,
      child: InkWell(
        onTap: () {
          if (item.customizationGroups.isNotEmpty) {
            controller.selectMenuItemForCustomization(item);
          } else {
            // TODO: Direct add to cart for non-customizable items
            // controller.addItemToCart(item, 1, []);
            Get.snackbar("Add to Cart", "${item.name} (Non-customizable) - Add to cart (TODO)", snackPosition: SnackPosition.BOTTOM);
          }
        },
        child: Padding(
          padding: const EdgeInsets.all(12.0),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Item Image
              SizedBox(
                width: 80,
                height: 80,
                child: ClipRRect(
                  borderRadius: BorderRadius.circular(8.0),
                  child: item.imageUrl != null && item.imageUrl!.isNotEmpty
                      ? Image.network( // Use CachedNetworkImage
                          item.imageUrl!,
                          fit: BoxFit.cover,
                           errorBuilder: (context, error, stackTrace) =>
                              const Icon(Icons.fastfood_outlined, size: 40, color: Colors.grey),
                          loadingBuilder: (context, child, loadingProgress) {
                            if (loadingProgress == null) return child;
                            return const Center(child: CircularProgressIndicator(strokeWidth: 2,));
                          },
                        )
                      : const Icon(Icons.fastfood_outlined, size: 40, color: Colors.grey),
                ),
              ),
              const SizedBox(width: 12),
              // Item Info
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      item.name,
                      style: Get.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w600),
                    ),
                    if (item.description != null && item.description!.isNotEmpty)
                      Padding(
                        padding: const EdgeInsets.only(top: 4.0),
                        child: Text(
                          item.description!,
                          style: Get.textTheme.bodySmall,
                          maxLines: 2,
                          overflow: TextOverflow.ellipsis,
                        ),
                      ),
                    const SizedBox(height: 8),
                    Text(
                      "\$${item.basePrice.toStringAsFixed(2)}",
                      style: Get.textTheme.titleSmall?.copyWith(fontWeight: FontWeight.bold, color: Get.theme.primaryColor),
                    ),
                  ],
                ),
              ),
              // Action Button (Customize or Add)
              Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  if (item.customizationGroups.isNotEmpty)
                    const Icon(Icons.tune_outlined, color: Colors.blueAccent) // Customize icon
                  else
                    Icon(Icons.add_shopping_cart_outlined, color: Get.theme.primaryColor), // Direct add icon
                  // Could be a small button too
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}