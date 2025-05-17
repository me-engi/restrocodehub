class UserModel {
  final String id;
  final String email;
  final String? name;
  final String? role;
  final String? tenantId;
  final String? tenantName;
  // Add other fields as needed from your UserSerializer response

  UserModel({
    required this.id,
    required this.email,
    this.name,
    this.role,
    this.tenantId,
    this.tenantName,
  });

  factory UserModel.fromJson(Map<String, dynamic> json) {
    return UserModel(
      id: json['id'] as String,
      email: json['email'] as String,
      name: json['name'] as String?,
      role: json['role'] as String?,
      tenantId: json['tenant'] as String?, // Assuming tenant ID is under 'tenant' key
      tenantName: json['tenant_name'] as String?,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'email': email,
      'name': name,
      'role': role,
      'tenant': tenantId,
      'tenant_name': tenantName,
    };
  }
}