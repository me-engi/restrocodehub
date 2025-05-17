import 'package:get/get.dart';
import '../../data/providers/order_repository.dart';
import './controllers/cart_controller.dart';
import './controllers/order_placement_controller.dart';
import './controllers/order_history_controller.dart';
import './controllers/order_detail_controller.dart';

class OrdersBinding extends Bindings {
  @override
  void dependencies() {
    // OrderRepository might be registered globally if used by other modules too
    if (!Get.isRegistered<OrderRepository>()) {
      Get.lazyPut<OrderRepository>(() => OrderRepository());
    }

    Get.lazyPut<CartController>(() => CartController(), fenix: true); // fenix:true to keep alive
    Get.lazyPut<OrderPlacementController>(() => OrderPlacementController());
    Get.lazyPut<OrderHistoryController>(() => OrderHistoryController());
    Get.lazyPut<OrderDetailController>(() => OrderDetailController());
  }
}