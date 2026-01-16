import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/providers/auth_provider.dart';
import '../../../../shared/widgets/email_verification_banner.dart';

class ProfileScreen extends ConsumerWidget {
  const ProfileScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final authState = ref.watch(authProvider);
    final loginMethod = authState.loginMethod;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Profile'),
      ),
      body: Column(
        children: [
          // Show verification banner for unverified users
          const EmailVerificationBanner(),
          Expanded(
            child: SafeArea(
              top: false,
              child: Padding(
                padding: const EdgeInsets.all(24),
                child: Column(
                  children: [
                    const SizedBox(height: 32),
                    CircleAvatar(
                      radius: 48,
                      backgroundColor:
                          Theme.of(context).colorScheme.primaryContainer,
                      child: Icon(
                        Icons.person,
                        size: 48,
                        color:
                            Theme.of(context).colorScheme.onPrimaryContainer,
                      ),
                    ),
                    const SizedBox(height: 24),
                    if (authState.name != null &&
                        authState.name!.isNotEmpty) ...[
                      Text(
                        authState.name!,
                        style:
                            Theme.of(context).textTheme.titleLarge?.copyWith(
                                  fontWeight: FontWeight.bold,
                                ),
                      ),
                      const SizedBox(height: 4),
                    ],
                    GestureDetector(
                      onTap: () {
                        final email = authState.email;
                        if (email != null) {
                          Clipboard.setData(ClipboardData(text: email));
                          ScaffoldMessenger.of(context).showSnackBar(
                            const SnackBar(
                              content: Text('Email copied to clipboard'),
                              duration: Duration(seconds: 2),
                            ),
                          );
                        }
                      },
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Text(
                            authState.email ?? 'No email',
                            style:
                                Theme.of(context).textTheme.bodyLarge?.copyWith(
                                      color: Theme.of(context)
                                          .colorScheme
                                          .onSurfaceVariant,
                                    ),
                          ),
                          const SizedBox(width: 4),
                          Icon(
                            Icons.copy,
                            size: 16,
                            color:
                                Theme.of(context).colorScheme.onSurfaceVariant,
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 8),

                    // Show login method
                    _LoginMethodChip(loginMethod: loginMethod),

                    const SizedBox(height: 32),

                    // Settings list - only show Change Password for password login
                    if (loginMethod == 'password')
                      ListTile(
                        leading: const Icon(Icons.lock_outline),
                        title: const Text('Change Password'),
                        trailing: const Icon(Icons.chevron_right),
                        onTap: () => context.push('/change-password'),
                      ),

                    const Spacer(),

                    // Logout button
                    SizedBox(
                      width: double.infinity,
                      child: OutlinedButton.icon(
                        onPressed: () => _showLogoutDialog(context, ref),
                        icon: const Icon(Icons.logout),
                        label: const Padding(
                          padding: EdgeInsets.symmetric(vertical: 12),
                          child: Text('Logout'),
                        ),
                      ),
                    ),
                    const SizedBox(height: 16),

                    // Delete Account button
                    SizedBox(
                      width: double.infinity,
                      child: TextButton(
                        onPressed: () => _showDeleteAccountDialog(
                          context,
                          ref,
                          hasPassword: loginMethod == 'password',
                        ),
                        style: TextButton.styleFrom(
                          foregroundColor: Theme.of(context).colorScheme.error,
                        ),
                        child: const Text('Delete Account'),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Future<void> _showLogoutDialog(BuildContext context, WidgetRef ref) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Logout'),
        content: const Text('Are you sure you want to logout?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Cancel'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Logout'),
          ),
        ],
      ),
    );

    if (confirmed == true) {
      await ref.read(authProvider.notifier).logout();
      // Router will automatically redirect to /login
    }
  }

  Future<void> _showDeleteAccountDialog(
    BuildContext context,
    WidgetRef ref, {
    required bool hasPassword,
  }) async {
    if (hasPassword) {
      // Show dialog with password input
      await showDialog(
        context: context,
        builder: (context) => _DeleteAccountWithPasswordDialog(ref: ref),
      );
    } else {
      // Show simple confirmation dialog
      final confirmed = await showDialog<bool>(
        context: context,
        builder: (context) => AlertDialog(
          title: const Text('Delete Account'),
          content: const Text(
            'Are you sure you want to delete your account? This action cannot be undone and all your data will be permanently deleted.',
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context, false),
              child: const Text('Cancel'),
            ),
            FilledButton(
              onPressed: () => Navigator.pop(context, true),
              style: FilledButton.styleFrom(
                backgroundColor: Theme.of(context).colorScheme.error,
              ),
              child: const Text('Delete'),
            ),
          ],
        ),
      );

      if (confirmed == true && context.mounted) {
        final success =
            await ref.read(authProvider.notifier).deleteAccount();
        if (!success && context.mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text(
                ref.read(authProvider).error ?? 'Failed to delete account',
              ),
            ),
          );
        }
      }
    }
  }
}

class _LoginMethodChip extends StatelessWidget {
  final String? loginMethod;

  const _LoginMethodChip({required this.loginMethod});

  @override
  Widget build(BuildContext context) {
    final (icon, label) = switch (loginMethod) {
      'google' => (Icons.g_mobiledata, 'Signed in with Google'),
      'apple' => (Icons.apple, 'Signed in with Apple'),
      'password' => (Icons.email_outlined, 'Signed in with Email'),
      _ => (Icons.login, 'Signed in'),
    };

    return Chip(
      avatar: Icon(icon, size: 18),
      label: Text(label),
      backgroundColor: Theme.of(context).colorScheme.surfaceContainerHighest,
      side: BorderSide.none,
    );
  }
}

class _DeleteAccountWithPasswordDialog extends ConsumerStatefulWidget {
  final WidgetRef ref;

  const _DeleteAccountWithPasswordDialog({required this.ref});

  @override
  ConsumerState<_DeleteAccountWithPasswordDialog> createState() =>
      _DeleteAccountWithPasswordDialogState();
}

class _DeleteAccountWithPasswordDialogState
    extends ConsumerState<_DeleteAccountWithPasswordDialog> {
  final _passwordController = TextEditingController();
  bool _isLoading = false;
  String? _error;

  @override
  void dispose() {
    _passwordController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: const Text('Delete Account'),
      content: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'This action cannot be undone. All your data will be permanently deleted.',
          ),
          const SizedBox(height: 16),
          const Text('Enter your password to confirm:'),
          const SizedBox(height: 8),
          TextField(
            controller: _passwordController,
            obscureText: true,
            decoration: InputDecoration(
              hintText: 'Password',
              errorText: _error,
            ),
            enabled: !_isLoading,
          ),
        ],
      ),
      actions: [
        TextButton(
          onPressed: _isLoading ? null : () => Navigator.pop(context),
          child: const Text('Cancel'),
        ),
        FilledButton(
          onPressed: _isLoading ? null : _deleteAccount,
          style: FilledButton.styleFrom(
            backgroundColor: Theme.of(context).colorScheme.error,
          ),
          child: _isLoading
              ? const SizedBox(
                  width: 20,
                  height: 20,
                  child: CircularProgressIndicator(strokeWidth: 2),
                )
              : const Text('Delete'),
        ),
      ],
    );
  }

  Future<void> _deleteAccount() async {
    final password = _passwordController.text;
    if (password.isEmpty) {
      setState(() => _error = 'Password is required');
      return;
    }

    setState(() {
      _isLoading = true;
      _error = null;
    });

    final success = await widget.ref
        .read(authProvider.notifier)
        .deleteAccount(password: password);

    if (mounted) {
      if (success) {
        Navigator.pop(context);
      } else {
        setState(() {
          _isLoading = false;
          _error = widget.ref.read(authProvider).error ?? 'Invalid password';
        });
      }
    }
  }
}
