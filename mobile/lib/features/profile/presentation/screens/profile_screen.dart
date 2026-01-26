import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:speech_to_text/speech_to_text.dart';

import '../../../../core/providers/auth_provider.dart';
import '../../../../core/providers/settings_provider.dart';
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

                    // Voice input language selection
                    Consumer(
                      builder: (context, ref, _) {
                        final settings = ref.watch(settingsProvider);
                        return ListTile(
                          leading: const Icon(Icons.mic_outlined),
                          title: const Text('Voice Input Language'),
                          subtitle: Text(
                            settings.speechLanguage == null
                                ? 'Auto (System)'
                                : _getLanguageLabel(settings.speechLanguage!),
                          ),
                          trailing: const Icon(Icons.chevron_right),
                          onTap: () => _showLanguageSelector(context, ref),
                        );
                      },
                    ),

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

  String _getLanguageLabel(String localeId) {
    // Common locale mappings
    final Map<String, String> localeLabels = {
      'en_US': 'English (US)',
      'en_GB': 'English (UK)',
      'en_AU': 'English (Australia)',
      'ru_RU': 'Russian',
      'uk_UA': 'Ukrainian',
      'de_DE': 'German',
      'fr_FR': 'French',
      'es_ES': 'Spanish (Spain)',
      'es_MX': 'Spanish (Mexico)',
      'it_IT': 'Italian',
      'pt_BR': 'Portuguese (Brazil)',
      'pt_PT': 'Portuguese (Portugal)',
      'zh_CN': 'Chinese (Simplified)',
      'zh_TW': 'Chinese (Traditional)',
      'ja_JP': 'Japanese',
      'ko_KR': 'Korean',
      'pl_PL': 'Polish',
      'nl_NL': 'Dutch',
      'tr_TR': 'Turkish',
      'ar_SA': 'Arabic',
      'he_IL': 'Hebrew',
      'hi_IN': 'Hindi',
    };

    return localeLabels[localeId] ?? localeId;
  }

  Future<void> _showLanguageSelector(BuildContext context, WidgetRef ref) async {
    final speech = SpeechToText();
    List<LocaleName> locales = [];

    try {
      final available = await speech.initialize();
      if (available) {
        locales = await speech.locales();
      }
    } catch (e) {
      // Speech not available
    }

    if (!context.mounted) return;

    final currentLang = ref.read(settingsProvider).speechLanguage;

    await showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      builder: (context) => DraggableScrollableSheet(
        initialChildSize: 0.6,
        minChildSize: 0.3,
        maxChildSize: 0.9,
        expand: false,
        builder: (context, scrollController) => Column(
          children: [
            Container(
              margin: const EdgeInsets.symmetric(vertical: 8),
              width: 32,
              height: 4,
              decoration: BoxDecoration(
                color: Theme.of(context).colorScheme.outline.withValues(alpha: 0.4),
                borderRadius: BorderRadius.circular(2),
              ),
            ),
            Padding(
              padding: const EdgeInsets.all(16),
              child: Text(
                'Voice Input Language',
                style: Theme.of(context).textTheme.titleLarge,
              ),
            ),
            const Divider(height: 1),
            Expanded(
              child: ListView(
                controller: scrollController,
                children: [
                  // Auto option
                  RadioListTile<String?>(
                    title: const Text('Auto (System)'),
                    subtitle: const Text('Use device language'),
                    value: null,
                    groupValue: currentLang,
                    onChanged: (value) {
                      ref.read(settingsProvider.notifier).setSpeechLanguage(null);
                      Navigator.pop(context);
                    },
                  ),
                  const Divider(height: 1),
                  // Available locales
                  ...locales.map((locale) => RadioListTile<String?>(
                    title: Text(locale.name),
                    subtitle: Text(locale.localeId),
                    value: locale.localeId,
                    groupValue: currentLang,
                    onChanged: (value) {
                      ref.read(settingsProvider.notifier).setSpeechLanguage(value);
                      Navigator.pop(context);
                    },
                  )),
                  if (locales.isEmpty)
                    const Padding(
                      padding: EdgeInsets.all(32),
                      child: Text(
                        'Speech recognition not available on this device.',
                        textAlign: TextAlign.center,
                      ),
                    ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
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
