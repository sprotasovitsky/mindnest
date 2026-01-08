import 'dart:developer' as developer;

/// Application logger using dart:developer
///
/// Usage:
/// ```dart
/// AppLogger.debug('Debug message');
/// AppLogger.info('Info message');
/// AppLogger.warning('Warning message');
/// AppLogger.error('Error message', error: e, stackTrace: st);
/// ```
class AppLogger {
  static const String _name = 'MindNest';

  /// Log debug message
  static void debug(String message, {String? tag}) {
    developer.log(
      message,
      name: tag ?? _name,
      level: 500, // FINE
    );
  }

  /// Log info message
  static void info(String message, {String? tag}) {
    developer.log(
      message,
      name: tag ?? _name,
      level: 800, // INFO
    );
  }

  /// Log warning message
  static void warning(String message, {String? tag}) {
    developer.log(
      message,
      name: tag ?? _name,
      level: 900, // WARNING
    );
  }

  /// Log error message with optional error object and stack trace
  static void error(
    String message, {
    Object? error,
    StackTrace? stackTrace,
    String? tag,
  }) {
    developer.log(
      message,
      name: tag ?? _name,
      level: 1000, // SEVERE
      error: error,
      stackTrace: stackTrace,
    );
  }
}
