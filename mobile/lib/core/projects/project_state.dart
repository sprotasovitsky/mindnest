import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../api/api_client.dart';

class Project {
  final String id;
  final String name;
  final String? description;

  Project({
    required this.id,
    required this.name,
    this.description,
  });

  factory Project.fromJson(Map<String, dynamic> json) {
    return Project(
      id: json['id'],
      name: json['name'],
      description: json['description'],
    );
  }
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
      state = state.copyWith(
        isLoading: false,
        projects: projects,
        currentProject: state.currentProject ?? (projects.isNotEmpty ? projects.first : null),
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
}

final projectProvider = StateNotifierProvider<ProjectNotifier, ProjectState>((ref) {
  final apiClient = ref.watch(apiClientProvider);
  return ProjectNotifier(apiClient);
});
