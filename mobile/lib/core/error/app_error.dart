import 'package:dio/dio.dart';

/// Base class for all application errors
sealed class AppError implements Exception {
  final String message;
  final bool isRetryable;

  const AppError(this.message, {this.isRetryable = false});

  @override
  String toString() => message;
}

/// Network-related errors
class NetworkError extends AppError {
  final int? statusCode;

  const NetworkError(super.message, {this.statusCode, super.isRetryable});

  factory NetworkError.fromDioException(DioException e) {
    if (e.type == DioExceptionType.connectionTimeout ||
        e.type == DioExceptionType.receiveTimeout) {
      return const NetworkError(
        'Connection timed out. Please try again.',
        isRetryable: true,
      );
    }
    if (e.type == DioExceptionType.connectionError) {
      return const NetworkError(
        'Unable to connect to server. Check your internet connection.',
        isRetryable: true,
      );
    }
    if (e.response != null) {
      final statusCode = e.response!.statusCode;
      final data = e.response!.data;
      final message = data is Map ? data['message'] : data?.toString();

      if (statusCode == 401) {
        return NetworkError(
          'Session expired. Please log in again.',
          statusCode: statusCode,
        );
      }
      if (statusCode == 403) {
        return NetworkError('Access denied.', statusCode: statusCode);
      }
      return NetworkError(
        message ?? 'Server error occurred.',
        statusCode: statusCode,
        isRetryable: statusCode != null && statusCode >= 500,
      );
    }
    return const NetworkError('An unexpected error occurred.');
  }
}

/// Authentication errors
class AuthError extends AppError {
  const AuthError(super.message);

  factory AuthError.invalidCredentials() =>
      const AuthError('Invalid email or password');

  factory AuthError.emailTaken() =>
      const AuthError('Email already registered');

  factory AuthError.sessionExpired() =>
      const AuthError('Session expired. Please log in again.');
}

/// Validation errors
class ValidationError extends AppError {
  final Map<String, String>? fieldErrors;

  const ValidationError(super.message, {this.fieldErrors});
}

/// Extension to extract user-friendly error messages
extension AppErrorExtension on Object {
  String toUserMessage() {
    if (this is AppError) {
      return (this as AppError).message;
    }
    final str = toString();
    if (str.contains('Invalid email or password')) {
      return 'Invalid email or password';
    }
    if (str.contains('Email already registered')) {
      return 'Email already registered';
    }
    return 'Something went wrong. Please try again.';
  }
}
