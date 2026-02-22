import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/models/project.dart';
import '../../../../core/providers/project_provider.dart';
import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_spacing.dart';
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
      floatingActionButton: Container(
        decoration: const BoxDecoration(
          borderRadius: BorderRadius.all(Radius.circular(AppSpacing.radiusLg)),
          boxShadow: [
            BoxShadow(
              color: AppColors.indigoGlow,
              blurRadius: 16,
              offset: Offset(0, 4),
            ),
          ],
        ),
        child: FloatingActionButton(
          key: const Key('create_project_fab'),
          onPressed: () => _showCreateProjectModal(context, ref),
          child: const Icon(Icons.add),
        ),
      ),
      body: projectState.isLoading
          ? const LoadingOverlay(message: 'Loading projects...')
          : RefreshIndicator(
              onRefresh: () => ref.read(projectsProvider.notifier).loadProjects(),
              child: projectState.error != null
                  ? _buildScrollableError(context, ref, projectState.error!)
                  : projectState.projects.isEmpty
                      ? _buildScrollableEmpty(context, ref)
                      : _buildProjectList(context, ref, projectState.projects),
            ),
    );
  }

  Widget _buildProjectList(BuildContext context, WidgetRef ref, List<Project> projects) {
    return ListView.builder(
      physics: const AlwaysScrollableScrollPhysics(),
      padding: const EdgeInsets.symmetric(vertical: 8, horizontal: 16),
      itemCount: projects.length,
      itemBuilder: (_, index) {
        final project = projects[index];
        return _ProjectCard(
          project: project,
          onTap: () => _openProject(context, ref, project),
        );
      },
    );
  }

  Widget _buildScrollableEmpty(BuildContext context, WidgetRef ref) {
    return CustomScrollView(
      physics: const AlwaysScrollableScrollPhysics(),
      slivers: [
        SliverFillRemaining(
          child: EmptyState(
            message: 'No projects yet\nCreate your first project or pull to refresh',
            actionLabel: 'Create Project',
            onAction: () => _showCreateProjectModal(context, ref),
            icon: Icons.folder_open_outlined,
          ),
        ),
      ],
    );
  }

  Widget _buildScrollableError(BuildContext context, WidgetRef ref, String error) {
    return CustomScrollView(
      physics: const AlwaysScrollableScrollPhysics(),
      slivers: [
        SliverFillRemaining(
          child: ErrorView(
            message: error,
            onRetry: () => ref.read(projectsProvider.notifier).loadProjects(),
          ),
        ),
      ],
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
    final theme = Theme.of(context);
    final colorScheme = theme.colorScheme;
    final isDark = theme.brightness == Brightness.dark;

    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          onTap: onTap,
          borderRadius: AppSpacing.borderRadiusXl,
          child: Container(
            padding: const EdgeInsets.all(AppSpacing.lg),
            decoration: BoxDecoration(
              gradient: isDark
                  ? const LinearGradient(
                      begin: Alignment.topLeft,
                      end: Alignment.bottomRight,
                      colors: [
                        AppColors.darkSurfaceContainerHighest,
                        AppColors.darkSurfaceContainer,
                      ],
                    )
                  : null,
              color: isDark ? null : colorScheme.surfaceContainerHighest,
              borderRadius: AppSpacing.borderRadiusXl,
              border: Border.all(color: colorScheme.outlineVariant),
            ),
            child: Row(
              children: [
                Container(
                  width: 48,
                  height: 48,
                  decoration: BoxDecoration(
                    color: colorScheme.primaryContainer,
                    borderRadius: AppSpacing.borderRadiusMd,
                  ),
                  child: Icon(
                    Icons.folder_outlined,
                    color: colorScheme.onPrimaryContainer,
                  ),
                ),
                const SizedBox(width: AppSpacing.lg),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        project.name,
                        style: theme.textTheme.titleMedium,
                      ),
                      if (project.description != null) ...[
                        const SizedBox(height: 4),
                        Text(
                          project.description!,
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                          style: theme.textTheme.bodySmall?.copyWith(
                            color: colorScheme.onSurfaceVariant,
                          ),
                        ),
                      ],
                    ],
                  ),
                ),
                Icon(
                  Icons.chevron_right,
                  color: colorScheme.onSurfaceVariant,
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
