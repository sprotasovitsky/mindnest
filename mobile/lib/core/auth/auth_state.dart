import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'auth_service.dart';
import '../api/api_client.dart';

class AuthState {
  final bool isLoading;
  final bool isAuthenticated;
  final String? userId;
  final String? email;
  final String? name;
  final String? error;

  const AuthState({
    this.isLoading = false,
    this.isAuthenticated = false,
    this.userId,
    this.email,
    this.name,
    this.error,
  });

  AuthState copyWith({
    bool? isLoading,
    bool? isAuthenticated,
    String? userId,
    String? email,
    String? name,
    String? error,
  }) {
    return AuthState(
      isLoading: isLoading ?? this.isLoading,
      isAuthenticated: isAuthenticated ?? this.isAuthenticated,
      userId: userId ?? this.userId,
      email: email ?? this.email,
      name: name ?? this.name,
      error: error,
    );
  }
}

class AuthNotifier extends StateNotifier<AuthState> {
  final AuthService _authService;
  final ApiClient _apiClient;

  AuthNotifier(this._authService, this._apiClient) : super(const AuthState(isLoading: true)) {
    _checkAuth();
  }

  Future<void> _checkAuth() async {
    final isLoggedIn = await _authService.isLoggedIn();
    if (isLoggedIn) {
      final token = await _authService.getToken();
      if (token != null) {
        _apiClient.setAuthToken(token);
      }
      final userData = await _authService.getUserData();
      state = AuthState(
        isAuthenticated: true,
        userId: userData['userId'],
        email: userData['email'],
        name: userData['name'],
      );
    } else {
      state = const AuthState(isAuthenticated: false);
    }
  }

  Future<bool> login(String email, String password) async {
    state = state.copyWith(isLoading: true, error: null);
    try {
      final response = await _apiClient.login(email, password);

      await _authService.saveAuthData(
        token: response['token'],
        userId: response['user_id'],
        email: response['email'],
        name: response['name'],
      );

      _apiClient.setAuthToken(response['token']);

      state = AuthState(
        isAuthenticated: true,
        userId: response['user_id'],
        email: response['email'],
        name: response['name'],
      );
      return true;
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        error: _extractErrorMessage(e),
      );
      return false;
    }
  }

  Future<bool> register(String email, String password, String? name) async {
    state = state.copyWith(isLoading: true, error: null);
    try {
      final response = await _apiClient.register(email, password, name);

      await _authService.saveAuthData(
        token: response['token'],
        userId: response['user_id'],
        email: response['email'],
        name: response['name'],
      );

      _apiClient.setAuthToken(response['token']);

      state = AuthState(
        isAuthenticated: true,
        userId: response['user_id'],
        email: response['email'],
        name: response['name'],
      );
      return true;
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        error: _extractErrorMessage(e),
      );
      return false;
    }
  }

  Future<void> logout() async {
    await _authService.clearAuth();
    _apiClient.clearAuthToken();
    state = const AuthState(isAuthenticated: false);
  }

  String _extractErrorMessage(dynamic error) {
    if (error.toString().contains('Invalid email or password')) {
      return 'Invalid email or password';
    }
    if (error.toString().contains('Email already registered')) {
      return 'Email already registered';
    }
    return 'Something went wrong. Please try again.';
  }
}

final authProvider = StateNotifierProvider<AuthNotifier, AuthState>((ref) {
  final authService = ref.watch(authServiceProvider);
  final apiClient = ref.watch(apiClientProvider);
  return AuthNotifier(authService, apiClient);
});
