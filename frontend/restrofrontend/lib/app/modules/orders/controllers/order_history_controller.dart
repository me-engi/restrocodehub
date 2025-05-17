import 'package:get/get.dart';
import 'package:restrofrontend/app/data/model/order_model.dart';
 // For OrderListModel, PaginatedOrdersResponse
import '../../../data/providers/order_repository.dart';
import '../../../routes/app_pages.dart'; // For navigation to order detail

class OrderHistoryController extends GetxController {
  final OrderRepository _orderRepository = Get.find<OrderRepository>();

  // --- Observable State ---
  var isLoading = true.obs; // Start with loading true for initial fetch
  var isLoadMoreError = false.obs; // For errors during "load more"
  var isMoreDataAvailable = true.obs; // To know if we can fetch more pages
  var currentPage = 1.obs;

  var orderList = <OrderListModel>[].obs; // The list of orders

  @override
  void onInit() {
    super.onInit();
    fetchOrders(isRefresh: true); // Initial fetch
  }

  Future<void> fetchOrders({bool isRefresh = false}) async {
    if (isLoading.value && !isRefresh) return; // Avoid multiple simultaneous fetches unless refreshing

    isLoadMoreError.value = false; // Reset load more error state
    if (isRefresh) {
      isLoading.value = true; // Show main loading indicator only on refresh
      currentPage.value = 1;
      orderList.clear();
      isMoreDataAvailable.value = true; // Reset pagination status
    } else if (!isMoreDataAvailable.value) {
      // No more data to load, and it's not a refresh
      return;
    }

    // For subsequent loads (not refresh), isLoading might be a separate smaller indicator
    // For now, we use the main isLoading for simplicity.

    try {
      final response = await _orderRepository.fetchOrderHistory(page: currentPage.value);

      if (response != null) {
        if (response.results.isNotEmpty) {
          orderList.addAll(response.results);
          currentPage.value++; // Increment page for next fetch
        }
        if (response.next == null || response.results.isEmpty) {
          isMoreDataAvailable.value = false;
        }
      } else {
        // Error occurred, or no response
        isMoreDataAvailable.value = false; // Assume no more data on error
        if (isRefresh) { // Only show prominent error if initial load fails
          Get.snackbar(
            "Error",
            "Could not fetch order history. Please try again.",
            snackPosition: SnackPosition.BOTTOM,
          );
        } else {
          isLoadMoreError.value = true; // Indicate load more failed
        }
      }
    } catch (e) {
      print("Error in fetchOrders: $e");
      isMoreDataAvailable.value = false;
      if (isRefresh) {
        Get.snackbar("Error", "An unexpected error occurred.", snackPosition: SnackPosition.BOTTOM);
      } else {
        isLoadMoreError.value = true;
      }
    } finally {
      if (isRefresh) {
        isLoading.value = false;
      }
      // If it was a load more action, the UI might have its own bottom loading indicator
      // independent of the main `isLoading`.
    }
  }

  Future<void> refreshOrders() async {
    await fetchOrders(isRefresh: true);
  }

  void navigateToOrderDetail(String orderId) {
    Get.toNamed(Routes.ORDER_DETAIL, arguments: orderId);
  }
}