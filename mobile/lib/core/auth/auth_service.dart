import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

import '../constants/app_config.dart';

final authServiceProvider = Provider<AuthService>((ref) {
  return AuthService();
});

class AuthService {
  final FlutterSecureStorage _storage = const FlutterSecureStorage();

  Future<String?> getToken() async {
    return await _storage.read(key: AppConfig.tokenKey);
  }

  Future<void> saveAuthData({
    required String token,
    required String userId,
    required String email,
    String? name,
  }) async {
    await _storage.write(key: AppConfig.tokenKey, value: token);
    await _storage.write(key: AppConfig.userIdKey, value: userId);
    await _storage.write(key: AppConfig.userEmailKey, value: email);
    if (name != null) {
      await _storage.write(key: AppConfig.userNameKey, value: name);
    }
  }

  Future<Map<String, String?>> getUserData() async {
    return {
      'userId': await _storage.read(key: AppConfig.userIdKey),
      'email': await _storage.read(key: AppConfig.userEmailKey),
      'name': await _storage.read(key: AppConfig.userNameKey),
    };
  }

  Future<void> clearAuth() async {
    await _storage.delete(key: AppConfig.tokenKey);
    await _storage.delete(key: AppConfig.userIdKey);
    await _storage.delete(key: AppConfig.userEmailKey);
    await _storage.delete(key: AppConfig.userNameKey);
  }

  Future<bool> isLoggedIn() async {
    final token = await getToken();
    return token != null && token.isNotEmpty;
  }
}
