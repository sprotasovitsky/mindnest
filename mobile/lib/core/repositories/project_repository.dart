import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../api/api_client.dart';
import '../error/app_error.dart';
import '../models/project.dart';

part 'project_repository.g.dart';

/// Repository for project operations
abstract class ProjectRepository {
  Future<List<Project>> getProjects();
  Future<Project> createProject(String name, String? description);
  Future<Project> updateProject(String projectId,
      {String? name, String? description});
}

class ProjectRepositoryImpl implements ProjectRepository {
  final ApiClient _apiClient;

  ProjectRepositoryImpl(this._apiClient);

  @override
  Future<List<Project>> getProjects() async {
    try {
      final response = await _apiClient.getProjects();
      return response.map((json) => Project.fromJson(json)).toList();
    } on DioException catch (e) {
      throw appErrorFromDioException(e);
    }
  }

  @override
  Future<Project> createProject(String name, String? description) async {
    try {
      final response = await _apiClient.createProject(name, description);
      return Project.fromJson(response);
    } on DioException catch (e) {
      throw appErrorFromDioException(e);
    }
  }

  @override
  Future<Project> updateProject(String projectId,
      {String? name, String? description}) async {
    try {
      final response = await _apiClient.updateProject(projectId,
          name: name, description: description);
      return Project.fromJson(response);
    } on DioException catch (e) {
      throw appErrorFromDioException(e);
    }
  }
}

@riverpod
ProjectRepository projectRepository(Ref ref) {
  final apiClient = ref.watch(apiClientProvider);
  return ProjectRepositoryImpl(apiClient);
}
