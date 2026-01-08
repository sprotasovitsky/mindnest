import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../api/api_client.dart';

class Member {
  final String id;
  final String email;
  final String? name;
  final String role;

  Member({
    required this.id,
    required this.email,
    this.name,
    required this.role,
  });

  factory Member.fromJson(Map<String, dynamic> json) {
    return Member(
      id: json['id'] ?? json['user_id'] ?? '',
      email: json['email'] ?? '',
      name: json['name'],
      role: json['role'] ?? 'member',
    );
  }
}

class MembersState {
  final bool isLoading;
  final List<Member> members;
  final String? error;

  const MembersState({
    this.isLoading = false,
    this.members = const [],
    this.error,
  });

  MembersState copyWith({
    bool? isLoading,
    List<Member>? members,
    String? error,
  }) {
    return MembersState(
      isLoading: isLoading ?? this.isLoading,
      members: members ?? this.members,
      error: error,
    );
  }
}

class MembersNotifier extends StateNotifier<MembersState> {
  final ApiClient _apiClient;

  MembersNotifier(this._apiClient) : super(const MembersState());

  Future<void> loadMembers(String projectId) async {
    state = state.copyWith(isLoading: true, error: null);
    try {
      final response = await _apiClient.getProjectMembers(projectId);
      final members = response.map((json) => Member.fromJson(json as Map<String, dynamic>)).toList();
      state = state.copyWith(
        isLoading: false,
        members: members,
      );
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        error: 'Failed to load members',
      );
    }
  }

  Future<bool> addMember(String projectId, String email) async {
    try {
      final response = await _apiClient.addProjectMember(projectId, email);
      final member = Member.fromJson(response);
      state = state.copyWith(
        members: [...state.members, member],
      );
      return true;
    } catch (e) {
      state = state.copyWith(error: 'Failed to add member');
      return false;
    }
  }

  void clearMembers() {
    state = const MembersState();
  }
}

final membersProvider = StateNotifierProvider<MembersNotifier, MembersState>((ref) {
  final apiClient = ref.watch(apiClientProvider);
  return MembersNotifier(apiClient);
});
