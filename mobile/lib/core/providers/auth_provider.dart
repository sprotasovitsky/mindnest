import 'package:flutter/foundation.dart';
import 'package:freezed_annotation/freezed_annotation.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../api/api_client.dart';
import '../auth/auth_service.dart';
import '../error/app_error.dart';
import '../repositories/auth_repository.dart';

part 'auth_provider.freezed.dart';
part 'auth_provider.g.dart';

@freezed
sealed class AuthState with _$AuthState {
  const factory AuthState({
    @Default(true) bool isLoading,
    @Default(false) bool isAuthenticated,
    String? userId,
    String? email,
    String? name,
    @Default(false) bool emailVerified,
    @Default(0) int tokensUsed,
    @Default(0) int tokenLimit,
    String? error,
    String? loginMethod, // 'password', 'google', or 'apple'
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
    final authService = ref.read(authServiceProvider);

    try {
      // Initialize API client with stored tokens
      await repository.initializeFromStorage();

      final isLoggedIn = await repository.isLoggedIn();
      if (isLoggedIn) {
        final userData = await repository.getUserData();
        final emailVerified = await repository.isEmailVerified();
        final loginMethod = await authService.getLoginMethod();
        state = AuthState(
          isLoading: false,
          isAuthenticated: true,
          userId: userData['userId'],
          email: userData['email'],
          name: userData['name'],
          emailVerified: emailVerified,
          loginMethod: loginMethod,
        );
        if (kDebugMode) debugPrint('Auth: User is logged in, emailVerified=$emailVerified, loginMethod=$loginMethod');
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
      final authService = ref.read(authServiceProvider);
      final response = await repository.login(email, password);

      // Save login method
      await authService.setLoginMethod('password');

      // projectsProvider watches authProvider and will auto-reload
      state = AuthState(
        isLoading: false,
        isAuthenticated: true,
        userId: response.userId,
        email: response.email,
        name: response.name,
        emailVerified: response.emailVerified,
        loginMethod: 'password',
      );

      if (kDebugMode) debugPrint('Auth: Login successful, emailVerified=${response.emailVerified}');
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
      final authService = ref.read(authServiceProvider);
      final response = await repository.register(email, password, name);

      // Save login method
      await authService.setLoginMethod('password');

      // projectsProvider watches authProvider and will auto-reload
      state = AuthState(
        isLoading: false,
        isAuthenticated: true,
        userId: response.userId,
        email: response.email,
        name: response.name,
        emailVerified: response.emailVerified,
        loginMethod: 'password',
      );

      if (kDebugMode) debugPrint('Auth: Registration successful, emailVerified=${response.emailVerified}');
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

  /// Verify email with token (from deep link)
  Future<bool> verifyEmail(String token) async {
    try {
      final repository = ref.read(authRepositoryProvider);
      await repository.verifyEmail(token);
      state = state.copyWith(emailVerified: true);
      if (kDebugMode) debugPrint('Auth: Email verified successfully');
      return true;
    } catch (e) {
      if (kDebugMode) debugPrint('Auth: Email verification failed: $e');
      return false;
    }
  }

  /// Resend verification email
  Future<bool> resendVerification() async {
    if (state.email == null) return false;

    try {
      final repository = ref.read(authRepositoryProvider);
      await repository.resendVerification(state.email!);
      if (kDebugMode) debugPrint('Auth: Verification email resent');
      return true;
    } catch (e) {
      if (kDebugMode) debugPrint('Auth: Failed to resend verification: $e');
      return false;
    }
  }

  /// Refresh user info from server (to get updated verification status)
  Future<void> refreshUserInfo() async {
    try {
      final repository = ref.read(authRepositoryProvider);
      final user = await repository.getCurrentUser();

      state = state.copyWith(
        emailVerified: user.emailVerified,
        tokensUsed: user.tokensUsed,
        tokenLimit: user.tokenLimit,
      );

      if (kDebugMode) debugPrint('Auth: User info refreshed, emailVerified=${user.emailVerified}');
    } catch (e) {
      // Silently fail - user info is not critical
      if (kDebugMode) debugPrint('Auth: Failed to refresh user info: $e');
    }
  }

  /// Update user name
  Future<bool> updateName(String name) async {
    try {
      final repository = ref.read(authRepositoryProvider);
      final user = await repository.updateProfile(name: name);

      state = state.copyWith(name: user.name);

      if (kDebugMode) debugPrint('Auth: Name updated to ${user.name}');
      return true;
    } catch (e) {
      if (kDebugMode) debugPrint('Auth: Failed to update name: $e');
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

  /// Social login (Google or Apple)
  Future<bool> socialLogin({
    required String provider,
    required String idToken,
    String? name,
    bool isAccessToken = false,
  }) async {
    state = state.copyWith(isLoading: true, error: null);

    try {
      final repository = ref.read(authRepositoryProvider);
      final authService = ref.read(authServiceProvider);
      final response = await repository.socialLogin(
        provider: provider,
        idToken: idToken,
        name: name,
        isAccessToken: isAccessToken,
      );

      // Save login method (google or apple)
      await authService.setLoginMethod(provider);

      state = AuthState(
        isLoading: false,
        isAuthenticated: true,
        userId: response.userId,
        email: response.email,
        name: response.name,
        emailVerified: response.emailVerified,  // Always true for social login
        loginMethod: provider,
      );

      if (kDebugMode) debugPrint('Auth: Social login successful via $provider');
      return true;
    } catch (e) {
      if (kDebugMode) debugPrint('Auth: Social login failed: $e');
      state = state.copyWith(
        isLoading: false,
        error: e is AppError ? e.message : 'Social login failed. Please try again.',
      );
      return false;
    }
  }

  /// Delete user account
  Future<bool> deleteAccount({String? password}) async {
    state = state.copyWith(isLoading: true, error: null);

    try {
      final repository = ref.read(authRepositoryProvider);
      await repository.deleteAccount(password: password);

      // Clear state
      state = const AuthState(isLoading: false, isAuthenticated: false);

      if (kDebugMode) debugPrint('Auth: Account deleted successfully');
      return true;
    } catch (e) {
      if (kDebugMode) debugPrint('Auth: Failed to delete account: $e');
      state = state.copyWith(
        isLoading: false,
        error: e is AppError ? e.message : 'Failed to delete account. Please try again.',
      );
      return false;
    }
  }
}
