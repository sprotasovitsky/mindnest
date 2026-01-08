import 'package:freezed_annotation/freezed_annotation.dart';

part 'member.freezed.dart';
part 'member.g.dart';

@freezed
class Member with _$Member {
  const factory Member({
    required String id,
    required String email,
    String? name,
    @Default('member') String role,
  }) = _Member;

  factory Member.fromJson(Map<String, dynamic> json) => _$MemberFromJson({
        'id': json['id'] ?? json['user_id'] ?? '',
        'email': json['email'] ?? '',
        'name': json['name'],
        'role': json['role'] ?? 'member',
      });
}
