import 'dart:io';

import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:google_sign_in/google_sign_in.dart';
import 'package:sign_in_with_apple/sign_in_with_apple.dart';

import '../../../../core/providers/auth_provider.dart';

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

    setState(() {
      _isLoading = true;
      _loadingProvider = 'google';
    });

    try {
      final googleSignIn = GoogleSignIn(
        scopes: ['email', 'profile'],
      );

      final account = await googleSignIn.signIn();
      if (account == null) {
        // User cancelled
        setState(() {
          _isLoading = false;
          _loadingProvider = null;
        });
        return;
      }

      final auth = await account.authentication;
      final idToken = auth.idToken;

      if (idToken == null) {
        widget.onError?.call('Failed to get Google ID token');
        setState(() {
          _isLoading = false;
          _loadingProvider = null;
        });
        return;
      }

      final success = await ref.read(authProvider.notifier).socialLogin(
            provider: 'google',
            idToken: idToken,
            name: account.displayName,
          );

      if (success) {
        widget.onSuccess?.call();
      } else {
        final error = ref.read(authProvider).error;
        widget.onError?.call(error ?? 'Google sign-in failed');
      }
    } catch (e) {
      if (kDebugMode) debugPrint('Google sign-in error: $e');
      widget.onError?.call('Google sign-in failed. Please try again.');
    } finally {
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

    setState(() {
      _isLoading = true;
      _loadingProvider = 'apple';
    });

    try {
      final credential = await SignInWithApple.getAppleIDCredential(
        scopes: [
          AppleIDAuthorizationScopes.email,
          AppleIDAuthorizationScopes.fullName,
        ],
      );

      final idToken = credential.identityToken;
      if (idToken == null) {
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

      final success = await ref.read(authProvider.notifier).socialLogin(
            provider: 'apple',
            idToken: idToken,
            name: name,
          );

      if (success) {
        widget.onSuccess?.call();
      } else {
        final error = ref.read(authProvider).error;
        widget.onError?.call(error ?? 'Apple sign-in failed');
      }
    } on SignInWithAppleAuthorizationException catch (e) {
      if (e.code == AuthorizationErrorCode.canceled) {
        // User cancelled - do nothing
      } else {
        if (kDebugMode) debugPrint('Apple sign-in error: $e');
        widget.onError?.call('Apple sign-in failed. Please try again.');
      }
    } catch (e) {
      if (kDebugMode) debugPrint('Apple sign-in error: $e');
      widget.onError?.call('Apple sign-in failed. Please try again.');
    } finally {
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
    final isIOS = !kIsWeb && Platform.isIOS;

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
        if (isIOS) ...[
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
