import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/providers/auth_provider.dart';

/// Screen shown after email verification via deep link.
/// Verifies the token and shows success/error message.
class EmailVerifiedScreen extends ConsumerStatefulWidget {
  final String? token;

  const EmailVerifiedScreen({super.key, this.token});

  @override
  ConsumerState<EmailVerifiedScreen> createState() =>
      _EmailVerifiedScreenState();
}

class _EmailVerifiedScreenState extends ConsumerState<EmailVerifiedScreen> {
  bool _isLoading = true;
  bool _isSuccess = false;
  String? _errorMessage;

  @override
  void initState() {
    super.initState();
    _handleVerification();
  }

  Future<void> _handleVerification() async {
    if (widget.token == null || widget.token!.isEmpty) {
      setState(() {
        _isLoading = false;
        _isSuccess = false;
        _errorMessage = 'Invalid verification link';
      });
      return;
    }

    try {
      // Call API to verify email
      final success =
          await ref.read(authProvider.notifier).verifyEmail(widget.token!);

      if (mounted) {
        setState(() {
          _isLoading = false;
          _isSuccess = success;
          _errorMessage = success ? null : 'Verification failed or link expired';
        });

        if (success) {
          // Short delay to show success message, then navigate
          await Future.delayed(const Duration(seconds: 2));
          if (mounted) {
            context.go('/projects');
          }
        }
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _isLoading = false;
          _isSuccess = false;
          _errorMessage = 'Verification failed. Please try again.';
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final colorScheme = theme.colorScheme;

    return Scaffold(
      body: SafeArea(
        child: Center(
          child: Padding(
            padding: const EdgeInsets.all(32),
            child: _isLoading
                ? _buildLoading(theme, colorScheme)
                : _isSuccess
                    ? _buildSuccess(theme, colorScheme)
                    : _buildError(theme, colorScheme),
          ),
        ),
      ),
    );
  }

  Widget _buildLoading(ThemeData theme, ColorScheme colorScheme) {
    return Column(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        const CircularProgressIndicator(),
        const SizedBox(height: 24),
        Text(
          'Verifying your email...',
          style: theme.textTheme.bodyLarge?.copyWith(
            color: colorScheme.onSurfaceVariant,
          ),
        ),
      ],
    );
  }

  Widget _buildSuccess(ThemeData theme, ColorScheme colorScheme) {
    return Column(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        Container(
          width: 80,
          height: 80,
          decoration: BoxDecoration(
            color: colorScheme.primaryContainer,
            shape: BoxShape.circle,
          ),
          child: Icon(
            Icons.check_circle_outline,
            size: 48,
            color: colorScheme.primary,
          ),
        ),
        const SizedBox(height: 24),
        Text(
          'Email Verified!',
          style: theme.textTheme.headlineMedium?.copyWith(
            fontWeight: FontWeight.bold,
            color: colorScheme.onSurface,
          ),
        ),
        const SizedBox(height: 12),
        Text(
          'Your email has been successfully verified.\nRedirecting...',
          textAlign: TextAlign.center,
          style: theme.textTheme.bodyLarge?.copyWith(
            color: colorScheme.onSurfaceVariant,
          ),
        ),
        const SizedBox(height: 32),
        const CircularProgressIndicator(),
      ],
    );
  }

  Widget _buildError(ThemeData theme, ColorScheme colorScheme) {
    return Column(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        Container(
          width: 80,
          height: 80,
          decoration: BoxDecoration(
            color: colorScheme.errorContainer,
            shape: BoxShape.circle,
          ),
          child: Icon(
            Icons.error_outline,
            size: 48,
            color: colorScheme.error,
          ),
        ),
        const SizedBox(height: 24),
        Text(
          'Verification Failed',
          style: theme.textTheme.headlineMedium?.copyWith(
            fontWeight: FontWeight.bold,
            color: colorScheme.onSurface,
          ),
        ),
        const SizedBox(height: 12),
        Text(
          _errorMessage ?? 'Something went wrong',
          textAlign: TextAlign.center,
          style: theme.textTheme.bodyLarge?.copyWith(
            color: colorScheme.onSurfaceVariant,
          ),
        ),
        const SizedBox(height: 32),
        FilledButton(
          onPressed: () => context.go('/login'),
          child: const Text('Go to Login'),
        ),
      ],
    );
  }
}
