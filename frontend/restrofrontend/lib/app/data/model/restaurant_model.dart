class RestaurantModel {
  final String id;
  final String name;
  final String? slug;
  final String? city;
  final double? latitude;
  final double? longitude;
  final String? logoImage; // URL
  final bool isOperational;
  final double? distanceKm; // Annotated by API or calculated locally

  RestaurantModel({
    required this.id,
    required this.name,
    this.slug,
    this.city,
    this.latitude,
    this.longitude,
    this.logoImage,
    required this.isOperational,
    this.distanceKm,
  });

  factory RestaurantModel.fromJson(Map<String, dynamic> json) {
    return RestaurantModel(
      id: json['id'] as String,
      name: json['name'] as String,
      slug: json['slug'] as String?,
      city: json['city'] as String?,
      latitude: (json['latitude'] as num?)?.toDouble(),
      longitude: (json['longitude'] as num?)?.toDouble(),
      logoImage: json['logo_image'] as String?,
      isOperational: json['is_operational'] as bool? ?? false,
      distanceKm: (json['distance_km'] as num?)?.toDouble(),
    );
  }
}

class PaginatedRestaurantsResponse {
  final int count;
  final String? next;
  final String? previous;
  final List<RestaurantModel> results;

  PaginatedRestaurantsResponse({
    required this.count,
    this.next,
    this.previous,
    required this.results,
  });

  factory PaginatedRestaurantsResponse.fromJson(Map<String, dynamic> json) {
    return PaginatedRestaurantsResponse(
      count: json['count'] as int,
      next: json['next'] as String?,
      previous: json['previous'] as String?,
      results: (json['results'] as List<dynamic>)
          .map((e) => RestaurantModel.fromJson(e as Map<String, dynamic>))
          .toList(),
    );
  }
}