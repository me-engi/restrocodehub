import 'package:flutter/material.dart';
import 'package:get/get.dart';

import '../controllers/signup_controller.dart'; // Change to your signup controller
import '../../../routes/app_pages.dart';

class SignupTenantScreen extends GetView<SignupController> { // Use SignupController
  const SignupTenantScreen({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text("Register Your Business"),
        centerTitle: true,
      ),
      body: Center(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(20.0),
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 450),
            child: Form(
              key: controller.signupFormKey,
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: <Widget>[
                  Text(
                    "Join Culinary AI Concierge",
                    style: Get.textTheme.headlineSmall,
                    textAlign: TextAlign.center,
                  ),
                  const SizedBox(height: 8),
                  Text(
                    "Create an account for your restaurant or food business.",
                    style: Get.textTheme.bodyMedium,
                    textAlign: TextAlign.center,
                  ),
                  const SizedBox(height: 30),
                  TextFormField(
                    controller: controller.tenantNameController,
                    decoration: const InputDecoration(
                      labelText: "Business Name (e.g., Luigi's Pizza)",
                      prefixIcon: Icon(Icons.store_mall_directory_outlined),
                      border: OutlineInputBorder(),
                    ),
                    validator: controller.validateTenantName,
                  ),
                  const SizedBox(height: 20),
                  TextFormField(
                    controller: controller.adminNameController,
                    decoration: const InputDecoration(
                      labelText: "Your Full Name (Admin)",
                      prefixIcon: Icon(Icons.person_outline),
                      border: OutlineInputBorder(),
                    ),
                    validator: controller.validateName,
                  ),
                  const SizedBox(height: 20),
                  TextFormField(
                    controller: controller.adminEmailController,
                    decoration: const InputDecoration(
                      labelText: "Your Email (Admin Login)",
                      prefixIcon: Icon(Icons.email_outlined),
                      border: OutlineInputBorder(),
                    ),
                    keyboardType: TextInputType.emailAddress,
                    validator: controller.validateEmail,
                  ),
                  const SizedBox(height: 20),
                  Obx(() => TextFormField(
                        controller: controller.adminPasswordController,
                        decoration: InputDecoration(
                          labelText: "Password",
                          prefixIcon: const Icon(Icons.lock_outline),
                          border: const OutlineInputBorder(),
                          suffixIcon: IconButton(
                            icon: Icon(
                              controller.obscurePassword.value
                                  ? Icons.visibility_off_outlined
                                  : Icons.visibility_outlined,
                            ),
                            onPressed: controller.toggleObscurePassword,
                          ),
                        ),
                        obscureText: controller.obscurePassword.value,
                        validator: controller.validatePassword,
                      )),
                  const SizedBox(height: 20),
                  Obx(() => TextFormField(
                        controller: controller.adminConfirmPasswordController,
                        decoration: InputDecoration(
                          labelText: "Confirm Password",
                          prefixIcon: const Icon(Icons.lock_reset_outlined),
                          border: const OutlineInputBorder(),
                           suffixIcon: IconButton(
                            icon: Icon(
                              controller.obscureConfirmPassword.value
                                  ? Icons.visibility_off_outlined
                                  : Icons.visibility_outlined,
                            ),
                            onPressed: controller.toggleObscureConfirmPassword,
                          ),
                        ),
                        obscureText: controller.obscureConfirmPassword.value,
                        validator: controller.validateConfirmPassword,
                      )),
                  const SizedBox(height: 30),
                  Obx(() => ElevatedButton(
                        onPressed: controller.isLoading.value
                            ? null
                            : controller.registerTenantAndAdmin,
                        style: ElevatedButton.styleFrom(
                          padding: const EdgeInsets.symmetric(vertical: 15),
                          textStyle: const TextStyle(fontSize: 16),
                        ),
                        child: controller.isLoading.value
                            ? const SizedBox(
                                height: 20,
                                width: 20,
                                child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                              )
                            : const Text("Create Account"),
                      )),
                  const SizedBox(height: 20),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      const Text("Already have an account?"),
                      TextButton(
                        onPressed: () {
                          Get.offNamed(Routes.LOGIN); // Go back to Login
                        },
                        child: const Text("Login"),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}