import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../constants/app_config.dart';
import '../utils/logger.dart';

final apiClientProvider = Provider<ApiClient>((ref) {
  return ApiClient();
});

class ApiClient {
  late final Dio _dio;
  String? _authToken;

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

    _dio.interceptors.add(LogInterceptor(
      requestBody: true,
      responseBody: true,
    ));

    _dio.interceptors.add(InterceptorsWrapper(
      onRequest: (options, handler) {
        if (_authToken != null) {
          options.headers['Authorization'] = 'Bearer $_authToken';
        }
        return handler.next(options);
      },
      onError: (error, handler) {
        AppLogger.error(
          'API Error: ${error.message}',
          error: error,
          tag: 'ApiClient',
        );
        return handler.next(error);
      },
    ));
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

  void clearAuthToken() {
    _authToken = null;
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
}
