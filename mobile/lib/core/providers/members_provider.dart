import 'package:freezed_annotation/freezed_annotation.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../error/app_error.dart';
import '../models/member.dart';
import '../repositories/members_repository.dart';

part 'members_provider.freezed.dart';
part 'members_provider.g.dart';

@freezed
sealed class MembersState with _$MembersState {
  const factory MembersState({
    @Default(false) bool isLoading,
    @Default([]) List<Member> members,
    String? error,
  }) = _MembersState;
}

@riverpod
class Members extends _$Members {
  @override
  MembersState build() {
    return const MembersState();
  }

  Future<void> loadMembers(String projectId) async {
    state = state.copyWith(isLoading: true, error: null);
    try {
      final repository = ref.read(membersRepositoryProvider);
      final members = await repository.getMembers(projectId);
      state = state.copyWith(
        isLoading: false,
        members: members,
      );
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        error: e.toUserMessage(),
      );
    }
  }

  Future<bool> addMember(String projectId, String email) async {
    try {
      final repository = ref.read(membersRepositoryProvider);
      final member = await repository.addMember(projectId, email);
      state = state.copyWith(
        members: [...state.members, member],
      );
      return true;
    } catch (e) {
      state = state.copyWith(error: e.toUserMessage());
      return false;
    }
  }

  void clearMembers() {
    state = const MembersState();
  }
}
