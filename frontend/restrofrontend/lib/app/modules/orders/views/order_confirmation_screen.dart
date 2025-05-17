// lib/app/modules/orders/views/order_confirmation_screen.dart
import 'package:flutter/material.dart';
import 'package:get/get.dart';
import 'package:restrofrontend/app/data/model/order_model.dart';
 // For OrderDetailModel
import '../../../routes/app_pages.dart';

class OrderConfirmationScreen extends StatelessWidget {
  const OrderConfirmationScreen({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    final OrderDetailModel? order = Get.arguments as OrderDetailModel?;

    if (order == null) {
      // Fallback if no order data is passed, though ideally this shouldn't happen
      return Scaffold(
        appBar: AppBar(title: const Text("Order Issue")),
        body: const Center(child: Text("Order details not found. Please check your order history.")),
      );
    }

    return Scaffold(
      appBar: AppBar(
        title: const Text("Order Confirmed!"),
        automaticallyImplyLeading: false, // No back button
      ),
      body: Center(
        child: Padding(
          padding: const EdgeInsets.all(20.0),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            crossAxisAlignment: CrossAxisAlignment.center,
            children: [
              const Icon(Icons.check_circle_outline_rounded, color: Colors.green, size: 100),
              const SizedBox(height: 20),
              Text(
                "Thank You!",
                style: Get.textTheme.headlineMedium?.copyWith(fontWeight: FontWeight.bold),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 10),
              Text(
                "Your order #${order.orderNumber.substring(order.orderNumber.length - 6)} has been placed successfully.",
                style: Get.textTheme.titleMedium,
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 8),
              Text(
                "Restaurant: ${order.restaurantName}",
                style: Get.textTheme.titleSmall,
                textAlign: TextAlign.center,
              ),
              if (order.estimatedDeliveryOrPickupTime != null)
                Padding(
                  padding: const EdgeInsets.only(top: 8.0),
                  child: Text(
                    "Estimated ${order.orderType == 'DELIVERY' ? 'Delivery' : 'Pickup'} Time: ${Get.Utils.capitalize(order.estimatedDeliveryOrPickupTime!.toLocal().toString().substring(11,16))}", // Format time
                    style: Get.textTheme.bodyMedium,
                    textAlign: TextAlign.center,
                  ),
                ),

              const SizedBox(height: 30),
              // Consider showing a QR code for gate pass or KDS token if applicable here
              // if (order.kdsTokenNumber != null) Text("Your Token: ${order.kdsTokenNumber}"),

              const Divider(height: 40),

              ElevatedButton.icon(
                icon: const Icon(Icons.track_changes_outlined),
                label: const Text("Track Your Order"),
                onPressed: () {
                  Get.offNamed(Routes.ORDER_DETAIL, arguments: order.id);
                },
              ),
              const SizedBox(height: 12),
              TextButton(
                onPressed: () {
                  Get.offAllNamed(Routes.HOME); // Go back to home screen
                },
                child: const Text("Continue Shopping"),
              ),
            ],
          ),
        ),
      ),
    );
  }
}