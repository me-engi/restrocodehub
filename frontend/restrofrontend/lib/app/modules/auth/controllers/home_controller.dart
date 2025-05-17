import 'package:get/get.dart';
import 'package:geolocator/geolocator.dart'; // For location
import 'package:restrofrontend/app/data/model/restaurant_model.dart';
import 'package:restrofrontend/app/data/providers/resturant_repository.dart';
import 'package:restrofrontend/app/modules/auth/controllers/login_controller.dart';


import '../../../routes/app_pages.dart';
// import '../../auth/controllers/login_controller.dart'; // For logout or user info

// lib/app/modules/home/controllers/home_controller.dart

// import '../../auth/controllers/login_controller.dart'; // For logout or user info

class HomeController extends GetxController {
  final RestaurantRepository _restaurantRepository = Get.find<RestaurantRepository>();
  // final LoginController _loginController = Get.find<LoginController>(); // If needed

  var isLoadingRestaurants = false.obs;
  var restaurants = <RestaurantModel>[].obs;
  var currentPosition = Rx<Position?>(null);
  var locationError = Rx<String?>(null);
  var currentRestaurantPage = 1.obs;
  var totalRestaurantCount = 0.obs;
  var hasMoreRestaurants = true.obs;

  // AI Chat related observables (example)
  var isChatVisible = false.obs;
  var chatMessages = <String>[].obs; // Simple list for now

  @override
  void onInit() {
    super.onInit();
    _determinePositionAndFetch();
  }

  Future<void> _determinePositionAndFetch() async { // Made this async to be awaitable
    isLoadingRestaurants.value = true;
    locationError.value = null;
    bool serviceEnabled;
    LocationPermission permission;

    // ... (rest of your location checking logic remains the same) ...
    serviceEnabled = await Geolocator.isLocationServiceEnabled();
    if (!serviceEnabled) {
      locationError.value = 'Location services are disabled.';
      Get.snackbar("Location Error", locationError.value!, snackPosition: SnackPosition.BOTTOM);
      isLoadingRestaurants.value = false;
      return; // Return here as it's an async function
    }

    permission = await Geolocator.checkPermission();
    if (permission == LocationPermission.denied) {
      permission = await Geolocator.requestPermission();
      if (permission == LocationPermission.denied) {
        locationError.value = 'Location permissions are denied';
        Get.snackbar("Location Error", locationError.value!, snackPosition: SnackPosition.BOTTOM);
        isLoadingRestaurants.value = false;
        return;
      }
    }

    if (permission == LocationPermission.deniedForever) {
      locationError.value = 'Location permissions are permanently denied, we cannot request permissions.';
      Get.snackbar("Location Error", locationError.value!, snackPosition: SnackPosition.BOTTOM);
      isLoadingRestaurants.value = false;
      return;
    }

    try {
      currentPosition.value = await Geolocator.getCurrentPosition(
        desiredAccuracy: LocationAccuracy.medium
      );
      if (currentPosition.value != null) {
        // Await the fetch operation
        await fetchNearbyRestaurants(isRefresh: true);
      } else {
        locationError.value = "Could not get current location.";
        Get.snackbar("Location Error", locationError.value!, snackPosition: SnackPosition.BOTTOM);
      }
    } catch (e) {
      locationError.value = "Error getting location: ${e.toString()}";
      Get.snackbar("Location Error", locationError.value!, snackPosition: SnackPosition.BOTTOM);
    } finally {
      // isLoadingRestaurants will be set to false within fetchNearbyRestaurants
      // or if an error occurred before calling it.
      if (restaurants.isEmpty && currentPosition.value == null) {
          isLoadingRestaurants.value = false; // Ensure it's false if fetch wasn't called
      }
    }
  }

  Future<void> fetchNearbyRestaurants({bool isRefresh = false}) async { // Already async
    if (currentPosition.value == null) {
      if (!isLoadingRestaurants.value) { // Only show if not already loading due to location attempt
        locationError.value = "Location not available to fetch restaurants.";
        Get.snackbar("Info", locationError.value!, snackPosition: SnackPosition.BOTTOM);
      }
      isLoadingRestaurants.value = false; // Ensure loading stops
      return;
    }
    if (isLoadingRestaurants.value && !isRefresh && restaurants.isNotEmpty) return;

    isLoadingRestaurants.value = true;
    if (isRefresh) {
      currentRestaurantPage.value = 1;
      restaurants.clear();
      hasMoreRestaurants.value = true;
    }

    if (!hasMoreRestaurants.value && !isRefresh) {
      isLoadingRestaurants.value = false;
      return;
    }

    final response = await _restaurantRepository.fetchNearbyRestaurants(
      latitude: currentPosition.value!.latitude,
      longitude: currentPosition.value!.longitude,
      page: currentRestaurantPage.value,
    );

    if (response != null) {
      restaurants.addAll(response.results);
      totalRestaurantCount.value = response.count;
      if (response.next == null || response.results.isEmpty) {
        hasMoreRestaurants.value = false;
      } else {
        currentRestaurantPage.value++;
      }
    } else {
      hasMoreRestaurants.value = false;
    }
    isLoadingRestaurants.value = false;
  }

  // Corrected refreshRestaurants
  Future<void> refreshRestaurants() async {
    // Simply call _determinePositionAndFetch which is already async and handles loading states.
    // It will internally call fetchNearbyRestaurants with isRefresh: true.
    await _determinePositionAndFetch();
  }

  void navigateToRestaurantMenu(RestaurantModel restaurant) {
    // Ensure Routes.RESTAURANT_MENU is defined in your app_pages.dart
    Get.toNamed(Routes.RESTAURANT_MENU, arguments: restaurant);
  }

  void toggleChatVisibility() {
    isChatVisible.value = !isChatVisible.value;
  }

  void sendChatMessage(String message) {
    if (message.trim().isEmpty) return;
    chatMessages.add("User: $message");
    // TODO: Call AI Chat Repository/Service
    // Simulate AI response
    Future.delayed(const Duration(seconds: 1), () {
      chatMessages.add("AI: I understood '$message'. I'm still learning!");
    });
  }

  // Example logout, assuming LoginController is globally available via Get.find()
  // A dedicated AuthService is often better for managing auth state.
  void logout() {
    if (Get.isRegistered<LoginController>()) {
      Get.find<LoginController>().logoutUser();
    } else {
      // Fallback or error handling if LoginController isn't found
      // This might happen if the app structure changes or bindings aren't set up for it to be global.
      // A more robust solution is an AuthService.
      print("Error: LoginController not found for logout.");
      Get.snackbar("Logout Error", "Could not perform logout action.", snackPosition: SnackPosition.BOTTOM);
    }
  }
}