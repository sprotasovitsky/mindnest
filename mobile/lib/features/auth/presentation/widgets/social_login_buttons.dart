import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:google_sign_in/google_sign_in.dart';
import 'package:sign_in_with_apple/sign_in_with_apple.dart';

import '../../../../core/providers/auth_provider.dart';

// Platform check helper that works on web
bool get _isIOSPlatform {
  if (kIsWeb) return false;
  // Use defaultTargetPlatform instead of dart:io Platform
  return defaultTargetPlatform == TargetPlatform.iOS;
}

class SocialLoginButtons extends ConsumerStatefulWidget {
  final VoidCallback? onSuccess;
  final void Function(String error)? onError;

  const SocialLoginButtons({
    super.key,
    this.onSuccess,
    this.onError,
  });

  @override
  ConsumerState<SocialLoginButtons> createState() => _SocialLoginButtonsState();
}

class _SocialLoginButtonsState extends ConsumerState<SocialLoginButtons> {
  bool _isLoading = false;
  String? _loadingProvider;

  Future<void> _handleGoogleSignIn() async {
    if (_isLoading) return;

    debugPrint('=== GOOGLE SIGN-IN START ===');

    setState(() {
      _isLoading = true;
      _loadingProvider = 'google';
    });

    try {
      debugPrint('Google: Creating GoogleSignIn instance...');
      final googleSignIn = GoogleSignIn(
        scopes: ['email', 'profile'],
      );

      debugPrint('Google: Calling signIn()...');
      final account = await googleSignIn.signIn();
      debugPrint('Google: signIn() returned, account: ${account?.email}');

      if (account == null) {
        debugPrint('Google: User cancelled sign-in');
        setState(() {
          _isLoading = false;
          _loadingProvider = null;
        });
        return;
      }

      debugPrint('Google: Getting authentication...');
      final auth = await account.authentication;
      final idToken = auth.idToken;
      debugPrint('Google: Got idToken: ${idToken != null ? "yes (${idToken.length} chars)" : "null"}');

      if (idToken == null) {
        debugPrint('Google: ERROR - idToken is null');
        widget.onError?.call('Failed to get Google ID token');
        setState(() {
          _isLoading = false;
          _loadingProvider = null;
        });
        return;
      }

      debugPrint('Google: Calling backend socialLogin...');
      final success = await ref.read(authProvider.notifier).socialLogin(
            provider: 'google',
            idToken: idToken,
            name: account.displayName,
          );
      debugPrint('Google: Backend returned success=$success');

      if (success) {
        debugPrint('Google: SUCCESS - calling onSuccess');
        widget.onSuccess?.call();
      } else {
        final error = ref.read(authProvider).error;
        debugPrint('Google: FAILED - error: $error');
        widget.onError?.call(error ?? 'Google sign-in failed');
      }
    } catch (e, stackTrace) {
      debugPrint('Google: EXCEPTION - $e');
      debugPrint('Google: Stack trace: $stackTrace');
      widget.onError?.call('Google sign-in failed. Please try again.');
    } finally {
      debugPrint('=== GOOGLE SIGN-IN END ===');
      if (mounted) {
        setState(() {
          _isLoading = false;
          _loadingProvider = null;
        });
      }
    }
  }

  Future<void> _handleAppleSignIn() async {
    if (_isLoading) return;

    debugPrint('=== APPLE SIGN-IN START ===');

    setState(() {
      _isLoading = true;
      _loadingProvider = 'apple';
    });

    try {
      debugPrint('Apple: Calling getAppleIDCredential...');
      final credential = await SignInWithApple.getAppleIDCredential(
        scopes: [
          AppleIDAuthorizationScopes.email,
          AppleIDAuthorizationScopes.fullName,
        ],
      );
      debugPrint('Apple: Got credential, userIdentifier: ${credential.userIdentifier}');

      final idToken = credential.identityToken;
      debugPrint('Apple: idToken: ${idToken != null ? "yes (${idToken.length} chars)" : "null"}');

      if (idToken == null) {
        debugPrint('Apple: ERROR - idToken is null');
        widget.onError?.call('Failed to get Apple ID token');
        setState(() {
          _isLoading = false;
          _loadingProvider = null;
        });
        return;
      }

      // Apple only provides name on first sign-in
      String? name;
      if (credential.givenName != null || credential.familyName != null) {
        final parts = [credential.givenName, credential.familyName]
            .where((s) => s != null && s.isNotEmpty)
            .toList();
        if (parts.isNotEmpty) {
          name = parts.join(' ');
        }
      }
      debugPrint('Apple: name=$name, email=${credential.email}');

      debugPrint('Apple: Calling backend socialLogin...');
      final success = await ref.read(authProvider.notifier).socialLogin(
            provider: 'apple',
            idToken: idToken,
            name: name,
          );
      debugPrint('Apple: Backend returned success=$success');

      if (success) {
        debugPrint('Apple: SUCCESS - calling onSuccess');
        widget.onSuccess?.call();
      } else {
        final error = ref.read(authProvider).error;
        debugPrint('Apple: FAILED - error: $error');
        widget.onError?.call(error ?? 'Apple sign-in failed');
      }
    } on SignInWithAppleAuthorizationException catch (e) {
      debugPrint('Apple: SignInWithAppleAuthorizationException - code: ${e.code}, message: ${e.message}');
      if (e.code == AuthorizationErrorCode.canceled) {
        debugPrint('Apple: User cancelled');
      } else {
        widget.onError?.call('Apple sign-in failed. Please try again.');
      }
    } catch (e, stackTrace) {
      debugPrint('Apple: EXCEPTION - $e');
      debugPrint('Apple: Stack trace: $stackTrace');
      widget.onError?.call('Apple sign-in failed. Please try again.');
    } finally {
      debugPrint('=== APPLE SIGN-IN END ===');
      if (mounted) {
        setState(() {
          _isLoading = false;
          _loadingProvider = null;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        // Google Sign-In button
        SizedBox(
          width: double.infinity,
          height: 48,
          child: OutlinedButton.icon(
            onPressed: _isLoading ? null : _handleGoogleSignIn,
            icon: _loadingProvider == 'google'
                ? SizedBox(
                    width: 20,
                    height: 20,
                    child: CircularProgressIndicator(
                      strokeWidth: 2,
                      color: theme.colorScheme.primary,
                    ),
                  )
                : Image.network(
                    'https://www.gstatic.com/firebasejs/ui/2.0.0/images/auth/google.svg',
                    width: 20,
                    height: 20,
                    errorBuilder: (_, __, ___) => Icon(
                      Icons.g_mobiledata,
                      size: 24,
                      color: theme.colorScheme.onSurface,
                    ),
                  ),
            label: const Text('Continue with Google'),
            style: OutlinedButton.styleFrom(
              foregroundColor: theme.colorScheme.onSurface,
              side: BorderSide(color: theme.colorScheme.outline),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(8),
              ),
            ),
          ),
        ),

        // Apple Sign-In button (iOS only - App Store requirement)
        if (_isIOSPlatform) ...[
          const SizedBox(height: 12),
          SizedBox(
            width: double.infinity,
            height: 48,
            child: ElevatedButton.icon(
              onPressed: _isLoading ? null : _handleAppleSignIn,
              icon: _loadingProvider == 'apple'
                  ? const SizedBox(
                      width: 20,
                      height: 20,
                      child: CircularProgressIndicator(
                        strokeWidth: 2,
                        color: Colors.white,
                      ),
                    )
                  : const Icon(Icons.apple, size: 24),
              label: const Text('Continue with Apple'),
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.black,
                foregroundColor: Colors.white,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(8),
                ),
              ),
            ),
          ),
        ],
      ],
    );
  }
}
