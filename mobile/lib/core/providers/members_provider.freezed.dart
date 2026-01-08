// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

part of 'members_provider.dart';

// **************************************************************************
// FreezedGenerator
// **************************************************************************

T _$identity<T>(T value) => value;

final _privateConstructorUsedError = UnsupportedError(
    'It seems like you constructed your class using `MyClass._()`. This constructor is only meant to be used by freezed and you are not supposed to need it nor use it.\nPlease check the documentation here for more information: https://github.com/rrousselGit/freezed#adding-getters-and-methods-to-our-models');

/// @nodoc
mixin _$MembersState {
  bool get isLoading => throw _privateConstructorUsedError;
  List<Member> get members => throw _privateConstructorUsedError;
  String? get error => throw _privateConstructorUsedError;

  /// Create a copy of MembersState
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $MembersStateCopyWith<MembersState> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $MembersStateCopyWith<$Res> {
  factory $MembersStateCopyWith(
          MembersState value, $Res Function(MembersState) then) =
      _$MembersStateCopyWithImpl<$Res, MembersState>;
  @useResult
  $Res call({bool isLoading, List<Member> members, String? error});
}

/// @nodoc
class _$MembersStateCopyWithImpl<$Res, $Val extends MembersState>
    implements $MembersStateCopyWith<$Res> {
  _$MembersStateCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of MembersState
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? isLoading = null,
    Object? members = null,
    Object? error = freezed,
  }) {
    return _then(_value.copyWith(
      isLoading: null == isLoading
          ? _value.isLoading
          : isLoading // ignore: cast_nullable_to_non_nullable
              as bool,
      members: null == members
          ? _value.members
          : members // ignore: cast_nullable_to_non_nullable
              as List<Member>,
      error: freezed == error
          ? _value.error
          : error // ignore: cast_nullable_to_non_nullable
              as String?,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$MembersStateImplCopyWith<$Res>
    implements $MembersStateCopyWith<$Res> {
  factory _$$MembersStateImplCopyWith(
          _$MembersStateImpl value, $Res Function(_$MembersStateImpl) then) =
      __$$MembersStateImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call({bool isLoading, List<Member> members, String? error});
}

/// @nodoc
class __$$MembersStateImplCopyWithImpl<$Res>
    extends _$MembersStateCopyWithImpl<$Res, _$MembersStateImpl>
    implements _$$MembersStateImplCopyWith<$Res> {
  __$$MembersStateImplCopyWithImpl(
      _$MembersStateImpl _value, $Res Function(_$MembersStateImpl) _then)
      : super(_value, _then);

  /// Create a copy of MembersState
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? isLoading = null,
    Object? members = null,
    Object? error = freezed,
  }) {
    return _then(_$MembersStateImpl(
      isLoading: null == isLoading
          ? _value.isLoading
          : isLoading // ignore: cast_nullable_to_non_nullable
              as bool,
      members: null == members
          ? _value._members
          : members // ignore: cast_nullable_to_non_nullable
              as List<Member>,
      error: freezed == error
          ? _value.error
          : error // ignore: cast_nullable_to_non_nullable
              as String?,
    ));
  }
}

/// @nodoc

class _$MembersStateImpl implements _MembersState {
  const _$MembersStateImpl(
      {this.isLoading = false,
      final List<Member> members = const [],
      this.error})
      : _members = members;

  @override
  @JsonKey()
  final bool isLoading;
  final List<Member> _members;
  @override
  @JsonKey()
  List<Member> get members {
    if (_members is EqualUnmodifiableListView) return _members;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_members);
  }

  @override
  final String? error;

  @override
  String toString() {
    return 'MembersState(isLoading: $isLoading, members: $members, error: $error)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$MembersStateImpl &&
            (identical(other.isLoading, isLoading) ||
                other.isLoading == isLoading) &&
            const DeepCollectionEquality().equals(other._members, _members) &&
            (identical(other.error, error) || other.error == error));
  }

  @override
  int get hashCode => Object.hash(runtimeType, isLoading,
      const DeepCollectionEquality().hash(_members), error);

  /// Create a copy of MembersState
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$MembersStateImplCopyWith<_$MembersStateImpl> get copyWith =>
      __$$MembersStateImplCopyWithImpl<_$MembersStateImpl>(this, _$identity);
}

abstract class _MembersState implements MembersState {
  const factory _MembersState(
      {final bool isLoading,
      final List<Member> members,
      final String? error}) = _$MembersStateImpl;

  @override
  bool get isLoading;
  @override
  List<Member> get members;
  @override
  String? get error;

  /// Create a copy of MembersState
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$MembersStateImplCopyWith<_$MembersStateImpl> get copyWith =>
      throw _privateConstructorUsedError;
}
