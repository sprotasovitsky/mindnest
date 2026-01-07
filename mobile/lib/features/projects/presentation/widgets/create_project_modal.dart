import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../../core/projects/project_state.dart';

class CreateProjectModal extends ConsumerStatefulWidget {
  const CreateProjectModal({super.key});

  @override
  ConsumerState<CreateProjectModal> createState() => _CreateProjectModalState();
}

class _CreateProjectModalState extends ConsumerState<CreateProjectModal> {
  final _nameController = TextEditingController();
  final _formKey = GlobalKey<FormState>();
  bool _isCreating = false;

  @override
  void dispose() {
    _nameController.dispose();
    super.dispose();
  }

  Future<void> _createProject() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() => _isCreating = true);

    final project = await ref.read(projectProvider.notifier).createProject(
          _nameController.text.trim(),
          null,
        );

    setState(() => _isCreating = false);

    if (project != null && mounted) {
      Navigator.pop(context);
      context.push('/chat');
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
                    'New Project',
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
                key: const Key('project_name_field'),
                controller: _nameController,
                autofocus: true,
                decoration: const InputDecoration(
                  labelText: 'Project Name',
                  hintText: 'Enter project name',
                  border: OutlineInputBorder(),
                  prefixIcon: Icon(Icons.folder_outlined),
                ),
                textInputAction: TextInputAction.done,
                onFieldSubmitted: (_) => _createProject(),
                validator: (value) {
                  if (value == null || value.trim().isEmpty) {
                    return 'Please enter a project name';
                  }
                  return null;
                },
              ),
              const SizedBox(height: 24),
              FilledButton(
                onPressed: _isCreating ? null : _createProject,
                child: Padding(
                  padding: const EdgeInsets.symmetric(vertical: 12),
                  child: _isCreating
                      ? const SizedBox(
                          height: 20,
                          width: 20,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                      : const Text('Create'),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
