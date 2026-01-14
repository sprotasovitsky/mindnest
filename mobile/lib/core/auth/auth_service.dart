import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

import '../constants/app_config.dart';

final authServiceProvider = Provider<AuthService>((ref) {
  return AuthService();
});

class AuthService {
  final FlutterSecureStorage _storage = const FlutterSecureStorage();

  // Storage key for email verification status
  static const String _emailVerifiedKey = 'email_verified';

  Future<String?> getToken() async {
    return await _storage.read(key: AppConfig.tokenKey);
  }

  Future<String?> getRefreshToken() async {
    return await _storage.read(key: AppConfig.refreshTokenKey);
  }

  Future<DateTime?> getTokenExpiresAt() async {
    final expiresAtStr = await _storage.read(key: AppConfig.tokenExpiresAtKey);
    if (expiresAtStr == null) return null;
    return DateTime.tryParse(expiresAtStr);
  }

  Future<bool> isTokenExpired() async {
    final expiresAt = await getTokenExpiresAt();
    if (expiresAt == null) return true;
    // Consider token expired 1 minute before actual expiry for safety
    return DateTime.now().isAfter(expiresAt.subtract(const Duration(minutes: 1)));
  }

  Future<void> saveAuthData({
    required String accessToken,
    required String refreshToken,
    required int expiresIn,
    required String userId,
    required String email,
    String? name,
    bool emailVerified = false,
  }) async {
    final expiresAt = DateTime.now().add(Duration(seconds: expiresIn));

    await _storage.write(key: AppConfig.tokenKey, value: accessToken);
    await _storage.write(key: AppConfig.refreshTokenKey, value: refreshToken);
    await _storage.write(key: AppConfig.tokenExpiresAtKey, value: expiresAt.toIso8601String());
    await _storage.write(key: AppConfig.userIdKey, value: userId);
    await _storage.write(key: AppConfig.userEmailKey, value: email);
    await _storage.write(key: _emailVerifiedKey, value: emailVerified.toString());
    if (name != null) {
      await _storage.write(key: AppConfig.userNameKey, value: name);
    }
  }

  Future<void> updateAccessToken({
    required String accessToken,
    required int expiresIn,
  }) async {
    final expiresAt = DateTime.now().add(Duration(seconds: expiresIn));
    await _storage.write(key: AppConfig.tokenKey, value: accessToken);
    await _storage.write(key: AppConfig.tokenExpiresAtKey, value: expiresAt.toIso8601String());
  }

  Future<Map<String, String?>> getUserData() async {
    return {
      'userId': await _storage.read(key: AppConfig.userIdKey),
      'email': await _storage.read(key: AppConfig.userEmailKey),
      'name': await _storage.read(key: AppConfig.userNameKey),
    };
  }

  Future<bool> isEmailVerified() async {
    final value = await _storage.read(key: _emailVerifiedKey);
    return value == 'true';
  }

  Future<void> setEmailVerified(bool verified) async {
    await _storage.write(key: _emailVerifiedKey, value: verified.toString());
  }

  Future<void> clearAuth() async {
    await _storage.delete(key: AppConfig.tokenKey);
    await _storage.delete(key: AppConfig.refreshTokenKey);
    await _storage.delete(key: AppConfig.tokenExpiresAtKey);
    await _storage.delete(key: AppConfig.userIdKey);
    await _storage.delete(key: AppConfig.userEmailKey);
    await _storage.delete(key: AppConfig.userNameKey);
    await _storage.delete(key: _emailVerifiedKey);
  }

  Future<bool> isLoggedIn() async {
    final token = await getToken();
    final refreshToken = await getRefreshToken();
    // User is logged in if they have a refresh token (access token can be refreshed)
    return refreshToken != null && refreshToken.isNotEmpty;
  }

  /// Validate password strength
  static String? validatePassword(String password) {
    if (password.length < AppConfig.minPasswordLength) {
      return 'Password must be at least ${AppConfig.minPasswordLength} characters';
    }
    if (!password.contains(RegExp(r'[0-9]'))) {
      return 'Password must contain at least one digit';
    }
    if (!password.contains(RegExp(r'[a-zA-Z]'))) {
      return 'Password must contain at least one letter';
    }
    return null; // Valid
  }
}
