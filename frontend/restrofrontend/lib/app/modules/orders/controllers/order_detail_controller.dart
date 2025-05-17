import 'package:flutter/material.dart';
import 'package:get/get.dart';
import 'package:restrofrontend/app/data/model/order_model.dart';
import 'package:restrofrontend/app/modules/auth/controllers/login_controller.dart';

import '../../../data/providers/order_repository.dart';

class OrderDetailController extends GetxController {
  final OrderRepository _orderRepository = Get.find<OrderRepository>();
  final String orderId = Get.arguments as String; // Get orderId passed as argument

  var isLoading = true.obs;
  var orderDetail = Rx<OrderDetailModel?>(null);
  var errorMessage = Rx<String?>(null);

  // For cancellation
  var isCancelling = false.obs;


  @override
  void onInit() {
    super.onInit();
    fetchOrderDetailData();
  }

  Future<void> fetchOrderDetailData() async {
    isLoading.value = true;
    errorMessage.value = null;
    final fetchedOrder = await _orderRepository.fetchOrderDetail(orderId);
    if (fetchedOrder != null) {
      orderDetail.value = fetchedOrder;
    } else {
      errorMessage.value = "Failed to load order details.";
      Get.snackbar("Error", errorMessage.value!, snackPosition: SnackPosition.BOTTOM);
    }
    isLoading.value = false;
  }

  bool get canCustomerCancel {
    if (orderDetail.value == null || orderDetail.value!.userEmail != Get.find<LoginController>().currentUser.value?.email) { // crude check for owner
      return false;
    }
    return orderDetail.value!.status == 'AWAITING_CONFIRMATION';
  }

  Future<void> cancelOrder() async {
    if (!canCustomerCancel) {
        Get.snackbar("Cancellation Denied", "This order cannot be cancelled by you at this time.", snackPosition: SnackPosition.BOTTOM);
        return;
    }

    // Show confirmation dialog
    bool? confirmCancel = await Get.dialog<bool>(
        AlertDialog(
            title: const Text("Cancel Order?"),
            content: const Text("Are you sure you want to cancel this order? This action cannot be undone."),
            actions: [
                TextButton(onPressed: () => Get.back(result: false), child: const Text("Keep Order")),
                TextButton(onPressed: () => Get.back(result: true), child: const Text("Yes, Cancel"), style: TextButton.styleFrom(foregroundColor: Colors.red)),
            ],
        )
    );

    if (confirmCancel == true) {
        isCancelling.value = true;
        final updatedOrder = await _orderRepository.cancelMyOrder(orderId, "Cancelled by customer via app.");
        isCancelling.value = false;
        if (updatedOrder != null) {
            orderDetail.value = updatedOrder;
            Get.snackbar("Order Cancelled", "Your order has been cancelled.", snackPosition: SnackPosition.BOTTOM);
        } else {
            Get.snackbar("Cancellation Failed", "Could not cancel the order. Please try again.", snackPosition: SnackPosition.BOTTOM);
        }
    }
  }
}