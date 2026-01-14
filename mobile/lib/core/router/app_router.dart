import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../providers/auth_provider.dart';
import '../../features/chat/presentation/screens/chat_screen.dart';
import '../../features/auth/presentation/screens/login_screen.dart';
import '../../features/projects/presentation/screens/projects_list_screen.dart';
import '../../features/profile/presentation/screens/profile_screen.dart';
import '../../features/members/presentation/screens/members_screen.dart';

final appRouterProvider = Provider<GoRouter>((ref) {
  final authNotifier = _AuthRefreshNotifier(ref);

  return GoRouter(
    initialLocation: '/projects',
    refreshListenable: authNotifier,
    redirect: (context, state) {
      final authState = authNotifier.authState;
      final isLoading = authState.isLoading;
      final isAuthenticated = authState.isAuthenticated;
      final isOnLoginPage = state.matchedLocation == '/login';

      // Still loading auth state
      if (isLoading) return null;

      // Not authenticated and not on login page -> redirect to login
      if (!isAuthenticated && !isOnLoginPage) {
        return '/login';
      }

      // Authenticated and on login page -> redirect to projects
      if (isAuthenticated && isOnLoginPage) {
        return '/projects';
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
        path: '/members',
        name: 'members',
        builder: (context, state) => const MembersScreen(),
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
