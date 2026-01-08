import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/providers/project_provider.dart';
import '../../../../shared/widgets/widgets.dart';

class ProjectSettingsSheet extends ConsumerStatefulWidget {
  const ProjectSettingsSheet({super.key});

  @override
  ConsumerState<ProjectSettingsSheet> createState() => _ProjectSettingsSheetState();
}

class _ProjectSettingsSheetState extends ConsumerState<ProjectSettingsSheet> {
  final _nameController = TextEditingController();
  final _formKey = GlobalKey<FormState>();
  bool _isSaving = false;

  @override
  void initState() {
    super.initState();
    final currentProject = ref.read(projectsProvider).currentProject;
    if (currentProject != null) {
      _nameController.text = currentProject.name;
    }
  }

  @override
  void dispose() {
    _nameController.dispose();
    super.dispose();
  }

  Future<void> _saveProject() async {
    if (!_formKey.currentState!.validate()) return;

    final currentProject = ref.read(projectsProvider).currentProject;
    if (currentProject == null) return;

    setState(() => _isSaving = true);

    final updatedProject = await ref.read(projectsProvider.notifier).updateProject(
          currentProject.id,
          name: _nameController.text.trim(),
        );

    setState(() => _isSaving = false);

    if (updatedProject != null && mounted) {
      Navigator.pop(context);
      showSuccessSnackBar(context, 'Project updated');
    } else if (mounted) {
      showErrorSnackBar(context, 'Failed to update project');
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
                    'Project Settings',
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
                controller: _nameController,
                decoration: const InputDecoration(
                  labelText: 'Project Name',
                  border: OutlineInputBorder(),
                  prefixIcon: Icon(Icons.folder_outlined),
                ),
                textInputAction: TextInputAction.done,
                onFieldSubmitted: (_) => _saveProject(),
                validator: (value) {
                  if (value == null || value.trim().isEmpty) {
                    return 'Please enter a project name';
                  }
                  return null;
                },
              ),
              const SizedBox(height: 24),
              FilledButton(
                onPressed: _isSaving ? null : _saveProject,
                child: Padding(
                  padding: const EdgeInsets.symmetric(vertical: 12),
                  child: _isSaving
                      ? const SizedBox(
                          height: 20,
                          width: 20,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                      : const Text('Save'),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
