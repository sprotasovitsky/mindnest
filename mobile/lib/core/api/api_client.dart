import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

final apiClientProvider = Provider<ApiClient>((ref) {
  return ApiClient();
});

class ApiClient {
  late final Dio _dio;

  ApiClient() {
    _dio = Dio(
      BaseOptions(
        baseUrl: const String.fromEnvironment(
          'API_URL',
          defaultValue: 'http://localhost:8080/api',
        ),
        connectTimeout: const Duration(seconds: 30),
        receiveTimeout: const Duration(seconds: 30),
        headers: {
          'Content-Type': 'application/json',
        },
      ),
    );

    _dio.interceptors.add(LogInterceptor(
      requestBody: true,
      responseBody: true,
    ));
  }

  Future<Map<String, dynamic>> chat(String message, {String? projectId}) async {
    final response = await _dio.post(
      '/chat',
      data: {
        'message': message,
        if (projectId != null) 'projectId': projectId,
      },
    );
    return response.data as Map<String, dynamic>;
  }

  Future<List<dynamic>> getProjects() async {
    final response = await _dio.get('/projects');
    return response.data as List<dynamic>;
  }
}
