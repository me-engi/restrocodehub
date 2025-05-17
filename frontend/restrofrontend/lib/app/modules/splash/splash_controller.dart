// lib/app/modules/splash/splash_controller.dart
import 'package:get/get.dart';
import 'package:get_storage/get_storage.dart';
import '../../routes/app_pages.dart';
// No need to import LoginController directly if AuthRepository or an AuthService handles login check

class SplashController extends GetxController {
  final GetStorage _storage = GetStorage();

  @override
  void onReady() { // onReady is called after the widget is rendered
    super.onReady();
    _checkAuthAndNavigate();
  }

  Future<void> _checkAuthAndNavigate() async {
    // Add a small delay for splash screen visibility, if desired
    await Future.delayed(const Duration(seconds: 2));

    final accessToken = _storage.read('accessToken');
    // You might want a more robust check here, e.g., token expiry or a quick validation ping to backend

    if (accessToken != null) {
      print("Splash: Token found, navigating to HOME");
      Get.offAllNamed(Routes.HOME); // Use offAllNamed to remove splash from stack
    } else {
      print("Splash: No token, navigating to LOGIN");
      Get.offAllNamed(Routes.LOGIN);
    }
  }
}