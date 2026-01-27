// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'api_key.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

_ApiKey _$ApiKeyFromJson(Map<String, dynamic> json) => _ApiKey(
  id: json['id'] as String,
  name: json['name'] as String,
  keyPrefix: json['keyPrefix'] as String,
  scopes: json['scopes'] as String,
  createdAt: DateTime.parse(json['createdAt'] as String),
  lastUsedAt: json['lastUsedAt'] == null
      ? null
      : DateTime.parse(json['lastUsedAt'] as String),
);

Map<String, dynamic> _$ApiKeyToJson(_ApiKey instance) => <String, dynamic>{
  'id': instance.id,
  'name': instance.name,
  'keyPrefix': instance.keyPrefix,
  'scopes': instance.scopes,
  'createdAt': instance.createdAt.toIso8601String(),
  'lastUsedAt': instance.lastUsedAt?.toIso8601String(),
};

_CreateApiKeyResponse _$CreateApiKeyResponseFromJson(
  Map<String, dynamic> json,
) => _CreateApiKeyResponse(
  id: json['id'] as String,
  name: json['name'] as String,
  key: json['key'] as String,
  keyPrefix: json['keyPrefix'] as String,
  scopes: json['scopes'] as String,
  createdAt: DateTime.parse(json['createdAt'] as String),
);

Map<String, dynamic> _$CreateApiKeyResponseToJson(
  _CreateApiKeyResponse instance,
) => <String, dynamic>{
  'id': instance.id,
  'name': instance.name,
  'key': instance.key,
  'keyPrefix': instance.keyPrefix,
  'scopes': instance.scopes,
  'createdAt': instance.createdAt.toIso8601String(),
};
