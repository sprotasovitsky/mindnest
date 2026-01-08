import 'package:dio/dio.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../api/api_client.dart';
import '../error/app_error.dart';
import '../models/member.dart';

part 'members_repository.g.dart';

/// Repository for project members operations
abstract class MembersRepository {
  Future<List<Member>> getMembers(String projectId);
  Future<Member> addMember(String projectId, String email);
}

class MembersRepositoryImpl implements MembersRepository {
  final ApiClient _apiClient;

  MembersRepositoryImpl(this._apiClient);

  @override
  Future<List<Member>> getMembers(String projectId) async {
    try {
      final response = await _apiClient.getProjectMembers(projectId);
      return response
          .map((json) => Member.fromJson(json as Map<String, dynamic>))
          .toList();
    } on DioException catch (e) {
      throw NetworkError.fromDioException(e);
    }
  }

  @override
  Future<Member> addMember(String projectId, String email) async {
    try {
      final response = await _apiClient.addProjectMember(projectId, email);
      return Member.fromJson(response);
    } on DioException catch (e) {
      throw NetworkError.fromDioException(e);
    }
  }
}

@riverpod
MembersRepository membersRepository(MembersRepositoryRef ref) {
  final apiClient = ref.watch(apiClientProvider);
  return MembersRepositoryImpl(apiClient);
}
