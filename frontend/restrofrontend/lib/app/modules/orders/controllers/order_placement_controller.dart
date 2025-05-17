import 'package:flutter/material.dart';
import 'package:get/get.dart';
import 'package:get_storage/get_storage.dart'; // For potentially storing/retrieving user details

 // For OrderDetailModel if returned
import '../../../data/providers/order_repository.dart';
import '../../../routes/app_pages.dart';
import '../../auth/controllers/login_controller.dart'; // To get logged-in user info
import 'cart_controller.dart'; // To get cart details and clear it

class OrderPlacementController extends GetxController {
  final OrderRepository _orderRepository = Get.find<OrderRepository>();
  final CartController cartController = Get.find<CartController>();
  final LoginController _loginController = Get.find<LoginController>(); // Assuming it's globally available

  // --- Observable State ---
  var isLoading = false.obs;
  var selectedOrderType = 'TAKEAWAY'.obs; // Default order type

  // --- Form Global Key ---
  final GlobalKey<FormState> checkoutFormKey = GlobalKey<FormState>();

  // --- Text Editing Controllers ---
  // Customer Info
  late TextEditingController customerNameController;
  late TextEditingController customerPhoneController;
  late TextEditingController customerEmailController;

  // Dine-In
  late TextEditingController tableNumberController;

  // Delivery
  late TextEditingController deliveryAddress1Controller;
  late TextEditingController deliveryAddress2Controller;
  late TextEditingController deliveryCityController;
  late TextEditingController deliveryStateProvinceController;
  late TextEditingController deliveryPostalCodeController;
  late TextEditingController deliveryCountryController;
  late TextEditingController deliveryInstructionsController;

  // General
  late TextEditingController specialInstructionsController; // For restaurant

  // Payment (simple hint for now, real payment handled by payment gateway flow)
  var selectedPaymentMethodHint = Rx<String?>(null);


  @override
  void onInit() {
    super.onInit();
    // Initialize controllers
    customerNameController = TextEditingController();
    customerPhoneController = TextEditingController();
    customerEmailController = TextEditingController();
    tableNumberController = TextEditingController();
    deliveryAddress1Controller = TextEditingController();
    deliveryAddress2Controller = TextEditingController();
    deliveryCityController = TextEditingController();
    deliveryStateProvinceController = TextEditingController();
    deliveryPostalCodeController = TextEditingController();
    deliveryCountryController = TextEditingController();
    deliveryInstructionsController = TextEditingController();
    specialInstructionsController = TextEditingController();

    // Pre-fill customer info if user is logged in
    _prefillUserInfo();
  }

  void _prefillUserInfo() {
    if (_loginController.isLoggedIn && _loginController.currentUser.value != null) {
      final user = _loginController.currentUser.value!;
      customerNameController.text = user.name ?? "";
      customerEmailController.text = user.email;
      // customerPhoneController.text = user.phoneNumber ?? ""; // Assuming UserModel has phoneNumber
    }
  }

  void onOrderTypeChanged(String newOrderType) {
    selectedOrderType.value = newOrderType;
    // Clear irrelevant fields when order type changes
    if (newOrderType != 'DINE_IN') {
      tableNumberController.clear();
    }
    if (newOrderType != 'DELIVERY') {
      deliveryAddress1Controller.clear();
      deliveryAddress2Controller.clear();
      deliveryCityController.clear();
      deliveryStateProvinceController.clear();
      deliveryPostalCodeController.clear();
      deliveryCountryController.clear();
      deliveryInstructionsController.clear();
    }
  }

  Future<void> placeOrder() async {
    if (!checkoutFormKey.currentState!.validate()) {
      Get.snackbar(
        "Validation Error",
        "Please correct the errors in the form.",
        snackPosition: SnackPosition.BOTTOM,
        backgroundColor: Colors.redAccent,
        colorText: Colors.white,
      );
      return;
    }

    if (cartController.cart.value == null || cartController.cart.value!.items.isEmpty) {
      Get.snackbar(
        "Empty Cart",
        "Your cart is empty. Please add items to order.",
        snackPosition: SnackPosition.BOTTOM,
        backgroundColor: Colors.orangeAccent,
        colorText: Colors.black,
      );
      return;
    }

    if (cartController.cart.value!.restaurantId == null) {
        Get.snackbar(
            "Error",
            "Cannot place order, restaurant context is missing from cart.",
            snackPosition: SnackPosition.BOTTOM
        );
        return;
    }


    isLoading.value = true;

    Map<String, dynamic> orderData = {
      "cart_id": cartController.cart.value!.id,
      "restaurant_id": cartController.cart.value!.restaurantId, // Crucial
      "order_type": selectedOrderType.value,
      "customer_name": customerNameController.text.trim(),
      "customer_phone": customerPhoneController.text.trim(),
      "customer_email": customerEmailController.text.trim(),
      "special_instructions_for_restaurant": specialInstructionsController.text.trim(),
      "payment_method_hint": selectedPaymentMethodHint.value, // e.g., "COD", "ONLINE"
      // "scheduled_for_time": null, // Add if you have scheduling
    };

    if (selectedOrderType.value == 'DINE_IN') {
      orderData['table_number'] = tableNumberController.text.trim();
    } else if (selectedOrderType.value == 'DELIVERY') {
      orderData.addAll({
        'delivery_address_line1': deliveryAddress1Controller.text.trim(),
        'delivery_address_line2': deliveryAddress2Controller.text.trim(),
        'delivery_city': deliveryCityController.text.trim(),
        'delivery_state_province': deliveryStateProvinceController.text.trim(),
        'delivery_postal_code': deliveryPostalCodeController.text.trim(),
        'delivery_country': deliveryCountryController.text.trim(),
        'delivery_instructions': deliveryInstructionsController.text.trim(),
      });
    }

    final placedOrder = await _orderRepository.placeOrder(orderData);
    isLoading.value = false;

    if (placedOrder != null) {
      await cartController.clearCurrentCart(showSnackbar: false); // Clear cart on successful order
      Get.snackbar(
        "Order Placed!",
        "Your order #${placedOrder.orderNumber.substring(placedOrder.orderNumber.length - 6)} has been successfully placed.",
        snackPosition: SnackPosition.TOP,
        backgroundColor: Colors.green,
        colorText: Colors.white,
        duration: const Duration(seconds: 4),
      );
      // Navigate to Order Confirmation or Payment screen based on flow
      // If payment is handled separately (e.g. online payment after this step):
      // Get.offNamed(Routes.PAYMENT_SCREEN, arguments: placedOrder);
      // If order is placed and confirmed (e.g. COD or payment handled implicitly):
      Get.offAllNamed(Routes.ORDER_CONFIRMATION, arguments: placedOrder);
    } else {
      // Error snackbar is usually shown by the repository's Dio error handler.
      // If not, show a generic one here.
      // Get.snackbar("Order Failed", "Could not place your order. Please try again.", snackPosition: SnackPosition.BOTTOM);
    }
  }

  @override
  void onClose() {
    // Dispose all TextEditingControllers
    customerNameController.dispose();
    customerPhoneController.dispose();
    customerEmailController.dispose();
    tableNumberController.dispose();
    deliveryAddress1Controller.dispose();
    deliveryAddress2Controller.dispose();
    deliveryCityController.dispose();
    deliveryStateProvinceController.dispose();
    deliveryPostalCodeController.dispose();
    deliveryCountryController.dispose();
    deliveryInstructionsController.dispose();
    specialInstructionsController.dispose();
    super.onClose();
  }
}