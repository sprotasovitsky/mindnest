import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
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
  Future<bool> isEmailVerified();
  Future<String?> getToken();
  Future<String?> getRefreshToken();
  Future<Map<String, String?>> getUserData();
  Future<void> initializeFromStorage();
  Future<void> verifyEmail(String token);
  Future<void> resendVerification(String email);
  Future<User> getCurrentUser();

  // Password reset
  Future<void> requestPasswordReset(String email);
  Future<String> verifyResetCode(String email, String code);
  Future<void> resetPassword(String resetToken, String newPassword);

  // Password change
  Future<void> changePassword(String currentPassword, String newPassword);

  // Social login
  Future<AuthResponse> socialLogin({
    required String provider,
    required String idToken,
    String? name,
  });

  // Account deletion
  Future<void> deleteAccount({String? password});
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
      throw appErrorFromDioException(e);
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
      throw appErrorFromDioException(e);
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
        emailVerified: authResponse.emailVerified,
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
  Future<bool> isEmailVerified() => _authService.isEmailVerified();

  @override
  Future<String?> getToken() => _authService.getToken();

  @override
  Future<String?> getRefreshToken() => _authService.getRefreshToken();

  @override
  Future<Map<String, String?>> getUserData() => _authService.getUserData();

  @override
  Future<void> verifyEmail(String token) async {
    try {
      await _apiClient.verifyEmail(token);
      await _authService.setEmailVerified(true);
    } on DioException catch (e) {
      throw appErrorFromDioException(e);
    } catch (e) {
      // Storage or other non-network errors
      throw NetworkError('Verification failed: ${e.toString()}');
    }
  }

  @override
  Future<void> resendVerification(String email) async {
    try {
      await _apiClient.resendVerification(email);
    } on DioException catch (e) {
      throw appErrorFromDioException(e);
    }
  }

  @override
  Future<User> getCurrentUser() async {
    try {
      final response = await _apiClient.getCurrentUser();
      final user = User.fromJson(response);
      // Update local email verified status
      await _authService.setEmailVerified(user.emailVerified);
      return user;
    } on DioException catch (e) {
      throw appErrorFromDioException(e);
    }
  }

  @override
  Future<void> requestPasswordReset(String email) async {
    try {
      await _apiClient.requestPasswordReset(email);
    } on DioException catch (e) {
      throw appErrorFromDioException(e);
    }
  }

  @override
  Future<String> verifyResetCode(String email, String code) async {
    try {
      final response = await _apiClient.verifyResetCode(email, code);
      return response['reset_token'] as String;
    } on DioException catch (e) {
      throw appErrorFromDioException(e);
    }
  }

  @override
  Future<void> resetPassword(String resetToken, String newPassword) async {
    try {
      await _apiClient.resetPassword(resetToken, newPassword);
    } on DioException catch (e) {
      throw appErrorFromDioException(e);
    }
  }

  @override
  Future<void> changePassword(
      String currentPassword, String newPassword) async {
    try {
      await _apiClient.changePassword(currentPassword, newPassword);
    } on DioException catch (e) {
      throw appErrorFromDioException(e);
    }
  }

  @override
  Future<AuthResponse> socialLogin({
    required String provider,
    required String idToken,
    String? name,
  }) async {
    try {
      final response = await _apiClient.socialLogin(
        provider: provider,
        idToken: idToken,
        name: name,
      );
      return await _processAuthResponse(response);
    } on DioException catch (e) {
      throw appErrorFromDioException(e);
    }
  }

  @override
  Future<void> deleteAccount({String? password}) async {
    try {
      await _apiClient.deleteAccount(password: password);
      await _authService.clearAuth();
    } on DioException catch (e) {
      throw appErrorFromDioException(e);
    }
  }
}

@riverpod
AuthRepository authRepository(Ref ref) {
  final apiClient = ref.watch(apiClientProvider);
  final authService = ref.watch(authServiceProvider);
  return AuthRepositoryImpl(apiClient, authService);
}
