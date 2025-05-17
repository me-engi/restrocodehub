// lib/app/app_binding.dart
import 'package:dio/dio.dart';
import 'package:get/get.dart';
import 'package:get_storage/get_storage.dart';
import 'package:restrofrontend/app/data/providers/resturant_repository.dart';

import './data/providers/auth_repository.dart';

// Import other global repositories/services as needed
import './shared/constants/api_constants.dart'; // For Dio base URL

class AppBinding extends Bindings {
  @override
  void dependencies() {
    // Global Dio Instance (example)
    Get.put<Dio>(
      Dio(BaseOptions(
        baseUrl: ApiConstants.baseUrl,
        connectTimeout: const Duration(seconds: 15),
        receiveTimeout: const Duration(seconds: 15),
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
      )),
      permanent: true, // Make it permanent so it's not disposed
    );

    // Add global interceptors to the Dio instance once
    final dioInstance = Get.find<Dio>();
    dioInstance.interceptors.add(LogInterceptor(requestBody: true, responseBody: true, responseHeader: false, requestHeader: false));
    dioInstance.interceptors.add(InterceptorsWrapper(
      onRequest: (options, handler) async {
        // Add auth token to headers if available
        final GetStorage storage = GetStorage();
        final token = storage.read('accessToken');
        if (token != null) {
          options.headers['Authorization'] = 'Bearer $token';
        }
        return handler.next(options);
      },
      onError: (DioException e, handler) {
        print("Global Dio Error Interceptor: ${e.message}");
        if (e.response?.statusCode == 401) {
          // Unauthorized - Token might be expired or invalid
          Get.snackbar("Authentication Error", "Your session may have expired. Please log in again.", snackPosition: SnackPosition.BOTTOM);
          // Consider logging out the user and redirecting to login
          // Get.find<LoginController>().logoutUser(); // Or use an AuthService
        } else {
            Get.snackbar(
              "API Error",
              e.response?.data?['error']?.toString() ?? e.response?.data?['detail']?.toString() ?? e.message ?? "An unknown API error occurred.",
              snackPosition: SnackPosition.BOTTOM
            );
        }
        return handler.next(e);
      },
    ));

    // Register Global Repositories (they can now use Get.find<Dio>())
    Get.put<AuthRepository>(AuthRepository(), permanent: true);
    Get.put<RestaurantRepository>(RestaurantRepository(), permanent: true);
    // Get.put<MenuRepository>(MenuRepository(), permanent: true);
    // Get.put<OrderRepository>(OrderRepository(), permanent: true);
    // Get.put<AIChatRepository>(AIChatRepository(), permanent: true);

    // You generally don't put page-specific controllers like LoginController here globally
    // unless they manage very global state (like auth state itself, which LoginController currently does a bit of).
    // An AuthService would be better for managing global auth state.
    // For now, we let LoginController be bound via AuthBinding, and SplashController will decide navigation.
  }
}