import 'package:get/get.dart';
import 'package:restrofrontend/app/data/providers/resturant_repository.dart';
import 'package:restrofrontend/app/modules/auth/controllers/home_controller.dart';



class HomeBinding extends Bindings {
  @override
  void dependencies() {
    // Register RestaurantRepository if not already globally registered
    if (!Get.isRegistered<RestaurantRepository>()) {
      Get.lazyPut<RestaurantRepository>(() => RestaurantRepository());
    }
    Get.lazyPut<HomeController>(() => HomeController());
  }
}