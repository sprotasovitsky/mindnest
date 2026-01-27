import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../constants/app_config.dart';
import '../utils/logger.dart';

final apiClientProvider = Provider<ApiClient>((ref) {
  return ApiClient();
});

class ApiClient {
  late final Dio _dio;
  String? _authToken;
  String? _refreshToken;
  bool _isRefreshing = false;

  // Callback to update tokens in storage (set by repository)
  Future<void> Function(String accessToken, int expiresIn)? onTokenRefreshed;
  Future<void> Function()? onRefreshFailed;
  // Callback to notify auth provider when auth is invalidated
  VoidCallback? onAuthInvalidated;

  ApiClient() {
    _dio = Dio(
      BaseOptions(
        baseUrl: AppConfig.apiUrl,
        connectTimeout: AppConfig.connectTimeout,
        receiveTimeout: AppConfig.receiveTimeout,
        headers: {
          'Content-Type': 'application/json',
        },
      ),
    );

    // Minimal logging in debug mode - only response status
    if (kDebugMode) {
      _dio.interceptors.add(LogInterceptor(
        request: false, // Don't log request info
        requestBody: false, // Never log request body - may contain passwords
        requestHeader: false,
        responseBody: false, // Don't log response body - may be large
        responseHeader: false,
        error: true, // Only log errors
        logPrint: (msg) => debugPrint('API: $msg'),
      ));
    }

    _dio.interceptors.add(InterceptorsWrapper(
      onRequest: (options, handler) {
        if (_authToken != null) {
          options.headers['Authorization'] = 'Bearer $_authToken';
        }
        return handler.next(options);
      },
      onError: (error, handler) async {
        // Handle 401 errors by refreshing token
        if (error.response?.statusCode == 401 && _refreshToken != null && !_isRefreshing) {
          try {
            final refreshed = await _refreshAccessToken();
            if (refreshed) {
              // Retry the original request with new token
              final opts = error.requestOptions;
              opts.headers['Authorization'] = 'Bearer $_authToken';
              final response = await _dio.fetch(opts);
              return handler.resolve(response);
            }
          } catch (e) {
            // Don't log full error - may contain sensitive data
            AppLogger.error('Token refresh failed: ${e.runtimeType}', tag: 'ApiClient');
          }
        }

        // Log error without request data (may contain passwords)
        AppLogger.error(
          'API Error: ${error.response?.statusCode ?? 'unknown'} ${error.message}',
          tag: 'ApiClient',
        );
        return handler.next(error);
      },
    ));
  }

  Future<bool> _refreshAccessToken() async {
    if (_refreshToken == null || _isRefreshing) return false;

    _isRefreshing = true;
    try {
      final response = await _dio.post(
        '/auth/refresh',
        data: {'refresh_token': _refreshToken},
        options: Options(
          headers: {'Authorization': null}, // Don't send expired token
        ),
      );

      final data = response.data as Map<String, dynamic>;
      _authToken = data['access_token'] as String;
      final expiresIn = data['expires_in'] as int;

      // Notify repository to save new token
      if (onTokenRefreshed != null) {
        await onTokenRefreshed!(_authToken!, expiresIn);
      }

      AppLogger.debug('Token refreshed successfully', tag: 'ApiClient');
      return true;
    } catch (e) {
      AppLogger.error('Failed to refresh token', error: e, tag: 'ApiClient');
      // Notify about refresh failure (will trigger logout)
      if (onRefreshFailed != null) {
        await onRefreshFailed!();
      }
      return false;
    } finally {
      _isRefreshing = false;
    }
  }

  Future<T> _retryRequest<T>(Future<T> Function() request) async {
    int attempts = 0;
    while (true) {
      try {
        attempts++;
        return await request();
      } on DioException catch (e) {
        if (attempts >= AppConfig.maxRetries || !_isRetryable(e)) {
          rethrow;
        }
        await Future.delayed(AppConfig.retryDelay * attempts);
      }
    }
  }

  bool _isRetryable(DioException e) {
    return e.type == DioExceptionType.connectionTimeout ||
        e.type == DioExceptionType.receiveTimeout ||
        e.type == DioExceptionType.connectionError ||
        (e.response?.statusCode != null && e.response!.statusCode! >= 500);
  }

  void setAuthToken(String token) {
    _authToken = token;
  }

  void setRefreshToken(String token) {
    _refreshToken = token;
  }

  void clearAuthToken() {
    _authToken = null;
    _refreshToken = null;
  }

  // Auth endpoints
  Future<Map<String, dynamic>> login(String email, String password) async {
    final response = await _dio.post(
      '/auth/login',
      data: {
        'email': email,
        'password': password,
      },
    );
    return response.data as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> register(
      String email, String password, String? name) async {
    final response = await _dio.post(
      '/auth/register',
      data: {
        'email': email,
        'password': password,
        if (name != null) 'name': name,
      },
    );
    return response.data as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> refreshToken(String refreshToken) async {
    final response = await _dio.post(
      '/auth/refresh',
      data: {'refresh_token': refreshToken},
    );
    return response.data as Map<String, dynamic>;
  }

  // Email verification endpoints
  Future<Map<String, dynamic>> verifyEmail(String token) async {
    final response = await _dio.post(
      '/auth/verify-email',
      data: {'token': token},
    );
    return response.data as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> resendVerification(String email) async {
    final response = await _dio.post(
      '/auth/resend-verification',
      data: {'email': email},
    );
    return response.data as Map<String, dynamic>;
  }

  // Get current user info (with verification status)
  Future<Map<String, dynamic>> getCurrentUser() async {
    final response = await _dio.get('/auth/me');
    return response.data as Map<String, dynamic>;
  }

  // Update user profile
  Future<Map<String, dynamic>> updateProfile({required String name}) async {
    final response = await _dio.patch(
      '/auth/me',
      data: {'name': name},
    );
    return response.data as Map<String, dynamic>;
  }

  // Password reset endpoints
  Future<Map<String, dynamic>> requestPasswordReset(String email) async {
    final response = await _dio.post(
      '/auth/request-password-reset',
      data: {'email': email},
    );
    return response.data as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> verifyResetCode(
      String email, String code) async {
    final response = await _dio.post(
      '/auth/verify-reset-code',
      data: {'email': email, 'code': code},
    );
    return response.data as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> resetPassword(
      String resetToken, String newPassword) async {
    final response = await _dio.post(
      '/auth/reset-password',
      data: {'reset_token': resetToken, 'new_password': newPassword},
    );
    return response.data as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> changePassword(
      String currentPassword, String newPassword) async {
    final response = await _dio.post(
      '/auth/change-password',
      data: {
        'current_password': currentPassword,
        'new_password': newPassword,
      },
    );
    return response.data as Map<String, dynamic>;
  }

  // Social login
  Future<Map<String, dynamic>> socialLogin({
    required String provider,
    required String idToken,
    String? name,
    bool isAccessToken = false,
  }) async {
    final response = await _dio.post(
      '/auth/social',
      data: {
        'provider': provider,
        'id_token': idToken,
        if (name != null) 'name': name,
        if (isAccessToken) 'is_access_token': true,
      },
    );
    return response.data as Map<String, dynamic>;
  }

  // Delete account
  Future<void> deleteAccount({String? password}) async {
    await _dio.delete(
      '/auth/account',
      data: {
        if (password != null) 'password': password,
      },
    );
  }

  // Chat endpoints
  Future<Map<String, dynamic>> chat(String message, {String? projectId}) async {
    return _retryRequest(() async {
      final response = await _dio.post(
        '/chat',
        data: {
          'message': message,
          if (projectId != null) 'projectId': projectId,
        },
      );
      return response.data as Map<String, dynamic>;
    });
  }

  // Project endpoints
  Future<List<dynamic>> getProjects() async {
    return _retryRequest(() async {
      final response = await _dio.get('/projects');
      return response.data as List<dynamic>;
    });
  }

  Future<Map<String, dynamic>> createProject(
      String name, String? description) async {
    return _retryRequest(() async {
      final response = await _dio.post(
        '/projects',
        data: {
          'name': name,
          if (description != null) 'description': description,
        },
      );
      return response.data as Map<String, dynamic>;
    });
  }

  Future<Map<String, dynamic>> updateProject(String projectId,
      {String? name, String? description}) async {
    return _retryRequest(() async {
      final response = await _dio.patch(
        '/projects/$projectId',
        data: {
          if (name != null) 'name': name,
          if (description != null) 'description': description,
        },
      );
      return response.data as Map<String, dynamic>;
    });
  }

  // Members endpoints
  Future<List<dynamic>> getProjectMembers(String projectId) async {
    return _retryRequest(() async {
      final response = await _dio.get('/projects/$projectId/members');
      return response.data as List<dynamic>;
    });
  }

  Future<Map<String, dynamic>> addProjectMember(
      String projectId, String email) async {
    return _retryRequest(() async {
      final response = await _dio.post(
        '/projects/$projectId/members',
        data: {'email': email},
      );
      return response.data as Map<String, dynamic>;
    });
  }

  // Chat history endpoint
  Future<Map<String, dynamic>> getChatHistory(String projectId,
      {int limit = 50}) async {
    return _retryRequest(() async {
      final response = await _dio.get(
        '/chat/history',
        queryParameters: {
          'project_id': projectId,
          'limit': limit,
        },
      );
      return response.data as Map<String, dynamic>;
    });
  }

  // API Keys endpoints
  Future<List<dynamic>> getApiKeys() async {
    return _retryRequest(() async {
      final response = await _dio.get('/api-keys');
      final data = response.data as Map<String, dynamic>;
      return data['keys'] as List<dynamic>;
    });
  }

  Future<Map<String, dynamic>> createApiKey(String name, String scopes) async {
    return _retryRequest(() async {
      final response = await _dio.post(
        '/api-keys',
        data: {
          'name': name,
          'scopes': scopes,
        },
      );
      return response.data as Map<String, dynamic>;
    });
  }

  Future<void> revokeApiKey(String keyId) async {
    return _retryRequest(() async {
      await _dio.delete('/api-keys/$keyId');
    });
  }
}
