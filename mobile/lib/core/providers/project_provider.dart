import 'package:freezed_annotation/freezed_annotation.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../error/app_error.dart';
import '../models/project.dart';
import '../repositories/project_repository.dart';

part 'project_provider.freezed.dart';
part 'project_provider.g.dart';

@freezed
class ProjectState with _$ProjectState {
  const factory ProjectState({
    @Default(true) bool isLoading,
    @Default([]) List<Project> projects,
    Project? currentProject,
    String? error,
  }) = _ProjectState;
}

@riverpod
class Projects extends _$Projects {
  @override
  ProjectState build() {
    _loadProjects();
    return const ProjectState();
  }

  /// Private method for internal loading (doesn't set isLoading since default is true)
  Future<void> _loadProjects() async {
    try {
      final repository = ref.read(projectRepositoryProvider);
      final projects = await repository.getProjects();

      // Update currentProject with fresh data from server
      Project? updatedCurrentProject;
      if (state.currentProject != null) {
        updatedCurrentProject = projects.firstWhere(
          (p) => p.id == state.currentProject!.id,
          orElse: () => state.currentProject!,
        );
      } else if (projects.isNotEmpty) {
        updatedCurrentProject = projects.first;
      }

      state = state.copyWith(
        isLoading: false,
        projects: projects,
        currentProject: updatedCurrentProject,
      );
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        error: e.toUserMessage(),
      );
    }
  }

  /// Public method for pull-to-refresh
  Future<void> loadProjects() async {
    state = state.copyWith(isLoading: true, error: null);
    await _loadProjects();
  }

  void selectProject(Project project) {
    state = state.copyWith(currentProject: project);
  }

  Future<Project?> createProject(String name, String? description) async {
    try {
      final repository = ref.read(projectRepositoryProvider);
      final project = await repository.createProject(name, description);
      state = state.copyWith(
        projects: [...state.projects, project],
        currentProject: project,
      );
      return project;
    } catch (e) {
      state = state.copyWith(error: e.toUserMessage());
      return null;
    }
  }

  Future<Project?> updateProject(String projectId,
      {String? name, String? description}) async {
    try {
      final repository = ref.read(projectRepositoryProvider);
      final updatedProject = await repository.updateProject(projectId,
          name: name, description: description);

      final updatedProjects = state.projects.map((p) {
        return p.id == projectId ? updatedProject : p;
      }).toList();

      state = state.copyWith(
        projects: updatedProjects,
        currentProject: state.currentProject?.id == projectId
            ? updatedProject
            : state.currentProject,
      );
      return updatedProject;
    } catch (e) {
      state = state.copyWith(error: e.toUserMessage());
      return null;
    }
  }
}
