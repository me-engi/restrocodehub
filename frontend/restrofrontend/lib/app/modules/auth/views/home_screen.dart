import 'package:flutter/material.dart';
import 'package:get/get.dart';
import 'package:restrofrontend/app/data/model/restaurant_model.dart';
import 'package:restrofrontend/app/modules/auth/controllers/login_controller.dart';
// import 'package:cached_network_image/cached_network_image.dart'; // For better image loading

import '../controllers/home_controller.dart';

import '../../../routes/app_pages.dart'; // For logout

class HomeScreen extends GetView<HomeController> {
  const HomeScreen({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    final scrollController = ScrollController();
    scrollController.addListener(() {
      if (scrollController.position.pixels == scrollController.position.maxScrollExtent &&
          !controller.isLoadingRestaurants.value &&
          controller.hasMoreRestaurants.value) {
        controller.fetchNearbyRestaurants(); // Load more on scroll end
      }
    });

    return Scaffold(
      appBar: AppBar(
        title: const Text("Culinary AI Concierge"),
        actions: [
          IconButton(
            icon: const Icon(Icons.logout),
            onPressed: () {
              // Find the login controller to call logout
              // This assumes LoginController is registered globally or accessible.
              // A better way is to have an AuthService.
              if (Get.isRegistered<LoginController>()) {
                 Get.find<LoginController>().logoutUser();
              } else {
                Get.snackbar("Error", "Logout failed. Controller not found.", snackPosition: SnackPosition.BOTTOM);
                // Fallback: Manually clear storage and navigate if controller not found
                // GetStorage storage = GetStorage();
                // storage.erase();
                // Get.offAllNamed(Routes.LOGIN);
              }
            },
          ),
        ],
      ),
      body: Obx(() { // Obx for reactive UI updates
        if (controller.locationError.value != null && controller.restaurants.isEmpty) {
          return Center(
            child: Padding(
              padding: const EdgeInsets.all(16.0),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const Icon(Icons.location_off, size: 60, color: Colors.redAccent),
                  const SizedBox(height: 16),
                  Text(
                    controller.locationError.value!,
                    textAlign: TextAlign.center,
                    style: Get.textTheme.titleMedium,
                  ),
                  const SizedBox(height: 16),
                  ElevatedButton.icon(
                    icon: const Icon(Icons.refresh),
                    label: const Text("Retry Location"),
                    onPressed: controller.refreshRestaurants,
                  )
                ],
              ),
            ),
          );
        }

        if (controller.isLoadingRestaurants.value && controller.restaurants.isEmpty) {
          return const Center(child: CircularProgressIndicator());
        }

        if (controller.restaurants.isEmpty && !controller.isLoadingRestaurants.value) {
          return Center(
            child: Padding(
              padding: const EdgeInsets.all(16.0),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const Icon(Icons.restaurant_menu_outlined, size: 60, color: Colors.grey),
                  const SizedBox(height: 16),
                  Text(
                    "No restaurants found nearby.",
                    style: Get.textTheme.titleMedium,
                  ),
                   const SizedBox(height: 16),
                  ElevatedButton.icon(
                    icon: const Icon(Icons.refresh),
                    label: const Text("Refresh"),
                    onPressed: controller.refreshRestaurants,
                  )
                ],
              ),
            ),
          );
        }

        return RefreshIndicator(
          onRefresh: controller.refreshRestaurants,
          child: ListView.builder(
            controller: scrollController,
            padding: const EdgeInsets.all(8.0),
            itemCount: controller.restaurants.length + (controller.hasMoreRestaurants.value ? 1 : 0),
            itemBuilder: (context, index) {
              if (index == controller.restaurants.length && controller.hasMoreRestaurants.value) {
                return const Padding(
                  padding: EdgeInsets.symmetric(vertical: 16.0),
                  child: Center(child: CircularProgressIndicator()),
                );
              }
              if (index >= controller.restaurants.length) return const SizedBox.shrink(); // Should not happen

              final restaurant = controller.restaurants[index];
              return RestaurantCard(restaurant: restaurant, onTap: () => controller.navigateToRestaurantMenu(restaurant));
            },
          ),
        );
      }),
      floatingActionButton: FloatingActionButton(
        onPressed: controller.toggleChatVisibility,
        tooltip: 'AI Chat',
        child: Obx(() => Icon(controller.isChatVisible.value ? Icons.chat_bubble_rounded : Icons.chat_bubble_outline_rounded)),
      ),
      bottomSheet: Obx(() { // For AI Chat overlay
        if (!controller.isChatVisible.value) return const SizedBox.shrink();
        return _buildChatBottomSheet(context, controller);
      }),
    );
  }

  Widget _buildChatBottomSheet(BuildContext context, HomeController controller) {
    TextEditingController chatInputController = TextEditingController();
    return Container(
      height: MediaQuery.of(context).size.height * 0.5, // Half screen
      padding: const EdgeInsets.all(16.0),
      decoration: BoxDecoration(
        color: Get.theme.cardColor, // Use theme color
        borderRadius: const BorderRadius.only(
          topLeft: Radius.circular(20),
          topRight: Radius.circular(20),
        ),
        boxShadow: [
          BoxShadow(
            color: Colors.grey.withOpacity(0.3),
            spreadRadius: 2,
            blurRadius: 5,
            offset: const Offset(0, -3),
          ),
        ],
      ),
      child: Column(
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text("AI Concierge", style: Get.textTheme.titleLarge),
              IconButton(
                icon: const Icon(Icons.close),
                onPressed: controller.toggleChatVisibility,
              ),
            ],
          ),
          const Divider(),
          Expanded(
            child: Obx(() => ListView.builder(
                  itemCount: controller.chatMessages.length,
                  itemBuilder: (context, index) {
                    final message = controller.chatMessages[index];
                    final isUserMessage = message.startsWith("User:");
                    return Align(
                      alignment: isUserMessage ? Alignment.centerRight : Alignment.centerLeft,
                      child: Container(
                        padding: const EdgeInsets.symmetric(vertical: 8, horizontal: 12),
                        margin: const EdgeInsets.symmetric(vertical: 4),
                        decoration: BoxDecoration(
                          color: isUserMessage ? Get.theme.primaryColor.withOpacity(0.8) : Get.theme.colorScheme.surfaceVariant,
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: Text(
                          message,
                          style: TextStyle(color: isUserMessage ? Colors.white : Get.textTheme.bodyLarge?.color),
                        ),
                      ),
                    );
                  },
                )),
          ),
          Padding(
            padding: const EdgeInsets.only(top: 8.0),
            child: Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: chatInputController,
                    decoration: InputDecoration(
                      hintText: "Ask me anything...",
                      border: OutlineInputBorder(borderRadius: BorderRadius.circular(25)),
                      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 0),
                    ),
                    onSubmitted: (value) {
                      controller.sendChatMessage(value);
                      chatInputController.clear();
                    },
                  ),
                ),
                const SizedBox(width: 8),
                IconButton(
                  icon: const Icon(Icons.send),
                  onPressed: () {
                    controller.sendChatMessage(chatInputController.text);
                    chatInputController.clear();
                  },
                  style: IconButton.styleFrom(
                    backgroundColor: Get.theme.primaryColor,
                    foregroundColor: Colors.white,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}


class RestaurantCard extends StatelessWidget {
  final RestaurantModel restaurant;
  final VoidCallback onTap;

  const RestaurantCard({Key? key, required this.restaurant, required this.onTap}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Card(
      elevation: 2,
      margin: const EdgeInsets.symmetric(vertical: 8.0),
      child: InkWell(
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.all(12.0),
          child: Row(
            children: [
              // Restaurant Logo
              SizedBox(
                width: 80,
                height: 80,
                child: ClipRRect(
                  borderRadius: BorderRadius.circular(8.0),
                  child: restaurant.logoImage != null && restaurant.logoImage!.isNotEmpty
                      ? Image.network( // Use CachedNetworkImage for better performance
                          restaurant.logoImage!,
                          fit: BoxFit.cover,
                          errorBuilder: (context, error, stackTrace) =>
                              const Icon(Icons.restaurant, size: 40, color: Colors.grey),
                          loadingBuilder: (context, child, loadingProgress) {
                            if (loadingProgress == null) return child;
                            return const Center(child: CircularProgressIndicator(strokeWidth: 2,));
                          },
                        )
                      : const Icon(Icons.restaurant, size: 40, color: Colors.grey),
                ),
              ),
              const SizedBox(width: 16),
              // Restaurant Info
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      restaurant.name,
                      style: Get.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                    const SizedBox(height: 4),
                    Text(
                      restaurant.city ?? "Unknown City",
                      style: Get.textTheme.bodySmall,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                    const SizedBox(height: 4),
                    Row(
                      children: [
                        Icon(Icons.location_on_outlined, size: 14, color: Get.theme.hintColor),
                        const SizedBox(width: 4),
                        Text(
                          restaurant.distanceKm != null ? "${restaurant.distanceKm} km away" : "Distance N/A",
                           style: Get.textTheme.bodySmall,
                        ),
                         const SizedBox(width: 8),
                        Icon(
                          restaurant.isOperational ? Icons.circle : Icons.circle_outlined,
                          color: restaurant.isOperational ? Colors.green : Colors.red,
                          size: 10,
                        ),
                        const SizedBox(width: 4),
                        Text(
                          restaurant.isOperational ? "Open" : "Closed",
                          style: Get.textTheme.bodySmall?.copyWith(
                            color: restaurant.isOperational ? Colors.green : Colors.red,
                            fontWeight: FontWeight.bold
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
              const Icon(Icons.chevron_right),
            ],
          ),
        ),
      ),
    );
  }
}