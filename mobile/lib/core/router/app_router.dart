import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../auth/auth_state.dart';
import '../../features/chat/presentation/screens/chat_screen.dart';
import '../../features/auth/presentation/screens/login_screen.dart';
import '../../features/onboarding/presentation/screens/onboarding_screen.dart';

// Provider to track onboarding status
final onboardingCompletedProvider = FutureProvider<bool>((ref) async {
  final prefs = await SharedPreferences.getInstance();
  return prefs.getBool('hasCompletedOnboarding') ?? false;
});

final appRouterProvider = Provider<GoRouter>((ref) {
  final authState = ref.watch(authProvider);
  final onboardingAsync = ref.watch(onboardingCompletedProvider);
  final hasCompletedOnboarding = onboardingAsync.valueOrNull ?? true;

  return GoRouter(
    initialLocation: '/chat',
    refreshListenable: _AuthRefreshListenable(ref),
    redirect: (context, state) {
      final isLoading = authState.isLoading;
      final isAuthenticated = authState.isAuthenticated;
      final isOnLoginPage = state.matchedLocation == '/login';
      final isOnOnboardingPage = state.matchedLocation == '/onboarding';

      // Still loading auth state
      if (isLoading) return null;

      // Not authenticated and not on login page -> redirect to login
      if (!isAuthenticated && !isOnLoginPage) {
        return '/login';
      }

      // Authenticated and on login page -> check onboarding
      if (isAuthenticated && isOnLoginPage) {
        if (!hasCompletedOnboarding) {
          return '/onboarding';
        }
        return '/chat';
      }

      // Authenticated, completed onboarding, on onboarding page -> redirect to chat
      if (isAuthenticated && hasCompletedOnboarding && isOnOnboardingPage) {
        return '/chat';
      }

      return null;
    },
    routes: [
      GoRoute(
        path: '/login',
        name: 'login',
        builder: (context, state) => const LoginScreen(),
      ),
      GoRoute(
        path: '/onboarding',
        name: 'onboarding',
        builder: (context, state) => const OnboardingScreen(),
      ),
      GoRoute(
        path: '/chat',
        name: 'chat',
        builder: (context, state) => const ChatScreen(),
      ),
    ],
    errorBuilder: (context, state) => Scaffold(
      body: Center(
        child: Text('Page not found: ${state.matchedLocation}'),
      ),
    ),
  );
});

class _AuthRefreshListenable extends ChangeNotifier {
  _AuthRefreshListenable(this._ref) {
    _ref.listen(authProvider, (_, __) => notifyListeners());
  }

  final Ref _ref;
}
