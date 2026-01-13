import 'package:dio/dio.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../api/api_client.dart';
import '../auth/auth_service.dart';
import '../error/app_error.dart';
import '../models/user.dart';

part 'auth_repository.g.dart';

/// Password validation error
class PasswordValidationError implements Exception {
  final String message;
  PasswordValidationError(this.message);

  @override
  String toString() => message;
}

/// Repository for authentication operations
abstract class AuthRepository {
  Future<AuthResponse> login(String email, String password);
  Future<AuthResponse> register(String email, String password, String? name);
  Future<void> logout();
  Future<bool> isLoggedIn();
  Future<String?> getToken();
  Future<Map<String, String?>> getUserData();
  Future<void> initializeFromStorage();
}

class AuthRepositoryImpl implements AuthRepository {
  final ApiClient _apiClient;
  final AuthService _authService;

  AuthRepositoryImpl(this._apiClient, this._authService) {
    // Set up token refresh callbacks
    _apiClient.onTokenRefreshed = _onTokenRefreshed;
    _apiClient.onRefreshFailed = _onRefreshFailed;
  }

  Future<void> _onTokenRefreshed(String accessToken, int expiresIn) async {
    await _authService.updateAccessToken(
      accessToken: accessToken,
      expiresIn: expiresIn,
    );
  }

  Future<void> _onRefreshFailed() async {
    // Clear auth data and notify app to redirect to login
    await logout();
  }

  @override
  Future<void> initializeFromStorage() async {
    // Load tokens from storage and set them in API client
    final token = await _authService.getToken();
    final refreshToken = await _authService.getRefreshToken();

    if (token != null) {
      _apiClient.setAuthToken(token);
    }
    if (refreshToken != null) {
      _apiClient.setRefreshToken(refreshToken);
    }
  }

  @override
  Future<AuthResponse> login(String email, String password) async {
    try {
      final response = await _apiClient.login(email, password);
      final authResponse = AuthResponse.fromJson(response);

      await _authService.saveAuthData(
        accessToken: authResponse.accessToken,
        refreshToken: authResponse.refreshToken,
        expiresIn: authResponse.expiresIn,
        userId: authResponse.userId,
        email: authResponse.email,
        name: authResponse.name,
      );
      _apiClient.setAuthToken(authResponse.accessToken);
      _apiClient.setRefreshToken(authResponse.refreshToken);

      return authResponse;
    } on DioException catch (e) {
      throw NetworkError.fromDioException(e);
    }
  }

  @override
  Future<AuthResponse> register(
      String email, String password, String? name) async {
    // Validate password on client side
    final validationError = AuthService.validatePassword(password);
    if (validationError != null) {
      throw PasswordValidationError(validationError);
    }

    try {
      final response = await _apiClient.register(email, password, name);
      final authResponse = AuthResponse.fromJson(response);

      await _authService.saveAuthData(
        accessToken: authResponse.accessToken,
        refreshToken: authResponse.refreshToken,
        expiresIn: authResponse.expiresIn,
        userId: authResponse.userId,
        email: authResponse.email,
        name: authResponse.name,
      );
      _apiClient.setAuthToken(authResponse.accessToken);
      _apiClient.setRefreshToken(authResponse.refreshToken);

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
