import 'package:get/get.dart';
import '../../data/providers/payment_repository.dart';
import './controllers/payment_controller.dart';

class PaymentBinding extends Bindings {
  @override
  void dependencies() {
    if (!Get.isRegistered<PaymentRepository>()) {
      Get.lazyPut<PaymentRepository>(() => PaymentRepository());
    }
    Get.lazyPut<PaymentController>(() => PaymentController());
  }
}