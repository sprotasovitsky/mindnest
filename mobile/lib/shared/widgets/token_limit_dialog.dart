import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/providers/auth_provider.dart';
import '../../core/theme/app_colors.dart';

/// A dialog shown when an unverified user has exceeded their token limit.
/// Prompts the user to verify their email to continue using the app.
class TokenLimitDialog extends ConsumerStatefulWidget {
  /// Creates a token limit dialog.
  ///
  /// [tokensUsed] - The number of tokens the user has used
  /// [limit] - The token limit for unverified users
  const TokenLimitDialog({
    super.key,
    required this.tokensUsed,
    required this.limit,
  });

  final int tokensUsed;
  final int limit;

  /// Shows the token limit dialog.
  ///
  /// Returns `true` if the user chose to verify email, `false` if dismissed.
  static Future<bool> show(
    BuildContext context, {
    required int tokensUsed,
    required int limit,
  }) async {
    final result = await showDialog<bool>(
      context: context,
      barrierDismissible: false,
      builder: (context) => TokenLimitDialog(
        tokensUsed: tokensUsed,
        limit: limit,
      ),
    );
    return result ?? false;
  }

  @override
  ConsumerState<TokenLimitDialog> createState() => _TokenLimitDialogState();
}

class _TokenLimitDialogState extends ConsumerState<TokenLimitDialog> {
  bool _isResending = false;

  String _formatTokenCount(int tokens) {
    if (tokens >= 1000000) {
      return '${(tokens / 1000000).toStringAsFixed(1)}M';
    } else if (tokens >= 1000) {
      return '${(tokens / 1000).toStringAsFixed(0)}K';
    }
    return tokens.toString();
  }

  Future<void> _resendVerification() async {
    if (_isResending) return;

    setState(() {
      _isResending = true;
    });

    try {
      final success =
          await ref.read(authProvider.notifier).resendVerification();

      if (mounted) {
        setState(() {
          _isResending = false;
        });

        if (success) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text('Verification email sent! Check your inbox.'),
              backgroundColor: AppColors.success,
            ),
          );
          Navigator.of(context).pop(true);
        } else {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text('Failed to send verification email. Try again.'),
              backgroundColor: AppColors.error,
            ),
          );
        }
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _isResending = false;
        });
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Failed to send verification email. Try again.'),
            backgroundColor: AppColors.error,
          ),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final colorScheme = theme.colorScheme;

    return AlertDialog(
      icon: Icon(
        Icons.email_outlined,
        size: 48,
        color: colorScheme.primary,
      ),
      title: const Text('Email Verification Required'),
      content: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Text(
            "You've used your trial limit of ${_formatTokenCount(widget.limit)} tokens.",
            textAlign: TextAlign.center,
            style: theme.textTheme.bodyLarge,
          ),
          const SizedBox(height: 12),
          Text(
            'Verify your email to continue using MindNest with unlimited access.',
            textAlign: TextAlign.center,
            style: theme.textTheme.bodyMedium?.copyWith(
              color: colorScheme.onSurfaceVariant,
            ),
          ),
          const SizedBox(height: 16),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            decoration: BoxDecoration(
              color: colorScheme.surfaceContainerHighest,
              borderRadius: BorderRadius.circular(8),
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(
                  Icons.analytics_outlined,
                  size: 18,
                  color: colorScheme.onSurfaceVariant,
                ),
                const SizedBox(width: 8),
                Text(
                  'Used: ${_formatTokenCount(widget.tokensUsed)} / ${_formatTokenCount(widget.limit)}',
                  style: theme.textTheme.bodySmall?.copyWith(
                    color: colorScheme.onSurfaceVariant,
                    fontWeight: FontWeight.w500,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.of(context).pop(false),
          child: const Text('Later'),
        ),
        FilledButton.icon(
          onPressed: _isResending ? null : _resendVerification,
          icon: _isResending
              ? SizedBox(
                  width: 18,
                  height: 18,
                  child: CircularProgressIndicator(
                    strokeWidth: 2,
                    color: colorScheme.onPrimary,
                  ),
                )
              : const Icon(Icons.send, size: 18),
          label: Text(_isResending ? 'Sending...' : 'Verify Email'),
        ),
      ],
    );
  }
}
