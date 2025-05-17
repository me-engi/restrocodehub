import 'package:get/get.dart';
import 'package:get_storage/get_storage.dart';
import 'package:restrofrontend/app/modules/auth/auth_bindings.dart';
import 'package:restrofrontend/app/modules/auth/views/home_screen.dart';
import 'package:restrofrontend/app/modules/auth/views/resturent_menu_screen.dart';
import 'package:restrofrontend/app/modules/auth/views/signup_tenant_screen.dart';
import 'package:restrofrontend/app/modules/home_binding.dart';
import 'package:restrofrontend/app/modules/menu_binding.dart';
import 'package:restrofrontend/app/modules/splash/splash_binding.dart';
import 'package:restrofrontend/app/modules/splash/splash_screen.dart';


import '../modules/auth/views/login_screen.dart';
// Import other screens and bindings
// import '../modules/auth/views/signup_tenant_screen.dart';
// import '../modules/home/bindings/home_binding.dart';
// import '../modules/home/views/home_screen.dart';
// import '../modules/splash/bindings/splash_binding.dart';
// import '../modules/splash/views/splash_screen.dart';


part 'app_routes.dart'; // Link to the routes file



class AppPages {
  AppPages._();

  // INITIALROUTE is now handled by starting with SPLASH
  static const INITIAL = Routes.SPLASH; // Start with Splash screen

  static final routes = [
    GetPage(
      name: _Paths.SPLASH,
      page: () => const SplashScreen(),
      binding: SplashBinding(),
    ),
    GetPage(
      name: _Paths.LOGIN,
      page: () => const LoginScreen(),
      binding: AuthBinding(),
    ),
    GetPage(
      name: _Paths.SIGNUP_TENANT,
      page: () => const SignupTenantScreen(), // Ensure this screen exists
      binding: AuthBinding(),
    ),
    GetPage(
      name: _Paths.HOME,
      page: () => const HomeScreen(),
      binding: HomeBinding(),
    ),
    GetPage(
      name: _Paths.RESTAURANT_MENU, // Ensure _Paths.RESTAURANT_MENU is defined
      page: () => const RestaurantMenuScreen(),
      binding: MenuBinding(),
      // Example of how to handle dynamic parts of a route if needed
      // name: '${_Paths.RESTAURANT_MENU}/:restaurantId',
      // parameters: {'restaurantId': 'string'},
    ),
    // ... other pages
  ];
}