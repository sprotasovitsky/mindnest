import 'package:freezed_annotation/freezed_annotation.dart';

part 'api_key.freezed.dart';
part 'api_key.g.dart';

@freezed
sealed class ApiKey with _$ApiKey {
  const ApiKey._();
  const factory ApiKey({
    required String id,
    required String name,
    required String keyPrefix,
    required String scopes,
    required DateTime createdAt,
    DateTime? lastUsedAt,
  }) = _ApiKey;

  factory ApiKey.fromJson(Map<String, dynamic> json) => _$ApiKeyFromJson({
        'id': json['id'] ?? '',
        'name': json['name'] ?? '',
        'keyPrefix': json['key_prefix'] ?? '',
        'scopes': json['scopes'] ?? 'read',
        'createdAt': json['created_at'] ?? DateTime.now().toIso8601String(),
        'lastUsedAt': json['last_used_at'],
      });

  bool get hasWriteScope => scopes.contains('write');
  bool get isReadOnly => !hasWriteScope;
}

/// Response when creating a new API key.
/// Contains the full key which is only shown once.
@freezed
sealed class CreateApiKeyResponse with _$CreateApiKeyResponse {
  const CreateApiKeyResponse._();
  const factory CreateApiKeyResponse({
    required String id,
    required String name,
    required String key, // Full key - shown only once
    required String keyPrefix,
    required String scopes,
    required DateTime createdAt,
  }) = _CreateApiKeyResponse;

  factory CreateApiKeyResponse.fromJson(Map<String, dynamic> json) =>
      _$CreateApiKeyResponseFromJson({
        'id': json['id'] ?? '',
        'name': json['name'] ?? '',
        'key': json['key'] ?? '',
        'keyPrefix': json['key_prefix'] ?? '',
        'scopes': json['scopes'] ?? 'read',
        'createdAt': json['created_at'] ?? DateTime.now().toIso8601String(),
      });
}
