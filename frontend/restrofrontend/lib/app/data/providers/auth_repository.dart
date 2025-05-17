import 'package:dio/dio.dart';
import 'package:get/get.dart';
 // For Get.find() if using GetConnect or global Dio instance

import '../../shared/constants/api_constants.dart'; // You'll create this
 // You'll create this
 import 'package:restrofrontend/app/data/model/user_model.dart';

class AuthRepository {
  late Dio _dio;

  AuthRepository() {
    // Initialize Dio with base options
    // You might want to create a global Dio instance or use Get.find<Dio>() if registered
    _dio = Dio(BaseOptions(
      baseUrl: ApiConstants.baseUrl, // e.g., "http://your-django-backend.com/api/v1"
      connectTimeout: const Duration(seconds: 10),
      receiveTimeout: const Duration(seconds: 10),
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
    ));

    // Optional: Add interceptors for logging, error handling, adding auth tokens
    _dio.interceptors.add(LogInterceptor(requestBody: true, responseBody: true));
    _dio.interceptors.add(InterceptorsWrapper(
      onError: (DioException e, handler) {
        // Handle Dio errors globally or per request
        print("Dio Error: ${e.message}");
        print("Dio Error Data: ${e.response?.data}");
        // You could show a generic error snackbar here using GetX
        // Get.snackbar("Error", e.message ?? "An unknown error occurred");
        return handler.next(e); // or handler.reject(e) if you want to stop
      },
    ));
  }

  Future<Map<String, dynamic>?> login(String email, String password) async {
    try {
      final response = await _dio.post(
        ApiConstants.loginEndpoint, // e.g., "/users/auth/login/"
        data: {
          'email': email,
          'password': password,
        },
      );

      if (response.statusCode == 200 && response.data != null) {
        // Assuming response.data contains {'access_token': '...', 'refresh_token': '...', 'user': {...}}
        return response.data as Map<String, dynamic>;
      } else {
        // Handle non-200 success codes if your API uses them differently
        return null;
      }
    } on DioException catch (e) {
      // Specific Dio error handling (e.g., based on e.response.statusCode)
      if (e.response?.statusCode == 401) {
        // Handle invalid credentials specifically
        Get.snackbar("Login Failed", e.response?.data['error'] ?? "Invalid credentials", snackPosition: SnackPosition.BOTTOM);
      } else {
        Get.snackbar("Login Error", e.message ?? "Could not connect to server.", snackPosition: SnackPosition.BOTTOM);
      }
      return null;
    } catch (e) {
      // Catch any other unexpected errors
      print("Login general error: $e");
      Get.snackbar("Error", "An unexpected error occurred during login.", snackPosition: SnackPosition.BOTTOM);
      return null;
    }
  }

  Future<Map<String, dynamic>?> registerTenantAndAdmin({
    required String tenantName,
    required String adminEmail,
    required String adminName,
    required String adminPassword,
    required String adminPassword2,
  }) async {
    try {
      final response = await _dio.post(
        ApiConstants.registerTenantEndpoint, // e.g., "/users/auth/register/tenant/"
        data: {
          'tenant_name': tenantName,
          'admin_email': adminEmail,
          'admin_name': adminName,
          'admin_password': adminPassword,
          'admin_password2': adminPassword2,
        },
      );
      if (response.statusCode == 201 && response.data != null) {
        return response.data as Map<String, dynamic>;
      } else {
        return null;
      }
    } on DioException catch (e) {
      if (e.response?.data != null && e.response!.data is Map) {
        // Try to get specific error messages from Django
        String errorMessage = "Registration failed.";
        (e.response!.data as Map).forEach((key, value) {
          if (value is List && value.isNotEmpty) {
            errorMessage = value.first; // Take the first error message
          } else if (value is String) {
            errorMessage = value;
          }
        });
         Get.snackbar("Registration Failed", errorMessage, snackPosition: SnackPosition.BOTTOM);
      } else {
        Get.snackbar("Registration Error", e.message ?? "Could not connect to server.", snackPosition: SnackPosition.BOTTOM);
      }
      return null;
    } catch (e) {
      Get.snackbar("Error", "An unexpected error occurred during registration.", snackPosition: SnackPosition.BOTTOM);
      return null;
    }
  }

  // Add other auth-related methods:
  // Future<void> logout(String refreshToken) async { ... }
  // Future<Map<String, dynamic>?> refreshToken(String oldRefreshToken) async { ... }
  // Future<void> requestPasswordReset(String email) async { ... }
  // Future<bool> confirmPasswordReset(String token, String newPassword) async { ... }
}