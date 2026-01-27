import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';

import '../../../../core/models/api_key.dart';
import '../../../../core/providers/api_keys_provider.dart';

class ApiKeysScreen extends ConsumerStatefulWidget {
  const ApiKeysScreen({super.key});

  @override
  ConsumerState<ApiKeysScreen> createState() => _ApiKeysScreenState();
}

class _ApiKeysScreenState extends ConsumerState<ApiKeysScreen> {
  @override
  void initState() {
    super.initState();
    Future.microtask(() {
      ref.read(apiKeysProvider.notifier).loadKeys();
    });
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(apiKeysProvider);

    // Show new key dialog when a key is created
    ref.listen(apiKeysProvider, (previous, next) {
      if (next.newKey != null && previous?.newKey == null) {
        _showNewKeyDialog(context, next.newKey!);
      }
    });

    return Scaffold(
      appBar: AppBar(
        title: const Text('API Keys'),
      ),
      body: state.isLoading && state.keys.isEmpty
          ? const Center(child: CircularProgressIndicator())
          : state.keys.isEmpty
              ? _buildEmptyState(context)
              : _buildKeysList(context, state.keys),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => _showCreateKeyDialog(context),
        icon: const Icon(Icons.add),
        label: const Text('Create Key'),
      ),
    );
  }

  Widget _buildEmptyState(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.key_off_outlined,
              size: 64,
              color: Theme.of(context).colorScheme.outline,
            ),
            const SizedBox(height: 16),
            Text(
              'No API Keys',
              style: Theme.of(context).textTheme.titleLarge,
            ),
            const SizedBox(height: 8),
            Text(
              'Create an API key to connect MindNest with Claude Code or other tools.',
              textAlign: TextAlign.center,
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    color: Theme.of(context).colorScheme.onSurfaceVariant,
                  ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildKeysList(BuildContext context, List<ApiKey> keys) {
    return ListView.builder(
      padding: const EdgeInsets.only(bottom: 80),
      itemCount: keys.length,
      itemBuilder: (context, index) {
        final key = keys[index];
        return _ApiKeyTile(
          apiKey: key,
          onRevoke: () => _showRevokeDialog(context, key),
        );
      },
    );
  }

  Future<void> _showCreateKeyDialog(BuildContext context) async {
    final nameController = TextEditingController();
    bool writeAccess = false;

    await showDialog(
      context: context,
      builder: (context) => StatefulBuilder(
        builder: (context, setState) => AlertDialog(
          title: const Text('Create API Key'),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              TextField(
                controller: nameController,
                autofocus: true,
                decoration: const InputDecoration(
                  labelText: 'Key Name',
                  hintText: 'e.g., Claude Code',
                  border: OutlineInputBorder(),
                ),
              ),
              const SizedBox(height: 16),
              SwitchListTile(
                title: const Text('Write Access'),
                subtitle: const Text('Allow adding data to projects'),
                value: writeAccess,
                onChanged: (value) => setState(() => writeAccess = value),
                contentPadding: EdgeInsets.zero,
              ),
            ],
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('Cancel'),
            ),
            FilledButton(
              onPressed: () {
                final name = nameController.text.trim();
                if (name.isNotEmpty) {
                  ref.read(apiKeysProvider.notifier).createKey(
                        name,
                        writeAccess: writeAccess,
                      );
                  Navigator.pop(context);
                }
              },
              child: const Text('Create'),
            ),
          ],
        ),
      ),
    );

    nameController.dispose();
  }

  Future<void> _showNewKeyDialog(
      BuildContext context, CreateApiKeyResponse newKey) async {
    await showDialog(
      context: context,
      barrierDismissible: false,
      builder: (context) => AlertDialog(
        title: Row(
          children: [
            Icon(
              Icons.check_circle,
              color: Theme.of(context).colorScheme.primary,
            ),
            const SizedBox(width: 8),
            const Text('API Key Created'),
          ],
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Theme.of(context).colorScheme.errorContainer,
                borderRadius: BorderRadius.circular(8),
              ),
              child: Row(
                children: [
                  Icon(
                    Icons.warning_amber_rounded,
                    color: Theme.of(context).colorScheme.onErrorContainer,
                    size: 20,
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      'Copy this key now. It will not be shown again.',
                      style: TextStyle(
                        color: Theme.of(context).colorScheme.onErrorContainer,
                        fontWeight: FontWeight.w500,
                      ),
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),
            Text(
              'API Key:',
              style: Theme.of(context).textTheme.labelMedium,
            ),
            const SizedBox(height: 4),
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Theme.of(context).colorScheme.surfaceContainerHighest,
                borderRadius: BorderRadius.circular(8),
              ),
              child: Row(
                children: [
                  Expanded(
                    child: SelectableText(
                      newKey.key,
                      style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                            fontFamily: 'monospace',
                          ),
                    ),
                  ),
                  IconButton(
                    icon: const Icon(Icons.copy),
                    onPressed: () {
                      Clipboard.setData(ClipboardData(text: newKey.key));
                      ScaffoldMessenger.of(context).showSnackBar(
                        const SnackBar(
                          content: Text('API key copied to clipboard'),
                          duration: Duration(seconds: 2),
                        ),
                      );
                    },
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),
            Text(
              'Add to your Claude Code config:',
              style: Theme.of(context).textTheme.labelMedium,
            ),
            const SizedBox(height: 4),
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Theme.of(context).colorScheme.surfaceContainerHighest,
                borderRadius: BorderRadius.circular(8),
              ),
              child: SelectableText(
                '''"mindnest": {
  "url": "https://api.mindnest.one/mcp",
  "headers": {
    "X-API-Key": "${newKey.key}"
  }
}''',
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                      fontFamily: 'monospace',
                    ),
              ),
            ),
          ],
        ),
        actions: [
          FilledButton(
            onPressed: () {
              ref.read(apiKeysProvider.notifier).clearNewKey();
              Navigator.pop(context);
            },
            child: const Text('Done'),
          ),
        ],
      ),
    );
  }

  Future<void> _showRevokeDialog(BuildContext context, ApiKey key) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Revoke API Key'),
        content: Text(
          'Are you sure you want to revoke "${key.name}"? This action cannot be undone.',
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
            child: const Text('Revoke'),
          ),
        ],
      ),
    );

    if (confirmed == true) {
      await ref.read(apiKeysProvider.notifier).revokeKey(key.id);
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('API key revoked')),
        );
      }
    }
  }
}

class _ApiKeyTile extends StatelessWidget {
  final ApiKey apiKey;
  final VoidCallback onRevoke;

  const _ApiKeyTile({
    required this.apiKey,
    required this.onRevoke,
  });

  @override
  Widget build(BuildContext context) {
    final dateFormat = DateFormat.yMMMd();

    return ListTile(
      leading: CircleAvatar(
        backgroundColor: Theme.of(context).colorScheme.primaryContainer,
        child: Icon(
          Icons.key,
          color: Theme.of(context).colorScheme.onPrimaryContainer,
        ),
      ),
      title: Text(apiKey.name),
      subtitle: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            '${apiKey.keyPrefix}...',
            style: TextStyle(
              fontFamily: 'monospace',
              color: Theme.of(context).colorScheme.onSurfaceVariant,
            ),
          ),
          Row(
            children: [
              Chip(
                label: Text(
                  apiKey.hasWriteScope ? 'Read/Write' : 'Read Only',
                  style: Theme.of(context).textTheme.labelSmall,
                ),
                visualDensity: VisualDensity.compact,
                padding: EdgeInsets.zero,
                side: BorderSide.none,
                backgroundColor:
                    Theme.of(context).colorScheme.surfaceContainerHighest,
              ),
              const SizedBox(width: 8),
              if (apiKey.lastUsedAt != null)
                Text(
                  'Used ${dateFormat.format(apiKey.lastUsedAt!.toLocal())}',
                  style: Theme.of(context).textTheme.labelSmall?.copyWith(
                        color: Theme.of(context).colorScheme.onSurfaceVariant,
                      ),
                )
              else
                Text(
                  'Never used',
                  style: Theme.of(context).textTheme.labelSmall?.copyWith(
                        color: Theme.of(context).colorScheme.onSurfaceVariant,
                      ),
                ),
            ],
          ),
        ],
      ),
      trailing: IconButton(
        icon: const Icon(Icons.delete_outline),
        onPressed: onRevoke,
        color: Theme.of(context).colorScheme.error,
      ),
      isThreeLine: true,
    );
  }
}
