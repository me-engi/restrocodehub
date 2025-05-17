import 'package:flutter/material.dart'; // For TextEditingController
import 'package:get/get.dart';
import 'package:get_storage/get_storage.dart'; // For storing token
import 'package:restrofrontend/app/data/model/user_model.dart';

import '../../../data/providers/auth_repository.dart';

import '../../../routes/app_pages.dart'; // For navigation

class LoginController extends GetxController {
  final AuthRepository _authRepository = Get.find<AuthRepository>(); // Dependency Injection
  final GetStorage _storage = GetStorage(); // For storing auth tokens

  // Form Keys and Text Editing Controllers
  final GlobalKey<FormState> loginFormKey = GlobalKey<FormState>();
  late TextEditingController emailController;
  late TextEditingController passwordController;

  // Observable state variables
  var isLoading = false.obs;
  var obscurePassword = true.obs;

  // To store user data after login
  var currentUser = Rx<UserModel?>(null);
  var accessToken = Rx<String?>(null);
  var refreshToken = Rx<String?>(null);


  @override
  void onInit() {
    super.onInit();
    emailController = TextEditingController();
    passwordController = TextEditingController();
    // For testing, prefill:
    // emailController.text = "test@example.com";
    // passwordController.text = "password123";
  }

  @override
  void onClose() {
    emailController.dispose();
    passwordController.dispose();
    super.onClose();
  }

  void toggleObscurePassword() {
    obscurePassword.value = !obscurePassword.value;
  }

  String? validateEmail(String? value) {
    if (value == null || value.isEmpty) {
      return "Email is required";
    }
    if (!GetUtils.isEmail(value)) {
      return "Enter a valid email";
    }
    return null;
  }

  String? validatePassword(String? value) {
    if (value == null || value.isEmpty) {
      return "Password is required";
    }
    if (value.length < 6) { // Example minimum length
      return "Password must be at least 6 characters";
    }
    return null;
  }

  Future<void> loginUser() async {
    if (loginFormKey.currentState!.validate()) {
      isLoading.value = true;
      try {
        final response = await _authRepository.login(
          emailController.text.trim(),
          passwordController.text.trim(),
        );

        if (response != null) {
          // Assuming response structure:
          // {
          //   "access_token": "...",
          //   "refresh_token": "...",
          //   "user": { "id": "...", "email": "...", ... }
          // }
          final String newAccessToken = response['access_token'];
          final String newRefreshToken = response['refresh_token'];
          final UserModel loggedInUser = UserModel.fromJson(response['user']);

          // Store tokens securely (GetStorage is simple, for production consider flutter_secure_storage)
          await _storage.write('accessToken', newAccessToken);
          await _storage.write('refreshToken', newRefreshToken);
          await _storage.write('userData', loggedInUser.toJson()); // Store user data

          // Update controller state
          accessToken.value = newAccessToken;
          refreshToken.value = newRefreshToken;
          currentUser.value = loggedInUser;


          Get.snackbar("Success", "Logged in successfully!", snackPosition: SnackPosition.BOTTOM);
          // Navigate to Home Screen or appropriate screen
          Get.offAllNamed(Routes.HOME); // Or your main app screen after login
        } else {
          // Error message is already shown by AuthRepository's Dio interceptor or error handler
          // Get.snackbar("Login Failed", "Invalid credentials or server error.", snackPosition: SnackPosition.BOTTOM);
        }
      } catch (e) {
        print("Login Controller Error: $e");
        Get.snackbar("Error", "An unexpected error occurred.", snackPosition: SnackPosition.BOTTOM);
      } finally {
        isLoading.value = false;
      }
    }
  }

  // Helper to check if user is logged in (based on stored token)
  bool get isLoggedIn {
    return _storage.read('accessToken') != null;
  }

  // Method to auto-login if tokens exist (call this from main.dart or splash screen)
  Future<void> tryAutoLogin() async {
     final storedAccessToken = _storage.read('accessToken');
     final storedRefreshToken = _storage.read('refreshToken');
     final storedUserData = _storage.read('userData');

     if (storedAccessToken != null && storedRefreshToken != null && storedUserData != null) {
        // TODO: Optionally verify token validity with backend here if needed
        // For now, assume if it exists, it's good for auto-login for simplicity
        accessToken.value = storedAccessToken;
        refreshToken.value = storedRefreshToken;
        currentUser.value = UserModel.fromJson(storedUserData as Map<String, dynamic>);
        print("Auto login successful for ${currentUser.value?.email}");
        // Don't navigate here, let the initial route logic in main.dart handle it
     } else {
        print("No stored tokens for auto login.");
     }
  }

  Future<void> logoutUser() async {
    // Optionally call backend logout endpoint
    // await _authRepository.logout(_storage.read('refreshToken'));

    await _storage.remove('accessToken');
    await _storage.remove('refreshToken');
    await _storage.remove('userData');
    currentUser.value = null;
    accessToken.value = null;
    refreshToken.value = null;
    Get.offAllNamed(Routes.LOGIN); // Navigate to login screen
  }
}