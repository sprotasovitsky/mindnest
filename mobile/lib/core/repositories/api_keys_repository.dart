import 'package:dio/dio.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../api/api_client.dart';
import '../error/app_error.dart';
import '../models/api_key.dart';

part 'api_keys_repository.g.dart';

/// Repository for API key operations
abstract class ApiKeysRepository {
  Future<List<ApiKey>> getApiKeys();
  Future<CreateApiKeyResponse> createApiKey(String name, String scopes);
  Future<void> revokeApiKey(String keyId);
}

class ApiKeysRepositoryImpl implements ApiKeysRepository {
  final ApiClient _apiClient;

  ApiKeysRepositoryImpl(this._apiClient);

  @override
  Future<List<ApiKey>> getApiKeys() async {
    try {
      final response = await _apiClient.getApiKeys();
      return response.map((json) => ApiKey.fromJson(json)).toList();
    } on DioException catch (e) {
      throw appErrorFromDioException(e);
    }
  }

  @override
  Future<CreateApiKeyResponse> createApiKey(String name, String scopes) async {
    try {
      final response = await _apiClient.createApiKey(name, scopes);
      return CreateApiKeyResponse.fromJson(response);
    } on DioException catch (e) {
      throw appErrorFromDioException(e);
    }
  }

  @override
  Future<void> revokeApiKey(String keyId) async {
    try {
      await _apiClient.revokeApiKey(keyId);
    } on DioException catch (e) {
      throw appErrorFromDioException(e);
    }
  }
}

@riverpod
ApiKeysRepository apiKeysRepository(Ref ref) {
  final apiClient = ref.watch(apiClientProvider);
  return ApiKeysRepositoryImpl(apiClient);
}
