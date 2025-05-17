// lib/app/modules/orders/views/order_detail_screen.dart
import 'package:flutter/material.dart';
import 'package:get/get.dart';
import 'package:restrofrontend/app/modules/orders/controllers/order_detail_controller.dart';

 // For OrderItemCustomizationSnapshotModel

class OrderDetailScreen extends GetView<OrderDetailController> {
  const OrderDetailScreen({Key? key}) : super(key: key);

  Color _getStatusColor(String status) { // Same helper as in OrderHistoryScreen
    switch (status) {
      case 'PENDING_PAYMENT':
      case 'AWAITING_CONFIRMATION': return Colors.orange.shade700;
      case 'CONFIRMED':
      case 'PREPARING': return Colors.blue.shade700;
      case 'READY_FOR_PICKUP':
      case 'OUT_FOR_DELIVERY': return Colors.teal.shade600;
      case 'COMPLETED':
      case 'DELIVERED': return Colors.green.shade700;
      case 'CANCELLED_BY_USER':
      case 'CANCELLED_BY_RESTAURANT':
      case 'FAILED_PAYMENT':
      case 'SYSTEM_CANCELLED': return Colors.red.shade700;
      default: return Colors.grey.shade600;
    }
  }

  IconData _getStatusIcon(String status) {
     switch (status) {
      case 'PENDING_PAYMENT': return Icons.payment_outlined;
      case 'AWAITING_CONFIRMATION': return Icons.hourglass_empty_rounded;
      case 'CONFIRMED': return Icons.check_circle_outline_rounded;
      case 'PREPARING': return Icons.soup_kitchen_outlined;
      case 'READY_FOR_PICKUP': return Icons.storefront_outlined;
      case 'OUT_FOR_DELIVERY': return Icons.delivery_dining_outlined;
      case 'DELIVERED': return Icons.mark_email_read_outlined;
      case 'COMPLETED': return Icons.done_all_rounded;
      case 'CANCELLED_BY_USER':
      case 'CANCELLED_BY_RESTAURANT':
      case 'SYSTEM_CANCELLED': return Icons.cancel_outlined;
      case 'FAILED_PAYMENT': return Icons.error_outline_rounded;
      default: return Icons.info_outline_rounded;
    }
  }


  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Obx(() => Text(controller.orderDetail.value != null
            ? "Order #${controller.orderDetail.value!.orderNumber.substring(controller.orderDetail.value!.orderNumber.length - 6)}"
            : "Order Details")),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: controller.fetchOrderDetailData,
          )
        ],
      ),
      body: Obx(() {
        if (controller.isLoading.value) {
          return const Center(child: CircularProgressIndicator());
        }
        if (controller.errorMessage.value != null) {
          return Center(child: Text(controller.errorMessage.value!));
        }
        if (controller.orderDetail.value == null) {
          return const Center(child: Text("Order not found."));
        }

        final order = controller.orderDetail.value!;
        return RefreshIndicator(
          onRefresh: controller.fetchOrderDetailData,
          child: ListView(
            padding: const EdgeInsets.all(16.0),
            children: [
              // --- Order Overview ---
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(16.0),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Text("Order Status:", style: Get.textTheme.titleMedium),
                          Chip(
                            avatar: Icon(_getStatusIcon(order.status), color: Colors.white, size: 18),
                            label: Text(order.statusDisplay, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
                            backgroundColor: _getStatusColor(order.status),
                          ),
                        ],
                      ),
                      const SizedBox(height: 8),
                      Text("Order ID: ${order.orderNumber}", style: Get.textTheme.bodyMedium),
                      Text("Placed On: ${Get.Utils.capitalize(order.createdAt.toLocal().toString().substring(0, 16))}", style: Get.textTheme.bodyMedium),
                      Text("Restaurant: ${order.restaurantName}", style: Get.textTheme.bodyMedium),
                      Text("Order Type: ${order.orderTypeDisplay}", style: Get.textTheme.bodyMedium),
                      if (order.tableNumber != null && order.tableNumber!.isNotEmpty)
                        Text("Table Number: ${order.tableNumber}", style: Get.textTheme.bodyMedium),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 16),

              // --- Delivery Information (if applicable) ---
              if (order.orderType == 'DELIVERY')
                Card(
                  child: Padding(
                    padding: const EdgeInsets.all(16.0),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text("Delivery Details", style: Get.textTheme.titleLarge),
                        const Divider(),
                        Text("To: ${order.customerNameSnapshot ?? 'N/A'}", style: Get.textTheme.bodyMedium),
                        Text("Address: ${order.deliveryAddressLine1 ?? ''} ${order.deliveryAddressLine1 ?? ''}".trim(), style: Get.textTheme.bodyMedium),
                        Text("${order.deliveryCity ?? ''}, ${order.deliveryPostalCode ?? ''}", style: Get.textTheme.bodyMedium),
                        if (order.deliveryInstructions != null && order.deliveryInstructions!.isNotEmpty)
                          Text("Instructions: ${order.deliveryInstructions}", style: Get.textTheme.bodyMedium),
                        if (order.estimatedDeliveryOrPickupTime != null)
                           Text("Est. Delivery: ${Get.Utils.capitalize(order.estimatedDeliveryOrPickupTime!.toLocal().toString().substring(11,16))}", style: Get.textTheme.bodyMedium),
                      ],
                    ),
                  ),
                ),
              const SizedBox(height: 16),

              // --- Items Ordered ---
              Text("Items Ordered", style: Get.textTheme.titleLarge),
              const SizedBox(height: 8),
              ...order.items.map((item) => Card(
                margin: const EdgeInsets.only(bottom: 8),
                child: ListTile(
                  title: Text("${item.quantity} x ${item.menuItemSnapshotName}"),
                  subtitle: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      if (item.selectedCustomizationsSnapshot.isNotEmpty)
                        Text(
                          item.selectedCustomizationsSnapshot
                              .map((cs) => "${cs.groupName}: ${cs.optionName} (+\$${cs.priceAdjustment.toStringAsFixed(2)})")
                              .join(', '),
                          style: Get.textTheme.bodySmall,
                        ),
                      Text("Unit Price: \$${item.unitPrice.toStringAsFixed(2)}"),
                    ],
                  ),
                  trailing: Text("\$${item.lineTotal.toStringAsFixed(2)}", style: const TextStyle(fontWeight: FontWeight.bold)),
                ),
              )),
              const SizedBox(height: 16),

              // --- Price Summary ---
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(16.0),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text("Payment Summary", style: Get.textTheme.titleLarge),
                      const Divider(),
                      _buildPriceRow("Subtotal:", order.subtotalPrice),
                      if (order.taxesAmount > 0) _buildPriceRow("Taxes:", order.taxesAmount),
                      if (order.deliveryFeeAmount > 0) _buildPriceRow("Delivery Fee:", order.deliveryFeeAmount),
                      if (order.serviceChargeAmount > 0) _buildPriceRow("Service Charge:", order.serviceChargeAmount),
                      if (order.discountAmount > 0) _buildPriceRow("Discount:", -order.discountAmount, isDiscount: true), // Show discount as negative
                      const Divider(),
                      _buildPriceRow("Total Amount:", order.totalPrice, isTotal: true),
                      const SizedBox(height: 8),
                      Text("Payment Status: ${order.paymentStatusDisplay}", style: Get.textTheme.bodyMedium?.copyWith(fontWeight: FontWeight.w600, color: _getStatusColor(order.paymentStatus))),
                      if (order.paymentMethodSnapshot != null)
                        Text("Payment Method: ${order.paymentMethodSnapshot}", style: Get.textTheme.bodyMedium),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 16),

              // --- Order Status History ---
              Text("Order History", style: Get.textTheme.titleLarge),
              const SizedBox(height: 8),
              if (order.statusHistory.isEmpty)
                const Text("No status history available yet.")
              else
                ...order.statusHistory.map((history) => Card(
                  margin: const EdgeInsets.only(bottom: 8),
                  child: ListTile(
                    leading: Icon(_getStatusIcon(history.status), color: _getStatusColor(history.status)),
                    title: Text(history.statusDisplay, style: const TextStyle(fontWeight: FontWeight.bold)),
                    subtitle: Text(
                        "At: ${Get.Utils.capitalize(history.timestamp.toLocal().toString().substring(0, 16))}\nBy: ${history.changedByEmail ?? 'System'}\n${history.notes ?? ''}".trim()),
                    isThreeLine: (history.notes?.isNotEmpty ?? false) || (history.changedByEmail?.isNotEmpty ?? false),
                  ),
                )),
              const SizedBox(height: 20),

              // --- Cancellation Button (if applicable) ---
              Obx(() => controller.canCustomerCancel ?
                SizedBox(
                  width: double.infinity,
                  child: ElevatedButton.icon(
                    icon: controller.isCancelling.value
                        ? const SizedBox(width:18, height:18, child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2,))
                        : const Icon(Icons.cancel_outlined),
                    label: Text(controller.isCancelling.value ? "Cancelling..." : "Cancel This Order"),
                    style: ElevatedButton.styleFrom(backgroundColor: Colors.redAccent),
                    onPressed: controller.isCancelling.value ? null : controller.cancelOrder,
                  ),
                ) : const SizedBox.shrink()),

            ],
          ),
        );
      }),
    );
  }

  Widget _buildPriceRow(String label, double amount, {bool isTotal = false, bool isDiscount = false}) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 2.0),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: TextStyle(fontWeight: isTotal ? FontWeight.bold : FontWeight.normal)),
          Text(
            "${isDiscount ? '-' : ''}\$${amount.abs().toStringAsFixed(2)}",
            style: TextStyle(
              fontWeight: isTotal ? FontWeight.bold : FontWeight.normal,
              color: isDiscount ? Colors.green : null
            ),
          ),
        ],
      ),
    );
  }
}