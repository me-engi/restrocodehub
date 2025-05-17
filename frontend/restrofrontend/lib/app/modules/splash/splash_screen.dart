// lib/app/modules/splash/splash_screen.dart
import 'package:flutter/material.dart';
import 'package:get/get.dart';
import './splash_controller.dart';

class SplashScreen extends GetView<SplashController> {
  const SplashScreen({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    // Trigger the controller's onReady logic which handles navigation
    // The controller is already put by the binding
    // Get.find<SplashController>(); // No need to call find if GetView is used correctly with bindings

    return const Scaffold(
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            // Replace with your app logo
            FlutterLogo(size: 100),
            SizedBox(height: 20),
            Text("Culinary AI Concierge", style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold)),
            SizedBox(height: 20),
            CircularProgressIndicator(),
          ],
        ),
      ),
    );
  }
}