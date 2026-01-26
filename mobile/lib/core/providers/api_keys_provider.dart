import 'package:freezed_annotation/freezed_annotation.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../error/app_error.dart';
import '../models/api_key.dart';
import '../repositories/api_keys_repository.dart';

part 'api_keys_provider.freezed.dart';
part 'api_keys_provider.g.dart';

@freezed
sealed class ApiKeysState with _$ApiKeysState {
  const factory ApiKeysState({
    @Default(false) bool isLoading,
    @Default([]) List<ApiKey> keys,
    String? error,
    /// The newly created key (full key, shown once)
    CreateApiKeyResponse? newKey,
  }) = _ApiKeysState;
}

@riverpod
class ApiKeys extends _$ApiKeys {
  @override
  ApiKeysState build() {
    return const ApiKeysState();
  }

  Future<void> loadKeys() async {
    state = state.copyWith(isLoading: true, error: null);
    try {
      final repository = ref.read(apiKeysRepositoryProvider);
      final keys = await repository.getApiKeys();
      state = state.copyWith(
        isLoading: false,
        keys: keys,
      );
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        error: e.toUserMessage(),
      );
    }
  }

  Future<bool> createKey(String name, {bool writeAccess = false}) async {
    state = state.copyWith(isLoading: true, error: null, newKey: null);
    try {
      final repository = ref.read(apiKeysRepositoryProvider);
      final scopes = writeAccess ? 'read,write' : 'read';
      final newKey = await repository.createApiKey(name, scopes);

      // Add the new key to the list (without the full key)
      final apiKey = ApiKey(
        id: newKey.id,
        name: newKey.name,
        keyPrefix: newKey.keyPrefix,
        scopes: newKey.scopes,
        createdAt: newKey.createdAt,
      );

      state = state.copyWith(
        isLoading: false,
        keys: [apiKey, ...state.keys],
        newKey: newKey, // Keep full key for display
      );
      return true;
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        error: e.toUserMessage(),
      );
      return false;
    }
  }

  Future<bool> revokeKey(String keyId) async {
    try {
      final repository = ref.read(apiKeysRepositoryProvider);
      await repository.revokeApiKey(keyId);

      // Remove from list
      state = state.copyWith(
        keys: state.keys.where((k) => k.id != keyId).toList(),
      );
      return true;
    } catch (e) {
      state = state.copyWith(error: e.toUserMessage());
      return false;
    }
  }

  void clearNewKey() {
    state = state.copyWith(newKey: null);
  }

  void clearError() {
    state = state.copyWith(error: null);
  }
}
