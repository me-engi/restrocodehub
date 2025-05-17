// lib/app/routes/app_routes.dart
part of 'app_pages.dart';

abstract class Routes {
  Routes._();

  static const SPLASH = _Paths.SPLASH; // Add this
  static const LOGIN = _Paths.LOGIN;
  static const SIGNUP_TENANT = _Paths.SIGNUP_TENANT;
  static const HOME = _Paths.HOME;
  static const RESTAURANT_MENU = _Paths.RESTAURANT_MENU;
  // ...
static const CART = '/cart';
static const CHECKOUT = '/checkout'; // For OrderPlacementController
static const ORDER_HISTORY = '/order-history';
static const ORDER_DETAIL = '/order-detail'; // Could be /orders/:id
static const ORDER_CONFIRMATION = '/order-confirmation';
// ...
static const PAYMENT_SCREEN = '/payment';
// ...

// ...
}

abstract class _Paths {
  _Paths._();

  static const SPLASH = '/'; // Splash screen is now the root
  static const LOGIN = '/login';
  static const SIGNUP_TENANT = '/signup-tenant';
  static const HOME = '/home';
  static const RESTAURANT_MENU = '/restaurant-menu';
  // ...
static const CART = '/cart';
static const CHECKOUT = '/checkout'; // For OrderPlacementController
static const ORDER_HISTORY = '/order-history';
static const ORDER_DETAIL = '/order-detail'; // Could be /orders/:id
static const ORDER_CONFIRMATION = '/order-confirmation';
// ...
static const PAYMENT_SCREEN = '/payment';
// ...
// ... // Example, could be /restaurants/:id/menu
}