import 'package:freezed_annotation/freezed_annotation.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../api/api_client.dart';
import '../error/app_error.dart';
import '../repositories/auth_repository.dart';
import 'project_provider.dart';

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
    // Subscribe to auth invalidation callback
    final apiClient = ref.read(apiClientProvider);
    apiClient.onAuthInvalidated = () {
      ref.invalidateSelf();
    };

    // Cleanup on dispose
    ref.onDispose(() {
      apiClient.onAuthInvalidated = null;
    });

    _checkAuth();
    return const AuthState();
  }

  Future<void> _checkAuth() async {
    final repository = ref.read(authRepositoryProvider);
    final apiClient = ref.read(apiClientProvider);

    try {
      final isLoggedIn = await repository.isLoggedIn();
      if (isLoggedIn) {
        final token = await repository.getToken();
        if (token != null) {
          apiClient.setAuthToken(token);
        }
        final userData = await repository.getUserData();
        state = AuthState(
          isLoading: false,
          isAuthenticated: true,
          userId: userData['userId'],
          email: userData['email'],
          name: userData['name'],
        );
      } else {
        state = const AuthState(isLoading: false, isAuthenticated: false);
      }
    } catch (e) {
      state = const AuthState(isLoading: false, isAuthenticated: false);
    }
  }

  Future<bool> login(String email, String password) async {
    state = state.copyWith(isLoading: true, error: null);
    try {
      final repository = ref.read(authRepositoryProvider);
      final response = await repository.login(email, password);

      // Clear any stale project state (e.g., errors from unauthenticated requests)
      ref.invalidate(projectsProvider);

      state = AuthState(
        isLoading: false,
        isAuthenticated: true,
        userId: response.userId,
        email: response.email,
        name: response.name,
      );
      return true;
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        error: e.toUserMessage(),
      );
      return false;
    }
  }

  Future<bool> register(String email, String password, String? name) async {
    state = state.copyWith(isLoading: true, error: null);
    try {
      final repository = ref.read(authRepositoryProvider);
      final response = await repository.register(email, password, name);

      // Clear any stale project state (e.g., errors from unauthenticated requests)
      ref.invalidate(projectsProvider);

      state = AuthState(
        isLoading: false,
        isAuthenticated: true,
        userId: response.userId,
        email: response.email,
        name: response.name,
      );
      return true;
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        error: e.toUserMessage(),
      );
      return false;
    }
  }

  Future<void> logout() async {
    final repository = ref.read(authRepositoryProvider);
    await repository.logout();

    // Clear user data from other providers
    ref.invalidate(projectsProvider);

    state = const AuthState(isLoading: false, isAuthenticated: false);
  }
}
