import 'package:dio/dio.dart';

/// Extract user-friendly error message from API response
String? _extractErrorMessage(dynamic data) {
  if (data == null) return null;
  if (data is! Map) return data.toString();

  final detail = data['detail'];

  // FastAPI validation errors: {"detail": [{"loc": [...], "msg": "...", "type": "..."}]}
  if (detail is List && detail.isNotEmpty) {
    final errors = detail
        .map((e) => e is Map ? e['msg'] as String? : null)
        .where((msg) => msg != null)
        .toList();
    if (errors.isNotEmpty) {
      return errors.join('. ');
    }
  }

  // Simple error: {"detail": "Error message"} or {"message": "Error message"}
  if (detail is String) return detail;
  if (data['message'] is String) return data['message'] as String;

  return null;
}

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
}

/// Creates an appropriate AppError from a DioException.
/// May return NetworkError, TokenLimitError, or other error types.
AppError appErrorFromDioException(DioException e) {
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
    final message = _extractErrorMessage(data);

    if (statusCode == 401) {
      return NetworkError(
        message ?? 'Session expired. Please log in again.',
        statusCode: statusCode,
      );
    }
    if (statusCode == 403) {
      // Check for token limit exceeded error
      if (data is Map && data['error'] == 'token_limit_exceeded') {
        return TokenLimitError(
          data['message'] as String? ??
              'Token limit exceeded. Please verify your email.',
          tokensUsed: data['tokens_used'] as int? ?? 0,
          limit: data['limit'] as int? ?? 0,
        );
      }
      return NetworkError('Access denied.', statusCode: statusCode);
    }
    if (statusCode == 422) {
      // Validation error
      return NetworkError(
        message ?? 'Invalid input. Please check your data.',
        statusCode: statusCode,
      );
    }
    return NetworkError(
      message ?? 'Server error occurred.',
      statusCode: statusCode,
      isRetryable: statusCode != null && statusCode >= 500,
    );
  }
  return const NetworkError('An unexpected error occurred.');
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

/// Token limit exceeded error (for unverified users)
class TokenLimitError extends AppError {
  final int tokensUsed;
  final int limit;

  const TokenLimitError(
    super.message, {
    required this.tokensUsed,
    required this.limit,
  });
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
