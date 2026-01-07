import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../../core/projects/project_state.dart';
import '../widgets/create_project_modal.dart';

class ProjectsListScreen extends ConsumerStatefulWidget {
  const ProjectsListScreen({super.key});

  @override
  ConsumerState<ProjectsListScreen> createState() => _ProjectsListScreenState();
}

class _ProjectsListScreenState extends ConsumerState<ProjectsListScreen> {
  @override
  void initState() {
    super.initState();
    Future.microtask(() {
      ref.read(projectProvider.notifier).loadProjects();
    });
  }

  void _showCreateProjectModal() {
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

  void _openProject(Project project) {
    ref.read(projectProvider.notifier).selectProject(project);
    context.push('/chat');
  }

  @override
  Widget build(BuildContext context) {
    final projectState = ref.watch(projectProvider);

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
        onPressed: _showCreateProjectModal,
        child: const Icon(Icons.add),
      ),
      body: projectState.isLoading
          ? const Center(child: CircularProgressIndicator())
          : projectState.projects.isEmpty
              ? _buildEmptyState()
              : _buildProjectList(projectState.projects),
    );
  }

  Widget _buildEmptyState() {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.folder_open_outlined,
              size: 80,
              color: Theme.of(context).colorScheme.outline,
            ),
            const SizedBox(height: 16),
            Text(
              'No projects yet',
              style: Theme.of(context).textTheme.titleLarge,
            ),
            const SizedBox(height: 8),
            Text(
              'Create your first project to get started',
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    color: Theme.of(context).colorScheme.onSurfaceVariant,
                  ),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 24),
            FilledButton.icon(
              onPressed: _showCreateProjectModal,
              icon: const Icon(Icons.add),
              label: const Text('Create Project'),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildProjectList(List<Project> projects) {
    return RefreshIndicator(
      onRefresh: () => ref.read(projectProvider.notifier).loadProjects(),
      child: ListView.builder(
        padding: const EdgeInsets.symmetric(vertical: 8),
        itemCount: projects.length,
        itemBuilder: (context, index) {
          final project = projects[index];
          return _ProjectCard(
            project: project,
            onTap: () => _openProject(project),
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
