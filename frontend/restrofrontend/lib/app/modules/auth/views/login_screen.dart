import 'package:flutter/material.dart';
import 'package:get/get.dart';

import '../controllers/login_controller.dart';
import '../../../routes/app_pages.dart'; // For navigation to signup

class LoginScreen extends GetView<LoginController> { // Use GetView for direct controller access
  const LoginScreen({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    // The controller is automatically found by GetView if bindings are set up
    // Or you can do: final LoginController controller = Get.find<LoginController>();

    return Scaffold(
      appBar: AppBar(
        title: const Text("Login - Culinary AI"),
        centerTitle: true,
      ),
      body: Center(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(20.0),
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 400), // Max width for desktop-like form
            child: Form(
              key: controller.loginFormKey,
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: <Widget>[
                  Text(
                    "Welcome Back!",
                    style: Get.textTheme.headlineMedium,
                    textAlign: TextAlign.center,
                  ),
                  const SizedBox(height: 8),
                  Text(
                    "Log in to continue your culinary journey.",
                    style: Get.textTheme.titleSmall,
                    textAlign: TextAlign.center,
                  ),
                  const SizedBox(height: 30),
                  TextFormField(
                    controller: controller.emailController,
                    decoration: const InputDecoration(
                      labelText: "Email",
                      prefixIcon: Icon(Icons.email_outlined),
                      border: OutlineInputBorder(),
                    ),
                    keyboardType: TextInputType.emailAddress,
                    validator: controller.validateEmail,
                  ),
                  const SizedBox(height: 20),
                  Obx(() => TextFormField( // Obx for reactive UI update
                        controller: controller.passwordController,
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
                  const SizedBox(height: 10),
                  Align(
                    alignment: Alignment.centerRight,
                    child: TextButton(
                      onPressed: () {
                        // TODO: Navigate to Forgot Password Screen
                        Get.snackbar("Forgot Password", "Feature coming soon!", snackPosition: SnackPosition.BOTTOM);
                      },
                      child: const Text("Forgot Password?"),
                    ),
                  ),
                  const SizedBox(height: 25),
                  Obx(() => ElevatedButton( // Obx for reactive loading state
                        onPressed: controller.isLoading.value ? null : controller.loginUser,
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
                            : const Text("Login"),
                      )),
                  const SizedBox(height: 20),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      const Text("Don't have an account?"),
                      TextButton(
                        onPressed: () {
                          Get.toNamed(Routes.SIGNUP_TENANT); // Navigate to your signup route
                        },
                        child: const Text("Sign Up"),
                      ),
                    ],
                  ),
                  // Optional: Social Login Buttons
                  // const SizedBox(height: 20),
                  // const Row(
                  //   children: [
                  //     Expanded(child: Divider()),
                  //     Padding(
                  //       padding: EdgeInsets.symmetric(horizontal: 8.0),
                  //       child: Text("OR"),
                  //     ),
                  //     Expanded(child: Divider()),
                  //   ],
                  // ),
                  // const SizedBox(height: 20),
                  // ElevatedButton.icon(
                  //   icon: const Icon(Icons.g_mobiledata), // Replace with actual Google icon
                  //   label: const Text("Login with Google"),
                  //   onPressed: () {
                  //     // TODO: Implement Google Sign In
                  //   },
                  //   style: ElevatedButton.styleFrom(backgroundColor: Colors.redAccent.withOpacity(0.1)),
                  // ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}