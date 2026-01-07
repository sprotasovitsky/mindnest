import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

final apiClientProvider = Provider<ApiClient>((ref) {
  return ApiClient();
});

class ApiException implements Exception {
  final String message;
  final int? statusCode;
  final bool isRetryable;

  ApiException(this.message, {this.statusCode, this.isRetryable = false});

  @override
  String toString() => message;
}

class ApiClient {
  late final Dio _dio;
  String? _authToken;
  static const int _maxRetries = 3;
  static const Duration _retryDelay = Duration(seconds: 1);

  ApiClient() {
    _dio = Dio(
      BaseOptions(
        baseUrl: const String.fromEnvironment(
          'API_URL',
          defaultValue: 'http://10.0.2.2:8000/api',
        ),
        connectTimeout: const Duration(seconds: 30),
        receiveTimeout: const Duration(seconds: 60),
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
        // Log errors for debugging
        print('API Error: ${error.message}');
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
        if (attempts >= _maxRetries || !_isRetryable(e)) {
          throw _convertException(e);
        }
        await Future.delayed(_retryDelay * attempts);
      }
    }
  }

  bool _isRetryable(DioException e) {
    // Retry on connection errors and server errors (5xx)
    return e.type == DioExceptionType.connectionTimeout ||
        e.type == DioExceptionType.receiveTimeout ||
        e.type == DioExceptionType.connectionError ||
        (e.response?.statusCode != null && e.response!.statusCode! >= 500);
  }

  ApiException _convertException(DioException e) {
    if (e.type == DioExceptionType.connectionTimeout ||
        e.type == DioExceptionType.receiveTimeout) {
      return ApiException('Connection timed out. Please try again.',
          isRetryable: true);
    }
    if (e.type == DioExceptionType.connectionError) {
      return ApiException(
          'Unable to connect to server. Check your internet connection.',
          isRetryable: true);
    }
    if (e.response != null) {
      final statusCode = e.response!.statusCode;
      final data = e.response!.data;
      final message = data is Map ? data['message'] : data?.toString();
      if (statusCode == 401) {
        return ApiException('Session expired. Please log in again.',
            statusCode: statusCode);
      }
      if (statusCode == 403) {
        return ApiException('Access denied.', statusCode: statusCode);
      }
      return ApiException(message ?? 'Server error occurred.',
          statusCode: statusCode, isRetryable: statusCode! >= 500);
    }
    return ApiException('An unexpected error occurred.');
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

  Future<Map<String, dynamic>> register(String email, String password, String? name) async {
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

  Future<Map<String, dynamic>> createProject(String name, String? description) async {
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

  Future<Map<String, dynamic>> updateProject(String projectId, {String? name, String? description}) async {
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

  Future<Map<String, dynamic>> addProjectMember(String projectId, String email) async {
    return _retryRequest(() async {
      final response = await _dio.post(
        '/projects/$projectId/members',
        data: {'email': email},
      );
      return response.data as Map<String, dynamic>;
    });
  }

  // Chat history endpoint
  Future<Map<String, dynamic>> getChatHistory(String projectId, {int limit = 50}) async {
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
