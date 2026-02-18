import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/providers/auth_provider.dart';
import '../../../../core/providers/whisper_provider.dart';
import '../../../../core/services/whisper_service.dart';
import '../../../../shared/widgets/email_verification_banner.dart';

class ProfileScreen extends ConsumerStatefulWidget {
  const ProfileScreen({super.key});

  @override
  ConsumerState<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends ConsumerState<ProfileScreen> {
  @override
  void initState() {
    super.initState();
    // Refresh user info to get updated email_verified status
    Future.microtask(() {
      ref.read(authProvider.notifier).refreshUserInfo();
    });
  }

  @override
  Widget build(BuildContext context) {
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
                      GestureDetector(
                        onTap: () => _showEditNameDialog(context, authState.name!),
                        child: Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Text(
                              authState.name!,
                              style:
                                  Theme.of(context).textTheme.titleLarge?.copyWith(
                                        fontWeight: FontWeight.bold,
                                      ),
                            ),
                            const SizedBox(width: 8),
                            Icon(
                              Icons.edit,
                              size: 18,
                              color: Theme.of(context).colorScheme.primary,
                            ),
                          ],
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

                    // Speech Model (Whisper)
                    const _WhisperModelTile(),

                    const Spacer(),

                    // Logout button
                    SizedBox(
                      width: double.infinity,
                      child: OutlinedButton.icon(
                        onPressed: () => _showLogoutDialog(context),
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

  Future<void> _showEditNameDialog(BuildContext context, String currentName) async {
    final controller = TextEditingController(text: currentName);
    final formKey = GlobalKey<FormState>();

    final newName = await showDialog<String>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Edit Name'),
        content: Form(
          key: formKey,
          child: TextFormField(
            controller: controller,
            autofocus: true,
            textCapitalization: TextCapitalization.words,
            decoration: const InputDecoration(
              labelText: 'Name',
              border: OutlineInputBorder(),
            ),
            validator: (value) {
              if (value == null || value.trim().isEmpty) {
                return 'Name is required';
              }
              if (value.trim().length < 2) {
                return 'Name must be at least 2 characters';
              }
              if (value.trim().length > 100) {
                return 'Name must be less than 100 characters';
              }
              return null;
            },
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cancel'),
          ),
          FilledButton(
            onPressed: () {
              if (formKey.currentState!.validate()) {
                Navigator.pop(context, controller.text.trim());
              }
            },
            child: const Text('Save'),
          ),
        ],
      ),
    );

    controller.dispose();

    if (newName != null && newName != currentName) {
      if (!mounted) return;
      final success = await ref.read(authProvider.notifier).updateName(newName);
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(success ? 'Name updated' : 'Failed to update name'),
        ),
      );
    }
  }

  Future<void> _showLogoutDialog(BuildContext context) async {
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
    BuildContext context, {
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

class _WhisperModelTile extends ConsumerWidget {
  const _WhisperModelTile();

  String _formatBytes(int bytes) {
    if (bytes < 1024) return '$bytes B';
    if (bytes < 1024 * 1024) return '${(bytes / 1024).toStringAsFixed(1)} KB';
    return '${(bytes / (1024 * 1024)).toStringAsFixed(1)} MB';
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final whisperState = ref.watch(whisperProvider);

    return ListTile(
      leading: const Icon(Icons.record_voice_over_outlined),
      title: const Text('Speech Model'),
      subtitle: _buildSubtitle(whisperState),
      trailing: _buildTrailing(context, ref, whisperState),
      onTap: () => _showModelDialog(context, ref, whisperState),
    );
  }

  Widget _buildSubtitle(WhisperState state) {
    switch (state.modelStatus) {
      case WhisperModelStatus.unknown:
        return const Text('Checking...');
      case WhisperModelStatus.notDownloaded:
        return Text('Not downloaded (~${_formatBytes(WhisperService.modelSizeBytes)})');
      case WhisperModelStatus.downloading:
        return const Text('Downloading...');
      case WhisperModelStatus.downloaded:
        final size = state.modelSizeBytes;
        return Text(size != null ? 'Downloaded (${_formatBytes(size)})' : 'Downloaded');
      case WhisperModelStatus.error:
        return Text(state.errorMessage ?? 'Error');
    }
  }

  Widget? _buildTrailing(BuildContext context, WidgetRef ref, WhisperState state) {
    switch (state.modelStatus) {
      case WhisperModelStatus.unknown:
      case WhisperModelStatus.downloading:
        return const SizedBox(
          width: 24,
          height: 24,
          child: CircularProgressIndicator(strokeWidth: 2),
        );
      case WhisperModelStatus.notDownloaded:
      case WhisperModelStatus.error:
        return const Icon(Icons.download);
      case WhisperModelStatus.downloaded:
        return const Icon(Icons.check_circle, color: Colors.green);
    }
  }

  void _showModelDialog(BuildContext context, WidgetRef ref, WhisperState state) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Speech Model'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'The speech model enables voice input for chat messages. '
              'Audio is processed locally on your device for privacy.',
            ),
            const SizedBox(height: 16),
            Row(
              children: [
                Icon(
                  state.modelStatus == WhisperModelStatus.downloaded
                      ? Icons.check_circle
                      : Icons.circle_outlined,
                  size: 20,
                  color: state.modelStatus == WhisperModelStatus.downloaded
                      ? Colors.green
                      : null,
                ),
                const SizedBox(width: 8),
                Text(
                  state.modelStatus == WhisperModelStatus.downloaded
                      ? 'Model downloaded'
                      : 'Model not downloaded',
                ),
              ],
            ),
            const SizedBox(height: 8),
            Text(
              'Size: ~${_formatBytes(WhisperService.modelSizeBytes)}',
              style: Theme.of(context).textTheme.bodySmall,
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Close'),
          ),
          if (state.modelStatus == WhisperModelStatus.downloaded)
            TextButton(
              onPressed: () async {
                Navigator.pop(context);
                final confirmed = await showDialog<bool>(
                  context: context,
                  builder: (context) => AlertDialog(
                    title: const Text('Delete Model'),
                    content: const Text(
                      'Delete the speech model to free up storage space? '
                      'You can download it again later.',
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
                if (confirmed == true) {
                  await ref.read(whisperProvider.notifier).deleteModel();
                }
              },
              style: TextButton.styleFrom(
                foregroundColor: Theme.of(context).colorScheme.error,
              ),
              child: const Text('Delete'),
            ),
          if (state.modelStatus == WhisperModelStatus.notDownloaded ||
              state.modelStatus == WhisperModelStatus.error)
            FilledButton(
              onPressed: () {
                Navigator.pop(context);
                ref.read(whisperProvider.notifier).downloadModel();
              },
              child: const Text('Download'),
            ),
        ],
      ),
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
