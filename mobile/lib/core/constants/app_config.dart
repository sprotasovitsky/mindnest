/// Application configuration constants
class AppConfig {
  AppConfig._();

  /// Environment name (dev, staging, prod)
  static const String environment = String.fromEnvironment(
    'ENVIRONMENT',
    defaultValue: 'dev',
  );

  /// API Configuration
  static const String apiUrl = String.fromEnvironment(
    'API_URL',
    defaultValue: 'http://10.0.2.2:8000/api',
  );

  /// Environment helpers
  static bool get isDev => environment == 'dev';
  static bool get isStaging => environment == 'staging';
  static bool get isProd => environment == 'prod';

  /// Debug logging (enabled in dev and staging)
  static bool get enableDebugLogs => !isProd;

  /// Timeouts
  static const Duration connectTimeout = Duration(seconds: 30);
  static const Duration receiveTimeout = Duration(seconds: 60);

  /// Retry Configuration
  static const int maxRetries = 3;
  static const Duration retryDelay = Duration(seconds: 1);

  /// Chat Configuration
  static const int chatHistoryLimit = 50;

  /// Storage Keys
  static const String tokenKey = 'auth_token';
  static const String refreshTokenKey = 'refresh_token';
  static const String tokenExpiresAtKey = 'token_expires_at';
  static const String userIdKey = 'user_id';
  static const String userEmailKey = 'user_email';
  static const String userNameKey = 'user_name';

  /// Password validation
  static const int minPasswordLength = 8;
  static const String passwordRequirements =
      'Password must be at least 8 characters with letters and numbers';
}
