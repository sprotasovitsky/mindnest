// GENERATED CODE - DO NOT MODIFY BY HAND
// coverage:ignore-file
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

part of 'members_provider.dart';

// **************************************************************************
// FreezedGenerator
// **************************************************************************

// dart format off
T _$identity<T>(T value) => value;
/// @nodoc
mixin _$MembersState {

 bool get isLoading; List<Member> get members; String? get error;
/// Create a copy of MembersState
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$MembersStateCopyWith<MembersState> get copyWith => _$MembersStateCopyWithImpl<MembersState>(this as MembersState, _$identity);



@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is MembersState&&(identical(other.isLoading, isLoading) || other.isLoading == isLoading)&&const DeepCollectionEquality().equals(other.members, members)&&(identical(other.error, error) || other.error == error));
}


@override
int get hashCode => Object.hash(runtimeType,isLoading,const DeepCollectionEquality().hash(members),error);

@override
String toString() {
  return 'MembersState(isLoading: $isLoading, members: $members, error: $error)';
}


}

/// @nodoc
abstract mixin class $MembersStateCopyWith<$Res>  {
  factory $MembersStateCopyWith(MembersState value, $Res Function(MembersState) _then) = _$MembersStateCopyWithImpl;
@useResult
$Res call({
 bool isLoading, List<Member> members, String? error
});




}
/// @nodoc
class _$MembersStateCopyWithImpl<$Res>
    implements $MembersStateCopyWith<$Res> {
  _$MembersStateCopyWithImpl(this._self, this._then);

  final MembersState _self;
  final $Res Function(MembersState) _then;

/// Create a copy of MembersState
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? isLoading = null,Object? members = null,Object? error = freezed,}) {
  return _then(_self.copyWith(
isLoading: null == isLoading ? _self.isLoading : isLoading // ignore: cast_nullable_to_non_nullable
as bool,members: null == members ? _self.members : members // ignore: cast_nullable_to_non_nullable
as List<Member>,error: freezed == error ? _self.error : error // ignore: cast_nullable_to_non_nullable
as String?,
  ));
}

}


/// Adds pattern-matching-related methods to [MembersState].
extension MembersStatePatterns on MembersState {
/// A variant of `map` that fallback to returning `orElse`.
///
/// It is equivalent to doing:
/// ```dart
/// switch (sealedClass) {
///   case final Subclass value:
///     return ...;
///   case _:
///     return orElse();
/// }
/// ```

@optionalTypeArgs TResult maybeMap<TResult extends Object?>(TResult Function( _MembersState value)?  $default,{required TResult orElse(),}){
final _that = this;
switch (_that) {
case _MembersState() when $default != null:
return $default(_that);case _:
  return orElse();

}
}
/// A `switch`-like method, using callbacks.
///
/// Callbacks receives the raw object, upcasted.
/// It is equivalent to doing:
/// ```dart
/// switch (sealedClass) {
///   case final Subclass value:
///     return ...;
///   case final Subclass2 value:
///     return ...;
/// }
/// ```

@optionalTypeArgs TResult map<TResult extends Object?>(TResult Function( _MembersState value)  $default,){
final _that = this;
switch (_that) {
case _MembersState():
return $default(_that);}
}
/// A variant of `map` that fallback to returning `null`.
///
/// It is equivalent to doing:
/// ```dart
/// switch (sealedClass) {
///   case final Subclass value:
///     return ...;
///   case _:
///     return null;
/// }
/// ```

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>(TResult? Function( _MembersState value)?  $default,){
final _that = this;
switch (_that) {
case _MembersState() when $default != null:
return $default(_that);case _:
  return null;

}
}
/// A variant of `when` that fallback to an `orElse` callback.
///
/// It is equivalent to doing:
/// ```dart
/// switch (sealedClass) {
///   case Subclass(:final field):
///     return ...;
///   case _:
///     return orElse();
/// }
/// ```

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>(TResult Function( bool isLoading,  List<Member> members,  String? error)?  $default,{required TResult orElse(),}) {final _that = this;
switch (_that) {
case _MembersState() when $default != null:
return $default(_that.isLoading,_that.members,_that.error);case _:
  return orElse();

}
}
/// A `switch`-like method, using callbacks.
///
/// As opposed to `map`, this offers destructuring.
/// It is equivalent to doing:
/// ```dart
/// switch (sealedClass) {
///   case Subclass(:final field):
///     return ...;
///   case Subclass2(:final field2):
///     return ...;
/// }
/// ```

@optionalTypeArgs TResult when<TResult extends Object?>(TResult Function( bool isLoading,  List<Member> members,  String? error)  $default,) {final _that = this;
switch (_that) {
case _MembersState():
return $default(_that.isLoading,_that.members,_that.error);}
}
/// A variant of `when` that fallback to returning `null`
///
/// It is equivalent to doing:
/// ```dart
/// switch (sealedClass) {
///   case Subclass(:final field):
///     return ...;
///   case _:
///     return null;
/// }
/// ```

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>(TResult? Function( bool isLoading,  List<Member> members,  String? error)?  $default,) {final _that = this;
switch (_that) {
case _MembersState() when $default != null:
return $default(_that.isLoading,_that.members,_that.error);case _:
  return null;

}
}

}

/// @nodoc


class _MembersState implements MembersState {
  const _MembersState({this.isLoading = false, final  List<Member> members = const [], this.error}): _members = members;
  

@override@JsonKey() final  bool isLoading;
 final  List<Member> _members;
@override@JsonKey() List<Member> get members {
  if (_members is EqualUnmodifiableListView) return _members;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_members);
}

@override final  String? error;

/// Create a copy of MembersState
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$MembersStateCopyWith<_MembersState> get copyWith => __$MembersStateCopyWithImpl<_MembersState>(this, _$identity);



@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _MembersState&&(identical(other.isLoading, isLoading) || other.isLoading == isLoading)&&const DeepCollectionEquality().equals(other._members, _members)&&(identical(other.error, error) || other.error == error));
}


@override
int get hashCode => Object.hash(runtimeType,isLoading,const DeepCollectionEquality().hash(_members),error);

@override
String toString() {
  return 'MembersState(isLoading: $isLoading, members: $members, error: $error)';
}


}

/// @nodoc
abstract mixin class _$MembersStateCopyWith<$Res> implements $MembersStateCopyWith<$Res> {
  factory _$MembersStateCopyWith(_MembersState value, $Res Function(_MembersState) _then) = __$MembersStateCopyWithImpl;
@override @useResult
$Res call({
 bool isLoading, List<Member> members, String? error
});




}
/// @nodoc
class __$MembersStateCopyWithImpl<$Res>
    implements _$MembersStateCopyWith<$Res> {
  __$MembersStateCopyWithImpl(this._self, this._then);

  final _MembersState _self;
  final $Res Function(_MembersState) _then;

/// Create a copy of MembersState
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? isLoading = null,Object? members = null,Object? error = freezed,}) {
  return _then(_MembersState(
isLoading: null == isLoading ? _self.isLoading : isLoading // ignore: cast_nullable_to_non_nullable
as bool,members: null == members ? _self._members : members // ignore: cast_nullable_to_non_nullable
as List<Member>,error: freezed == error ? _self.error : error // ignore: cast_nullable_to_non_nullable
as String?,
  ));
}


}

// dart format on
