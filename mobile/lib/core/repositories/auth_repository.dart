import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
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
  Future<String?> getRefreshToken();
  Future<Map<String, String?>> getUserData();
  Future<void> initializeFromStorage();
}

class AuthRepositoryImpl implements AuthRepository {
  final ApiClient _apiClient;
  final AuthService _authService;

  AuthRepositoryImpl(this._apiClient, this._authService) {
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
    await logout();
    _apiClient.onAuthInvalidated?.call();
  }

  @override
  Future<void> initializeFromStorage() async {
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
      return await _processAuthResponse(response);
    } on DioException catch (e) {
      throw NetworkError.fromDioException(e);
    }
  }

  @override
  Future<AuthResponse> register(String email, String password, String? name) async {
    // Client-side password validation
    final validationError = AuthService.validatePassword(password);
    if (validationError != null) {
      throw ValidationError(validationError);
    }

    try {
      final response = await _apiClient.register(email, password, name);
      return await _processAuthResponse(response);
    } on DioException catch (e) {
      throw NetworkError.fromDioException(e);
    }
  }

  /// Process successful auth response - parse JSON and save tokens
  Future<AuthResponse> _processAuthResponse(Map<String, dynamic> response) async {
    // Parse response
    final AuthResponse authResponse;
    try {
      authResponse = AuthResponse.fromJson(response);
    } catch (e) {
      if (kDebugMode) {
        debugPrint('Auth: Failed to parse response: $e');
        debugPrint('Auth: Response was: $response');
      }
      throw const AuthError('Invalid server response');
    }

    // Save to secure storage
    try {
      await _authService.saveAuthData(
        accessToken: authResponse.accessToken,
        refreshToken: authResponse.refreshToken,
        expiresIn: authResponse.expiresIn,
        userId: authResponse.userId,
        email: authResponse.email,
        name: authResponse.name,
      );
    } catch (e) {
      if (kDebugMode) {
        debugPrint('Auth: Failed to save to secure storage: $e');
      }
      throw const AuthError('Failed to save credentials');
    }

    // Set tokens in API client
    _apiClient.setAuthToken(authResponse.accessToken);
    _apiClient.setRefreshToken(authResponse.refreshToken);

    return authResponse;
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
  Future<String?> getRefreshToken() => _authService.getRefreshToken();

  @override
  Future<Map<String, String?>> getUserData() => _authService.getUserData();
}

@riverpod
AuthRepository authRepository(AuthRepositoryRef ref) {
  final apiClient = ref.watch(apiClientProvider);
  final authService = ref.watch(authServiceProvider);
  return AuthRepositoryImpl(apiClient, authService);
}
