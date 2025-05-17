import 'package:flutter/material.dart';
import 'package:get/get.dart';

import '../../../data/providers/auth_repository.dart';
import '../../../routes/app_pages.dart';

class SignupController extends GetxController {
  final AuthRepository _authRepository = Get.find<AuthRepository>();

  final GlobalKey<FormState> signupFormKey = GlobalKey<FormState>();
  late TextEditingController tenantNameController;
  late TextEditingController adminNameController;
  late TextEditingController adminEmailController;
  late TextEditingController adminPasswordController;
  late TextEditingController adminConfirmPasswordController;

  var isLoading = false.obs;
  var obscurePassword = true.obs;
  var obscureConfirmPassword = true.obs;

  @override
  void onInit() {
    super.onInit();
    tenantNameController = TextEditingController();
    adminNameController = TextEditingController();
    adminEmailController = TextEditingController();
    adminPasswordController = TextEditingController();
    adminConfirmPasswordController = TextEditingController();
  }

  @override
  void onClose() {
    tenantNameController.dispose();
    adminNameController.dispose();
    adminEmailController.dispose();
    adminPasswordController.dispose();
    adminConfirmPasswordController.dispose();
    super.onClose();
  }

  void toggleObscurePassword() {
    obscurePassword.value = !obscurePassword.value;
  }

  void toggleObscureConfirmPassword() {
    obscureConfirmPassword.value = !obscureConfirmPassword.value;
  }

  String? validateTenantName(String? value) {
    if (value == null || value.isEmpty) {
      return "Business name is required";
    }
    return null;
  }

  String? validateName(String? value) {
    if (value == null || value.isEmpty) {
      return "Your name is required";
    }
    return null;
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
    if (value.length < 8) {
      return "Password must be at least 8 characters";
    }
    // Add more password strength validation if needed
    return null;
  }

  String? validateConfirmPassword(String? value) {
    if (value == null || value.isEmpty) {
      return "Confirm password is required";
    }
    if (value != adminPasswordController.text) {
      return "Passwords do not match";
    }
    return null;
  }

  Future<void> registerTenantAndAdmin() async {
    if (signupFormKey.currentState!.validate()) {
      isLoading.value = true;
      try {
        final response = await _authRepository.registerTenantAndAdmin(
          tenantName: tenantNameController.text.trim(),
          adminEmail: adminEmailController.text.trim(),
          adminName: adminNameController.text.trim(),
          adminPassword: adminPasswordController.text,
          adminPassword2: adminConfirmPasswordController.text,
        );

        if (response != null) {
          // Assuming backend returns success message, user_id, tenant_id
          Get.snackbar(
            "Registration Successful",
            response['message'] ?? "Your business account has been created. Please log in.",
            snackPosition: SnackPosition.BOTTOM,
            duration: const Duration(seconds: 5)
          );
          Get.offNamed(Routes.LOGIN); // Navigate to login after successful registration
        } else {
          // Error snackbar handled by AuthRepository or its Dio interceptor
        }
      } catch (e) {
        Get.snackbar("Error", "An unexpected error occurred during registration.", snackPosition: SnackPosition.BOTTOM);
      } finally {
        isLoading.value = false;
      }
    }
  }
}