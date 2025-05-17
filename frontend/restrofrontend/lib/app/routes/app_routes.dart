// lib/app/routes/app_routes.dart
part of 'app_pages.dart';

abstract class Routes {
  Routes._();

  static const SPLASH = _Paths.SPLASH; // Add this
  static const LOGIN = _Paths.LOGIN;
  static const SIGNUP_TENANT = _Paths.SIGNUP_TENANT;
  static const HOME = _Paths.HOME;
  static const RESTAURANT_MENU = _Paths.RESTAURANT_MENU;
}

abstract class _Paths {
  _Paths._();

  static const SPLASH = '/'; // Splash screen is now the root
  static const LOGIN = '/login';
  static const SIGNUP_TENANT = '/signup-tenant';
  static const HOME = '/home';
  static const RESTAURANT_MENU = '/restaurant-menu'; // Example, could be /restaurants/:id/menu
}