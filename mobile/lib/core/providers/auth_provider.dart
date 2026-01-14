import 'package:flutter/foundation.dart';
import 'package:freezed_annotation/freezed_annotation.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../api/api_client.dart';
import '../error/app_error.dart';
import '../repositories/auth_repository.dart';

part 'auth_provider.freezed.dart';
part 'auth_provider.g.dart';

@freezed
class AuthState with _$AuthState {
  const factory AuthState({
    @Default(true) bool isLoading,
    @Default(false) bool isAuthenticated,
    String? userId,
    String? email,
    String? name,
    String? error,
  }) = _AuthState;
}

@riverpod
class Auth extends _$Auth {
  @override
  AuthState build() {
    // Set up callback for auth invalidation (e.g., when refresh token fails)
    final apiClient = ref.read(apiClientProvider);
    apiClient.onAuthInvalidated = () {
      if (kDebugMode) debugPrint('Auth: Session invalidated, forcing re-check');
      ref.invalidateSelf();
    };

    ref.onDispose(() {
      apiClient.onAuthInvalidated = null;
    });

    // Check auth status on build
    _checkAuth();
    return const AuthState();
  }

  Future<void> _checkAuth() async {
    final repository = ref.read(authRepositoryProvider);

    try {
      // Initialize API client with stored tokens
      await repository.initializeFromStorage();

      final isLoggedIn = await repository.isLoggedIn();
      if (isLoggedIn) {
        final userData = await repository.getUserData();
        state = AuthState(
          isLoading: false,
          isAuthenticated: true,
          userId: userData['userId'],
          email: userData['email'],
          name: userData['name'],
        );
        if (kDebugMode) debugPrint('Auth: User is logged in');
      } else {
        state = const AuthState(isLoading: false, isAuthenticated: false);
        if (kDebugMode) debugPrint('Auth: User is not logged in');
      }
    } catch (e) {
      if (kDebugMode) debugPrint('Auth: Error checking auth: $e');
      state = const AuthState(isLoading: false, isAuthenticated: false);
    }
  }

  Future<bool> login(String email, String password) async {
    state = state.copyWith(isLoading: true, error: null);

    try {
      final repository = ref.read(authRepositoryProvider);
      final response = await repository.login(email, password);

      // projectsProvider watches authProvider and will auto-reload
      state = AuthState(
        isLoading: false,
        isAuthenticated: true,
        userId: response.userId,
        email: response.email,
        name: response.name,
      );

      if (kDebugMode) debugPrint('Auth: Login successful');
      return true;
    } catch (e) {
      if (kDebugMode) debugPrint('Auth: Login failed: $e');
      state = state.copyWith(
        isLoading: false,
        error: e is AppError ? e.message : 'Login failed. Please try again.',
      );
      return false;
    }
  }

  Future<bool> register(String email, String password, String? name) async {
    state = state.copyWith(isLoading: true, error: null);

    try {
      final repository = ref.read(authRepositoryProvider);
      final response = await repository.register(email, password, name);

      // projectsProvider watches authProvider and will auto-reload
      state = AuthState(
        isLoading: false,
        isAuthenticated: true,
        userId: response.userId,
        email: response.email,
        name: response.name,
      );

      if (kDebugMode) debugPrint('Auth: Registration successful');
      return true;
    } catch (e) {
      if (kDebugMode) debugPrint('Auth: Registration failed: $e');
      state = state.copyWith(
        isLoading: false,
        error: e is AppError ? e.message : 'Registration failed. Please try again.',
      );
      return false;
    }
  }

  Future<void> logout() async {
    if (kDebugMode) debugPrint('Auth: Logging out...');

    try {
      final repository = ref.read(authRepositoryProvider);
      await repository.logout();
    } catch (e) {
      if (kDebugMode) debugPrint('Auth: Error during logout: $e');
    }

    // Update state - projectsProvider watches authProvider and will auto-rebuild
    state = const AuthState(isLoading: false, isAuthenticated: false);

    if (kDebugMode) debugPrint('Auth: Logout complete, isAuthenticated=${state.isAuthenticated}');
  }
}
