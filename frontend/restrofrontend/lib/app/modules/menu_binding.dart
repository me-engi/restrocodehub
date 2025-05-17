import 'package:get/get.dart';
import 'package:restrofrontend/app/data/providers/resturant_repository.dart';
import 'package:restrofrontend/app/modules/auth/controllers/resturent_menu_controller.dart';


class MenuBinding extends Bindings {
  @override
  void dependencies() {
    // RestaurantRepository might be registered globally or in HomeBinding already
    if (!Get.isRegistered<RestaurantRepository>()) {
      Get.lazyPut<RestaurantRepository>(() => RestaurantRepository());
    }
    // If you have a CartController for managing cart state globally:
    // if (!Get.isRegistered<CartController>()) {
    //   Get.lazyPut<CartController>(() => CartController());
    // }
    Get.lazyPut<RestaurantMenuController>(() => RestaurantMenuController());
  }
}