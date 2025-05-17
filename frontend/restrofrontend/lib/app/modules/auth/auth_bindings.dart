import 'package:get/get.dart';
import 'package:restrofrontend/app/modules/auth/controllers/signup_controller.dart';

import '../../data/providers/auth_repository.dart';
import './controllers/login_controller.dart';
// Import other controllers like SignupController if you have them

class AuthBinding extends Bindings {
  @override
  void dependencies() {
    // Repositories should ideally be registered globally if used by many controllers,
    // or lazily put here if specific to this module.
    // For this example, let's assume AuthRepository might be used more broadly,
    // so it could be registered in main.dart or an AppBinding.
    // If it's only for auth module, lazyPut is fine.
    Get.lazyPut<AuthRepository>(() => AuthRepository());

    Get.lazyPut<LoginController>(() => LoginController());
    Get.lazyPut<SignupController>(() => SignupController());
    // Get.lazyPut<SignupController>(() => SignupController());
  }
}