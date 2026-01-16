import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../providers/auth_provider.dart';
import '../../features/auth/presentation/screens/email_verified_screen.dart';
import '../../features/auth/presentation/screens/forgot_password_screen.dart';
import '../../features/auth/presentation/screens/login_screen.dart';
import '../../features/chat/presentation/screens/chat_screen.dart';
import '../../features/landing/presentation/screens/landing_screen.dart';
import '../../features/members/presentation/screens/members_screen.dart';
import '../../features/profile/presentation/screens/change_password_screen.dart';
import '../../features/profile/presentation/screens/profile_screen.dart';
import '../../features/projects/presentation/screens/projects_list_screen.dart';

final appRouterProvider = Provider<GoRouter>((ref) {
  final authNotifier = _AuthRefreshNotifier(ref);

  return GoRouter(
    // Web: start at landing page, Mobile: start at projects (will redirect to login if needed)
    initialLocation: kIsWeb ? '/' : '/projects',
    refreshListenable: authNotifier,
    redirect: (context, state) {
      final authState = authNotifier.authState;
      final isLoading = authState.isLoading;
      final isAuthenticated = authState.isAuthenticated;
      final location = state.matchedLocation;
      final isOnLoginPage = location == '/login';
      final isOnLandingPage = location == '/';

      // Public routes that don't require authentication
      final isPublicRoute = location == '/' ||
          location == '/login' ||
          location == '/forgot-password' ||
          location == '/verify-email' ||
          location == '/reset-password';

      // Still loading auth state
      if (isLoading) return null;

      // Mobile: redirect from landing to login (landing is for web only)
      if (!kIsWeb && isOnLandingPage && !isAuthenticated) {
        return '/login';
      }

      // Not authenticated and not on public route -> redirect to login
      if (!isAuthenticated && !isPublicRoute) {
        return '/login';
      }

      // Authenticated and on login/landing page -> redirect to projects
      if (isAuthenticated && (isOnLoginPage || isOnLandingPage)) {
        return '/projects';
      }

      return null;
    },
    routes: [
      // Landing page (web only - mobile goes directly to login/projects)
      GoRoute(
        path: '/',
        name: 'landing',
        builder: (context, state) => const LandingScreen(),
      ),
      GoRoute(
        path: '/login',
        name: 'login',
        builder: (context, state) => const LoginScreen(),
      ),
      GoRoute(
        path: '/forgot-password',
        name: 'forgot-password',
        builder: (context, state) => const ForgotPasswordScreen(),
      ),
      GoRoute(
        path: '/projects',
        name: 'projects',
        builder: (context, state) => const ProjectsListScreen(),
      ),
      GoRoute(
        path: '/chat',
        name: 'chat',
        builder: (context, state) => const ChatScreen(),
      ),
      GoRoute(
        path: '/profile',
        name: 'profile',
        builder: (context, state) => const ProfileScreen(),
      ),
      GoRoute(
        path: '/change-password',
        name: 'change-password',
        builder: (context, state) => const ChangePasswordScreen(),
      ),
      GoRoute(
        path: '/members',
        name: 'members',
        builder: (context, state) => const MembersScreen(),
      ),
      // Deep link handler for email verification
      // Universal Link: https://mindnest.one/verify-email?token=XXX
      GoRoute(
        path: '/verify-email',
        name: 'verify-email',
        builder: (context, state) {
          final token = state.uri.queryParameters['token'];
          return EmailVerifiedScreen(token: token);
        },
      ),
    ],
    errorBuilder: (context, state) => Scaffold(
      body: Center(
        child: Text('Page not found: ${state.matchedLocation}'),
      ),
    ),
  );
});

class _AuthRefreshNotifier extends ChangeNotifier {
  _AuthRefreshNotifier(Ref ref) {
    // Initialize with current state
    _authState = ref.read(authProvider);
    // Listen for changes
    ref.listen(authProvider, (_, newState) {
      _authState = newState;
      notifyListeners();
    });
  }

  late AuthState _authState;
  AuthState get authState => _authState;
}
