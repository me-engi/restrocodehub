// lib/app/modules/orders/views/checkout_screen.dart
import 'package:flutter/material.dart';
import 'package:get/get.dart';
import '../controllers/order_placement_controller.dart';
import '../controllers/cart_controller.dart'; // To display cart summary
import '../../../routes/app_pages.dart'; // For navigation

class CheckoutScreen extends GetView<OrderPlacementController> {
  const CheckoutScreen({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    final CartController cartController = Get.find<CartController>(); // To show cart summary

    return Scaffold(
      appBar: AppBar(
        title: const Text("Checkout"),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () => Get.back(),
        ),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16.0),
        child: Form(
          key: controller.orderDetailsFormKey,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // --- Order Type Selection ---
              Text("Select Order Type", style: Get.textTheme.titleLarge),
              const SizedBox(height: 8),
              Obx(() => SegmentedButton<String>(
                    segments: const <ButtonSegment<String>>[
                      ButtonSegment<String>(value: 'TAKEAWAY', label: Text('Takeaway'), icon: Icon(Icons.takeout_dining_outlined)),
                      ButtonSegment<String>(value: 'DINE_IN', label: Text('Dine-In'), icon: Icon(Icons.restaurant_outlined)),
                      ButtonSegment<String>(value: 'DELIVERY', label: Text('Delivery'), icon: Icon(Icons.delivery_dining_outlined)),
                    ],
                    selected: <String>{controller.selectedOrderType.value},
                    onSelectionChanged: (Set<String> newSelection) {
                      controller.selectedOrderType.value = newSelection.first;
                    },
                    style: SegmentedButton.styleFrom(
                        // selectedBackgroundColor: Get.theme.colorScheme.primaryContainer,
                        // selectedForegroundColor: Get.theme.colorScheme.onPrimaryContainer,
                        ),
                  )),
              const SizedBox(height: 20),

              // --- Conditional Fields based on Order Type ---
              Obx(() {
                if (controller.selectedOrderType.value == 'DINE_IN') {
                  return _buildDineInFields();
                } else if (controller.selectedOrderType.value == 'DELIVERY') {
                  return _buildDeliveryFields();
                }
                return const SizedBox.shrink(); // For Takeaway, no extra fields here initially
              }),
              const SizedBox(height: 20),

              // --- Customer Information ---
              Text("Your Information", style: Get.textTheme.titleLarge),
              const SizedBox(height: 12),
              TextFormField(
                controller: controller.customerNameController,
                decoration: const InputDecoration(labelText: "Full Name"),
                validator: (value) => (value == null || value.isEmpty) ? "Name is required" : null,
              ),
              const SizedBox(height: 12),
              TextFormField(
                controller: controller.customerPhoneController,
                decoration: const InputDecoration(labelText: "Phone Number"),
                keyboardType: TextInputType.phone,
                validator: (value) {
                  if (value == null || value.isEmpty) return "Phone number is required";
                  if (!GetUtils.isPhoneNumber(value)) return "Enter a valid phone number";
                  return null;
                },
              ),
              const SizedBox(height: 12),
              TextFormField(
                controller: controller.customerEmailController,
                decoration: const InputDecoration(labelText: "Email Address (for receipt)"),
                keyboardType: TextInputType.emailAddress,
                validator: (value) {
                  if (value == null || value.isEmpty) return "Email is required";
                  if (!GetUtils.isEmail(value)) return "Enter a valid email";
                  return null;
                },
              ),
              const SizedBox(height: 20),

              // --- Special Instructions ---
              TextFormField(
                controller: controller.specialInstructionsController,
                decoration: const InputDecoration(
                  labelText: "Special Instructions for Restaurant (Optional)",
                  hintText: "e.g., less spicy, extra napkins",
                ),
                maxLines: 3,
              ),
              const SizedBox(height: 20),

              // --- Order Summary (from CartController) ---
              Text("Order Summary", style: Get.textTheme.titleLarge),
              const SizedBox(height: 8),
              Obx(() {
                if (cartController.cart.value == null || cartController.cart.value!.items.isEmpty) {
                  return const Text("Your cart is empty.");
                }
                final cart = cartController.cart.value!;
                return Card(
                  elevation: 0,
                  color: Get.theme.colorScheme.surfaceVariant.withOpacity(0.5),
                  child: Padding(
                    padding: const EdgeInsets.all(12.0),
                    child: Column(
                      children: [
                        ...cart.items.map((item) => ListTile(
                              dense: true,
                              leading: SizedBox(width:30, child: Text("${item.quantity}x")),
                              title: Text(item.menuItemName, style: const TextStyle(fontSize: 14)),
                              trailing: Text("\$${item.lineTotal.toStringAsFixed(2)}", style: const TextStyle(fontSize: 14)),
                            )),
                        const Divider(),
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            const Text("Subtotal:", style: TextStyle(fontWeight: FontWeight.bold)),
                            Text("\$${cart.subtotalPrice.toStringAsFixed(2)}", style: const TextStyle(fontWeight: FontWeight.bold)),
                          ],
                        ),
                        // TODO: Add Taxes, Delivery Fee, Total here once calculated
                      ],
                    ),
                  ),
                );
              }),
              const SizedBox(height: 30),

              // --- Place Order Button ---
              Obx(() => ElevatedButton.icon(
                    icon: controller.isLoading.value
                        ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2))
                        : const Icon(Icons.payment_outlined), // Or Icons.check_circle_outline
                    label: Text(controller.isLoading.value ? "Placing Order..." : "Proceed to Payment / Place Order"),
                    onPressed: controller.isLoading.value || (cartController.cart.value?.items.isEmpty ?? true)
                        ? null
                        : controller.placeOrder,
                  )),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildDineInFields() {
    return TextFormField(
      controller: controller.tableNumberController,
      decoration: const InputDecoration(labelText: "Table Number (Optional)"),
      // validator: (value) => (value == null || value.isEmpty) ? "Table number is required for Dine-In" : null,
    );
  }

  Widget _buildDeliveryFields() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        TextFormField(
          controller: controller.deliveryAddress1Controller,
          decoration: const InputDecoration(labelText: "Address Line 1"),
          validator: (value) => (value == null || value.isEmpty) ? "Address Line 1 is required" : null,
        ),
        const SizedBox(height: 12),
        // TextFormField(controller: controller.deliveryAddress2Controller, decoration: InputDecoration(labelText: "Address Line 2 (Optional)")),
        // const SizedBox(height: 12),
        TextFormField(
          controller: controller.deliveryCityController,
          decoration: const InputDecoration(labelText: "City"),
          validator: (value) => (value == null || value.isEmpty) ? "City is required" : null,
        ),
        const SizedBox(height: 12),
        TextFormField(
          controller: controller.deliveryPostalCodeController,
          decoration: const InputDecoration(labelText: "Postal Code"),
          validator: (value) => (value == null || value.isEmpty) ? "Postal Code is required" : null,
        ),
        const SizedBox(height: 12),
        TextFormField(
          controller: controller.deliveryCountryController,
          decoration: const InputDecoration(labelText: "Country"),
          validator: (value) => (value == null || value.isEmpty) ? "Country is required" : null,
        ),
        // Add State/Province field if necessary
      ],
    );
  }
}