import 'package:flutter/material.dart';
import 'package:get/get.dart';
import 'package:restrofrontend/app/data/model/menu_model.dart';
import 'package:restrofrontend/app/data/model/restaurant_model.dart';
import 'package:restrofrontend/app/data/providers/resturant_repository.dart';


// Import cart controller later for "Add to Cart" functionality

class RestaurantMenuController extends GetxController {
  final RestaurantRepository _restaurantRepository = Get.find<RestaurantRepository>();
  // final CartController _cartController = Get.find<CartController>(); // For adding items

  final RestaurantModel restaurant = Get.arguments as RestaurantModel; // Get restaurant passed from Home

  var isLoadingMenu = true.obs;
  var fullMenu = Rx<FullMenuModel?>(null);
  var errorMessage = Rx<String?>(null);

  // For managing selected item and its customizations (if opening a dialog/bottom sheet)
  var selectedMenuItem = Rx<MenuItemModel?>(null);
  var selectedCustomizations = <String, String>{}.obs; // {groupId: optionId}
  var currentItemQuantity = 1.obs;
  var currentCustomizedPrice = 0.0.obs;


  @override
  void onInit() {
    super.onInit();
    fetchMenu();
  }

  Future<void> fetchMenu() async {
    isLoadingMenu.value = true;
    errorMessage.value = null;
    final menuData = await _restaurantRepository.fetchRestaurantMenu(restaurant.id); // Or restaurant.slug
    if (menuData != null) {
      fullMenu.value = menuData;
    } else {
      errorMessage.value = "Failed to load menu. Please try again.";
      Get.snackbar("Menu Error", errorMessage.value!, snackPosition: SnackPosition.BOTTOM);
    }
    isLoadingMenu.value = false;
  }

  void selectMenuItemForCustomization(MenuItemModel item) {
    selectedMenuItem.value = item;
    selectedCustomizations.clear();
    currentItemQuantity.value = 1;
    // Pre-select default options
    for (var group in item.customizationGroups) {
      for (var option in group.options) {
        if (option.isDefaultSelected) {
          selectedCustomizations[group.id] = option.id;
          break; // Assuming only one default per group for single-select
        }
      }
    }
    calculateCustomizedPrice();
    // Typically, you would open a dialog or bottom sheet here to show customization options
    // Get.bottomSheet(_buildCustomizationSheet()); or Get.dialog(...)
    Get.bottomSheet(
      _buildCustomizationBottomSheet(), // You'll define this widget
      isScrollControlled: true, // Allows bottom sheet to take more height
      backgroundColor: Get.theme.cardColor,
       shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
    );
  }

  void updateCustomization(String groupId, String optionId) {
    // Handle single/multi-select logic based on CustomizationGroupModel.maxSelection
    final group = selectedMenuItem.value?.customizationGroups.firstWhere((g) => g.id == groupId);
    if (group != null) {
      if (group.maxSelection == 1) { // Single select
        selectedCustomizations[groupId] = optionId;
      } else { // Multi-select (more complex, needs to manage a list of options for the group)
        // This example simplifies to single select for now.
        // For multi-select, selectedCustomizations might be Map<String, List<String>>
        selectedCustomizations[groupId] = optionId;
      }
    }
    calculateCustomizedPrice();
  }

   void incrementQuantity() {
    currentItemQuantity.value++;
    calculateCustomizedPrice();
  }

  void decrementQuantity() {
    if (currentItemQuantity.value > 1) {
      currentItemQuantity.value--;
      calculateCustomizedPrice();
    }
  }


  void calculateCustomizedPrice() {
    if (selectedMenuItem.value == null) return;
    double price = selectedMenuItem.value!.basePrice;
    selectedCustomizations.forEach((groupId, optionId) {
      final group = selectedMenuItem.value!.customizationGroups.firstWhere((g) => g.id == groupId);
      final option = group.options.firstWhere((o) => o.id == optionId);
      price += option.priceAdjustment;
    });
    currentCustomizedPrice.value = price * currentItemQuantity.value;
  }

  void addItemToCartWithCustomizations() {
    if (selectedMenuItem.value == null) return;

    // Validate min/max selections for each group based on selectedCustomizations
    for (var group in selectedMenuItem.value!.customizationGroups) {
        int currentSelectionsInGroup = 0;
        selectedCustomizations.forEach((gId, oId) {
            if (gId == group.id) {
                // For multi-select, this logic would count options in a list for this group
                currentSelectionsInGroup = 1; // Simplified for single-select
            }
        });

        if (currentSelectionsInGroup < group.minSelection) {
            Get.snackbar("Customization Error", "Please select at least ${group.minSelection} option(s) for '${group.name}'.", snackPosition: SnackPosition.BOTTOM);
            return;
        }
        // max_selection validation already implicitly handled by UI if single-select radio buttons
    }


    // Prepare selected option IDs list for the CartController/Repository
    List<String> finalSelectedOptionIds = selectedCustomizations.values.toList();

    // TODO: Get.find<CartController>().addItemToCart(selectedMenuItem.value!, currentItemQuantity.value, finalSelectedOptionIds, restaurant.id);
    print("Adding to cart: ${selectedMenuItem.value!.name}, Qty: ${currentItemQuantity.value}, Options: $finalSelectedOptionIds, Price: ${currentCustomizedPrice.value}");
    Get.back(); // Close the bottom sheet/dialog
    Get.snackbar(
        "Added to Cart",
        "${currentItemQuantity.value} x ${selectedMenuItem.value!.name} added.",
        snackPosition: SnackPosition.BOTTOM
    );
  }

  // This widget would be part of your menu_screen.dart or a separate component file
  Widget _buildCustomizationBottomSheet() {
    // Use Obx for reactive UI updates within the bottom sheet
    return Obx(() {
      if (selectedMenuItem.value == null) return const SizedBox.shrink();
      final item = selectedMenuItem.value!;
      return Container(
        padding: const EdgeInsets.all(20.0),
        child: SingleChildScrollView( // Important for long customization lists
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(item.name, style: Get.textTheme.headlineSmall),
              if (item.description != null && item.description!.isNotEmpty)
                Padding(
                  padding: const EdgeInsets.symmetric(vertical: 8.0),
                  child: Text(item.description!, style: Get.textTheme.bodyMedium),
                ),
              const Divider(),
              ...item.customizationGroups.map((group) {
                return Padding(
                  padding: const EdgeInsets.symmetric(vertical: 8.0),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(group.name, style: Get.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold)),
                      if (group.minSelection > 0 || group.maxSelection > 0)
                        Text(
                          "(Select ${group.minSelection == group.maxSelection && group.minSelection > 0 ? 'exactly ' : group.minSelection > 0 ? 'at least ' : ''}${group.minSelection > 0 ? group.minSelection : ''}${group.minSelection > 0 && group.maxSelection > 0 && group.maxSelection != group.minSelection ? ' up to ' : ''}${group.maxSelection > 0 && group.maxSelection != group.minSelection ? group.maxSelection : ''}${group.isRequired && group.minSelection == 0 ? ' (Optional)' : group.isRequired ? ' (Required)' : ' (Optional)'})",
                          style: Get.textTheme.bodySmall,
                        ),
                      ...group.options.where((opt) => opt.isAvailable).map((option) { // Filter available options
                        return RadioListTile<String>( // Example for single-select group
                          title: Text(option.name),
                          subtitle: Text(option.priceAdjustment != 0
                              ? "${option.priceAdjustment > 0 ? '+' : ''}\$${option.priceAdjustment.toStringAsFixed(2)}"
                              : "Included"),
                          value: option.id,
                          groupValue: selectedCustomizations[group.id],
                          onChanged: (String? value) {
                            if (value != null) {
                              updateCustomization(group.id, value);
                            }
                          },
                          activeColor: Get.theme.primaryColor,
                        );
                        // For multi-select groups, use CheckboxListTile
                      }),
                      const Divider(height: 10, thickness: 0.5),
                    ],
                  ),
                );
              }).toList(),
              const SizedBox(height: 16),
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Row(
                    children: [
                      IconButton(icon: const Icon(Icons.remove_circle_outline), onPressed: decrementQuantity),
                      Obx(() => Text(currentItemQuantity.value.toString(), style: Get.textTheme.titleLarge)),
                      IconButton(icon: const Icon(Icons.add_circle_outline), onPressed: incrementQuantity),
                    ],
                  ),
                  Obx(() => Text(
                    "Total: \$${currentCustomizedPrice.value.toStringAsFixed(2)}",
                    style: Get.textTheme.titleLarge?.copyWith(fontWeight: FontWeight.bold),
                  )),
                ],
              ),
              const SizedBox(height: 20),
              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  onPressed: addItemToCartWithCustomizations,
                  style: ElevatedButton.styleFrom(padding: const EdgeInsets.symmetric(vertical: 15)),
                  child: const Text("Add to Cart"),
                ),
              ),
            ],
          ),
        ),
      );
    });
  }

}