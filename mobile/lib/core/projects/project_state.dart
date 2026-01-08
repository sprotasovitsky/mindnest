import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../api/api_client.dart';

class Project {
  final String id;
  final String name;
  final String? description;
  final String ownerId;

  Project({
    required this.id,
    required this.name,
    this.description,
    required this.ownerId,
  });

  factory Project.fromJson(Map<String, dynamic> json) {
    return Project(
      id: json['id'],
      name: json['name'],
      description: json['description'],
      ownerId: json['owner_id'] ?? '',
    );
  }

  bool get needsOnboarding => description == null || description!.isEmpty;
}

class ProjectState {
  final bool isLoading;
  final List<Project> projects;
  final Project? currentProject;
  final String? error;

  const ProjectState({
    this.isLoading = false,
    this.projects = const [],
    this.currentProject,
    this.error,
  });

  ProjectState copyWith({
    bool? isLoading,
    List<Project>? projects,
    Project? currentProject,
    String? error,
  }) {
    return ProjectState(
      isLoading: isLoading ?? this.isLoading,
      projects: projects ?? this.projects,
      currentProject: currentProject ?? this.currentProject,
      error: error,
    );
  }
}

class ProjectNotifier extends StateNotifier<ProjectState> {
  final ApiClient _apiClient;

  ProjectNotifier(this._apiClient) : super(const ProjectState());

  Future<void> loadProjects() async {
    state = state.copyWith(isLoading: true, error: null);
    try {
      final response = await _apiClient.getProjects();
      final projects = response.map((json) => Project.fromJson(json)).toList();

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
        error: 'Failed to load projects',
      );
    }
  }

  void selectProject(Project project) {
    state = state.copyWith(currentProject: project);
  }

  Future<Project?> createProject(String name, String? description) async {
    try {
      final response = await _apiClient.createProject(name, description);
      final project = Project.fromJson(response);
      state = state.copyWith(
        projects: [...state.projects, project],
        currentProject: project,
      );
      return project;
    } catch (e) {
      state = state.copyWith(error: 'Failed to create project');
      return null;
    }
  }

  Future<Project?> updateProject(String projectId, {String? name, String? description}) async {
    try {
      final response = await _apiClient.updateProject(projectId, name: name, description: description);
      final updatedProject = Project.fromJson(response);

      final updatedProjects = state.projects.map((p) {
        return p.id == projectId ? updatedProject : p;
      }).toList();

      state = state.copyWith(
        projects: updatedProjects,
        currentProject: state.currentProject?.id == projectId ? updatedProject : state.currentProject,
      );
      return updatedProject;
    } catch (e) {
      state = state.copyWith(error: 'Failed to update project');
      return null;
    }
  }
}

final projectProvider = StateNotifierProvider<ProjectNotifier, ProjectState>((ref) {
  final apiClient = ref.watch(apiClientProvider);
  return ProjectNotifier(apiClient);
});
