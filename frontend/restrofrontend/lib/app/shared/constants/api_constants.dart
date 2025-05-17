class ApiConstants {
  // Replace with your actual backend base URL
  static const String baseUrl = "http://10.0.2.2:8000/api/v1"; // Android emulator accessing host machine's localhost
  // For iOS emulator: static const String baseUrl = "http://localhost:8000/api/v1";
  // For physical device testing, use your machine's network IP: e.g., "http://192.168.1.100:8000/api/v1"

  // Auth Endpoints
  static const String loginEndpoint = "/users/auth/login/";
  static const String registerTenantEndpoint = "/users/auth/register/tenant/";
  static const String refreshTokenEndpoint = "/users/auth/token/refresh/";
  static const String logoutEndpoint = "/users/auth/logout/"; // This might just be client-side token removal + optional server call
  static const String requestPasswordResetEndpoint = "/users/auth/password/reset/request/";
  static const String confirmPasswordResetEndpoint = "/users/auth/password/reset/confirm/";
  static const String changePasswordEndpoint = "/users/auth/password/change/";

  // User "Me" Endpoints
  static const String currentUserEndpoint = "/users/me/";
  static const String currentUserSessionsEndpoint = "/users/me/sessions/";
  static const String nearbyRestaurantsEndpoint = "/restaurants/nearby/"; // GET
  static String restaurantMenuEndpoint(String restaurantIdOrSlug) => "/restaurants/$restaurantIdOrSlug/menu/"; // GET
  // static String revokeSessionEndpoint(String sessionId) => "/users/me/sessions/$sessionId/revoke/"; // Example
  
  static const String cartDetailEndpoint = "/orders/cart/"; // GET (view), DELETE (clear)
  static const String cartAddItemEndpoint = "/orders/cart/add-item/"; // POST
  static String cartUpdateItemEndpoint(String cartItemId) => "/orders/cart/items/$cartItemId/"; // PATCH/PUT (update qty)
  static String cartRemoveItemEndpoint(String cartItemId) => "/orders/cart/items/$cartItemId/"; // DELETE

  // Order Endpoints
  static const String placeOrderEndpoint = "/orders/place-order/"; // POST
  static const String myOrderHistoryEndpoint = "/orders/"; // GET (OrderListViewSet filters by user)
  static String orderDetailEndpoint(String orderId) => "/orders/$orderId/"; // GET
  static String cancelMyOrderEndpoint(String orderId) => "/orders/$orderId/cancel-my-order/"; // POST

  // Payment Endpoints
  static const String initiatePaymentEndpoint = "/payments/initiate/"; // POST
  // Webhooks are backend-only, not called by Flutter

  // ... add other endpoint constants ...
}