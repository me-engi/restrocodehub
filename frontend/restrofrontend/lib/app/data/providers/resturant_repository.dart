import 'package:dio/dio.dart';
import 'package:get/get.dart';
import 'package:restrofrontend/app/data/model/menu_model.dart';
import 'package:restrofrontend/app/data/model/restaurant_model.dart';

import '../../shared/constants/api_constants.dart';

// Import menu model later

class RestaurantRepository {
  late Dio _dio;

  RestaurantRepository() {
    // Use a globally registered Dio instance or initialize one
    // For simplicity, initializing one here. In a larger app, use Get.find<Dio>()
    _dio = Dio(BaseOptions(
      baseUrl: ApiConstants.baseUrl,
      connectTimeout: const Duration(seconds: 10),
      receiveTimeout: const Duration(seconds: 10),
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
    ));
    _dio.interceptors.add(LogInterceptor(requestBody: true, responseBody: true));
     _dio.interceptors.add(InterceptorsWrapper(
      onError: (DioException e, handler) {
        Get.snackbar("API Error", e.message ?? "An error occurred", snackPosition: SnackPosition.BOTTOM);
        return handler.next(e);
      },
    ));
    // Add auth interceptor if needed for these endpoints later
  }

  Future<PaginatedRestaurantsResponse?> fetchNearbyRestaurants({
    required double latitude,
    required double longitude,
    double radius = 5.0, // km
    int page = 1,
  }) async {
    try {
      final response = await _dio.get(
        ApiConstants.nearbyRestaurantsEndpoint,
        queryParameters: {
          'lat': latitude,
          'lon': longitude,
          'radius': radius,
          'page': page,
        },
      );
      if (response.statusCode == 200 && response.data != null) {
        return PaginatedRestaurantsResponse.fromJson(response.data as Map<String, dynamic>);
      }
    } on DioException catch (e) {
      print("Error fetching nearby restaurants: ${e.message}");
      // Error already shown by interceptor
    } catch (e) {
      print("Unexpected error fetching nearby restaurants: $e");
       Get.snackbar("Error", "Could not fetch restaurants.", snackPosition: SnackPosition.BOTTOM);
    }
    return null;
  }

    Future<FullMenuModel?> fetchRestaurantMenu(String restaurantIdOrSlug) async {
    try {
      // The endpoint already includes the restaurant ID/slug
      final response = await _dio.get(ApiConstants.restaurantMenuEndpoint(restaurantIdOrSlug));
      if (response.statusCode == 200 && response.data != null) {
        return FullMenuModel.fromJson(response.data as Map<String, dynamic>);
      }
    } on DioException catch (e) {
      print("Error fetching menu for $restaurantIdOrSlug: ${e.message}");
    } catch (e) {
      print("Unexpected error fetching menu for $restaurantIdOrSlug: $e");
      Get.snackbar("Error", "Could not fetch menu.", snackPosition: SnackPosition.BOTTOM);
    }
    return null;
  }
}