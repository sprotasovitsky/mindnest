import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/models/project.dart';
import '../../../../core/providers/project_provider.dart';
import '../../../../shared/widgets/widgets.dart';
import '../widgets/create_project_modal.dart';

class ProjectsListScreen extends ConsumerWidget {
  const ProjectsListScreen({super.key});

  void _showCreateProjectModal(BuildContext context, WidgetRef ref) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      builder: (context) => Padding(
        padding: EdgeInsets.only(
          bottom: MediaQuery.of(context).viewInsets.bottom,
        ),
        child: const CreateProjectModal(),
      ),
    );
  }

  void _openProject(BuildContext context, WidgetRef ref, Project project) {
    ref.read(projectsProvider.notifier).selectProject(project);
    context.push('/chat');
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final projectState = ref.watch(projectsProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('MindNest'),
        actions: [
          IconButton(
            icon: const Icon(Icons.person_outline),
            onPressed: () => context.push('/profile'),
            tooltip: 'Profile',
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton(
        key: const Key('create_project_fab'),
        onPressed: () => _showCreateProjectModal(context, ref),
        child: const Icon(Icons.add),
      ),
      body: projectState.isLoading
          ? const LoadingOverlay(message: 'Loading projects...')
          : projectState.error != null
              ? ErrorView(
                  message: projectState.error!,
                  onRetry: () => ref.read(projectsProvider.notifier).loadProjects(),
                )
              : projectState.projects.isEmpty
                  ? EmptyState(
                      message: 'No projects yet\nCreate your first project to get started',
                      actionLabel: 'Create Project',
                      onAction: () => _showCreateProjectModal(context, ref),
                      icon: Icons.folder_open_outlined,
                    )
                  : _buildProjectList(context, ref, projectState.projects),
    );
  }

  Widget _buildProjectList(BuildContext context, WidgetRef ref, List<Project> projects) {
    return RefreshIndicator(
      onRefresh: () => ref.read(projectsProvider.notifier).loadProjects(),
      child: ListView.builder(
        padding: const EdgeInsets.symmetric(vertical: 8),
        itemCount: projects.length,
        itemBuilder: (_, index) {
          final project = projects[index];
          return _ProjectCard(
            project: project,
            onTap: () => _openProject(context, ref, project),
          );
        },
      ),
    );
  }
}

class _ProjectCard extends StatelessWidget {
  final Project project;
  final VoidCallback onTap;

  const _ProjectCard({
    required this.project,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
      child: ListTile(
        leading: CircleAvatar(
          backgroundColor: Theme.of(context).colorScheme.primaryContainer,
          child: Icon(
            Icons.folder_outlined,
            color: Theme.of(context).colorScheme.onPrimaryContainer,
          ),
        ),
        title: Text(
          project.name,
          style: const TextStyle(fontWeight: FontWeight.w500),
        ),
        subtitle: project.description != null
            ? Text(
                project.description!,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
              )
            : null,
        trailing: const Icon(Icons.chevron_right),
        onTap: onTap,
      ),
    );
  }
}
