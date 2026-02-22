import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/providers/members_provider.dart';
import '../../../../core/providers/project_provider.dart';
import '../../../../shared/widgets/widgets.dart';

class AddMemberModal extends ConsumerStatefulWidget {
  const AddMemberModal({super.key});

  @override
  ConsumerState<AddMemberModal> createState() => _AddMemberModalState();
}

class _AddMemberModalState extends ConsumerState<AddMemberModal> {
  final _emailController = TextEditingController();
  final _formKey = GlobalKey<FormState>();
  bool _isAdding = false;

  @override
  void dispose() {
    _emailController.dispose();
    super.dispose();
  }

  Future<void> _addMember() async {
    if (!_formKey.currentState!.validate()) return;

    final currentProject = ref.read(projectsProvider).currentProject;
    if (currentProject == null) return;

    setState(() => _isAdding = true);

    final success = await ref.read(membersProvider.notifier).addMember(
          currentProject.id,
          _emailController.text.trim(),
        );

    setState(() => _isAdding = false);

    if (success && mounted) {
      Navigator.pop(context);
      showSuccessSnackBar(context, 'Member added successfully');
    } else if (mounted) {
      showErrorSnackBar(context, 'Failed to add member');
    }
  }

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Form(
          key: _formKey,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(
                    'Add Member',
                    style: Theme.of(context).textTheme.titleLarge,
                  ),
                  IconButton(
                    icon: const Icon(Icons.close),
                    onPressed: () => Navigator.pop(context),
                  ),
                ],
              ),
              const SizedBox(height: 24),
              TextFormField(
                key: const Key('member_email_field'),
                controller: _emailController,
                autofocus: true,
                decoration: const InputDecoration(
                  labelText: 'Email',
                  hintText: 'Enter member email',
                  prefixIcon: Icon(Icons.email_outlined),
                ),
                keyboardType: TextInputType.emailAddress,
                textInputAction: TextInputAction.done,
                onFieldSubmitted: (_) => _addMember(),
                validator: (value) {
                  if (value == null || value.trim().isEmpty) {
                    return 'Please enter an email';
                  }
                  if (!value.contains('@')) {
                    return 'Please enter a valid email';
                  }
                  return null;
                },
              ),
              const SizedBox(height: 24),
              FilledButton(
                onPressed: _isAdding ? null : _addMember,
                child: Padding(
                  padding: const EdgeInsets.symmetric(vertical: 12),
                  child: _isAdding
                      ? const SizedBox(
                          height: 20,
                          width: 20,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                      : const Text('Add'),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
