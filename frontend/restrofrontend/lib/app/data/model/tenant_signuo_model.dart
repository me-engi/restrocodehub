// You might not need a complex model if the response is simple
// For example, if the backend just returns a success message and IDs
class TenantSignupResponseModel {
  final String message;
  final String? userId; // From your Django backend
  final String? tenantId; // From your Django backend

  TenantSignupResponseModel({required this.message, this.userId, this.tenantId});

  factory TenantSignupResponseModel.fromJson(Map<String, dynamic> json) {
    return TenantSignupResponseModel(
      message: json['message'] as String,
      userId: json['user_id'] as String?,
      tenantId: json['tenant_id'] as String?,
    );
  }
}