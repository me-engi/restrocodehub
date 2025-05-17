import 'package:flutter/material.dart';
import 'package:get/get.dart';
import 'package:restrofrontend/app/data/model/order_model.dart';
import 'package:restrofrontend/app/routes/app_pages.dart';
import '../controllers/order_history_controller.dart';


class OrderHistoryScreen extends GetView<OrderHistoryController> {
  const OrderHistoryScreen({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    final scrollController = ScrollController();
    scrollController.addListener(() {
      if (scrollController.position.pixels == scrollController.position.maxScrollExtent &&
          !controller.isLoading.value &&
          controller.hasMoreOrders.value) {
        controller.fetchOrders();
      }
    });

    return Scaffold(
      appBar: AppBar(title: const Text("My Orders")),
      body: Obx(() {
        if (controller.isLoading.value && controller.orders.isEmpty) {
          return const Center(child: CircularProgressIndicator());
        }
        if (controller.orders.isEmpty && !controller.isLoading.value) {
          return Center(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                const Icon(Icons.receipt_long_outlined, size: 80, color: Colors.grey),
                const SizedBox(height: 20),
                const Text("You haven't placed any orders yet.", style: TextStyle(fontSize: 18)),
                 const SizedBox(height: 20),
                ElevatedButton(
                  onPressed: () => Get.offAllNamed(Routes.HOME),
                  child: const Text("Start Ordering"),
                )
              ],
            ),
          );
        }

        return RefreshIndicator(
          onRefresh: () => controller.fetchOrders(isRefresh: true),
          child: ListView.builder(
            controller: scrollController,
            itemCount: controller.orders.length + (controller.hasMoreOrders.value ? 1 : 0),
            itemBuilder: (context, index) {
              if (index == controller.orders.length && controller.hasMoreOrders.value) {
                return const Padding(
                  padding: EdgeInsets.symmetric(vertical: 16.0),
                  child: Center(child: CircularProgressIndicator()),
                );
              }
              if (index >= controller.orders.length) return const SizedBox.shrink();

              final order = controller.orders[index];
              return OrderHistoryCard(order: order, onTap: () => controller.viewOrderDetail(order));
            },
          ),
        );
      }),
    );
  }
}

class OrderHistoryCard extends StatelessWidget {
  final OrderListModel order;
  final VoidCallback onTap;

  const OrderHistoryCard({Key? key, required this.order, required this.onTap}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      child: InkWell(
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.all(16.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(
                    "Order #${order.orderNumber.substring(order.orderNumber.length - 6)}", // Show last 6 chars
                    style: Get.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold),
                  ),
                  Text(
                    "\$${order.totalPrice.toStringAsFixed(2)}",
                     style: Get.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold, color: Get.theme.primaryColor),
                  ),
                ],
              ),
              const SizedBox(height: 8),
              Text("Restaurant: ${order.restaurantName}", style: Get.textTheme.bodyMedium),
              Text("Date: ${Get.Utils. капитала(order.createdAt.toLocal().toString().substring(0, 16))}", style: Get.textTheme.bodySmall), // Format date
              const SizedBox(height: 8),
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                   Chip(
                    label: Text(order.statusDisplay, style: const TextStyle(fontSize: 12, color: Colors.white)),
                    backgroundColor: _getStatusColor(order.status),
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                  ),
                  Text(order.orderTypeDisplay, style: Get.textTheme.bodySmall),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  Color _getStatusColor(String status) {
    switch (status) {
      case 'PENDING_PAYMENT':
      case 'AWAITING_CONFIRMATION':
        return Colors.orange.shade700;
      case 'CONFIRMED':
      case 'PREPARING':
        return Colors.blue.shade700;
      case 'READY_FOR_PICKUP':
      case 'OUT_FOR_DELIVERY':
        return Colors.teal.shade600;
      case 'COMPLETED':
      case 'DELIVERED':
        return Colors.green.shade700;
      case 'CANCELLED_BY_USER':
      case 'CANCELLED_BY_RESTAURANT':
      case 'FAILED_PAYMENT':
      case 'SYSTEM_CANCELLED':
        return Colors.red.shade700;
      default:
        return Colors.grey.shade600;
    }
  }
}