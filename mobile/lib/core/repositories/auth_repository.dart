import 'package:dio/dio.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../api/api_client.dart';
import '../auth/auth_service.dart';
import '../error/app_error.dart';
import '../models/user.dart';

part 'auth_repository.g.dart';

/// Repository for authentication operations
abstract class AuthRepository {
  Future<AuthResponse> login(String email, String password);
  Future<AuthResponse> register(String email, String password, String? name);
  Future<void> logout();
  Future<bool> isLoggedIn();
  Future<String?> getToken();
  Future<Map<String, String?>> getUserData();
}

class AuthRepositoryImpl implements AuthRepository {
  final ApiClient _apiClient;
  final AuthService _authService;

  AuthRepositoryImpl(this._apiClient, this._authService);

  @override
  Future<AuthResponse> login(String email, String password) async {
    try {
      final response = await _apiClient.login(email, password);
      final authResponse = AuthResponse.fromJson(response);

      await _authService.saveAuthData(
        token: authResponse.token,
        userId: authResponse.userId,
        email: authResponse.email,
        name: authResponse.name,
      );
      _apiClient.setAuthToken(authResponse.token);

      return authResponse;
    } on DioException catch (e) {
      throw NetworkError.fromDioException(e);
    }
  }

  @override
  Future<AuthResponse> register(
      String email, String password, String? name) async {
    try {
      final response = await _apiClient.register(email, password, name);
      final authResponse = AuthResponse.fromJson(response);

      await _authService.saveAuthData(
        token: authResponse.token,
        userId: authResponse.userId,
        email: authResponse.email,
        name: authResponse.name,
      );
      _apiClient.setAuthToken(authResponse.token);

      return authResponse;
    } on DioException catch (e) {
      throw NetworkError.fromDioException(e);
    }
  }

  @override
  Future<void> logout() async {
    await _authService.clearAuth();
    _apiClient.clearAuthToken();
  }

  @override
  Future<bool> isLoggedIn() => _authService.isLoggedIn();

  @override
  Future<String?> getToken() => _authService.getToken();

  @override
  Future<Map<String, String?>> getUserData() => _authService.getUserData();
}

@riverpod
AuthRepository authRepository(AuthRepositoryRef ref) {
  final apiClient = ref.watch(apiClientProvider);
  final authService = ref.watch(authServiceProvider);
  return AuthRepositoryImpl(apiClient, authService);
}
