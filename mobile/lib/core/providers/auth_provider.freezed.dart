// GENERATED CODE - DO NOT MODIFY BY HAND
// coverage:ignore-file
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

part of 'auth_provider.dart';

// **************************************************************************
// FreezedGenerator
// **************************************************************************

// dart format off
T _$identity<T>(T value) => value;
/// @nodoc
mixin _$AuthState implements DiagnosticableTreeMixin {

 bool get isLoading; bool get isAuthenticated; String? get userId; String? get email; String? get name; bool get emailVerified; int get tokensUsed; int get tokenLimit; String? get error; String? get loginMethod;
/// Create a copy of AuthState
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$AuthStateCopyWith<AuthState> get copyWith => _$AuthStateCopyWithImpl<AuthState>(this as AuthState, _$identity);


@override
void debugFillProperties(DiagnosticPropertiesBuilder properties) {
  properties
    ..add(DiagnosticsProperty('type', 'AuthState'))
    ..add(DiagnosticsProperty('isLoading', isLoading))..add(DiagnosticsProperty('isAuthenticated', isAuthenticated))..add(DiagnosticsProperty('userId', userId))..add(DiagnosticsProperty('email', email))..add(DiagnosticsProperty('name', name))..add(DiagnosticsProperty('emailVerified', emailVerified))..add(DiagnosticsProperty('tokensUsed', tokensUsed))..add(DiagnosticsProperty('tokenLimit', tokenLimit))..add(DiagnosticsProperty('error', error))..add(DiagnosticsProperty('loginMethod', loginMethod));
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is AuthState&&(identical(other.isLoading, isLoading) || other.isLoading == isLoading)&&(identical(other.isAuthenticated, isAuthenticated) || other.isAuthenticated == isAuthenticated)&&(identical(other.userId, userId) || other.userId == userId)&&(identical(other.email, email) || other.email == email)&&(identical(other.name, name) || other.name == name)&&(identical(other.emailVerified, emailVerified) || other.emailVerified == emailVerified)&&(identical(other.tokensUsed, tokensUsed) || other.tokensUsed == tokensUsed)&&(identical(other.tokenLimit, tokenLimit) || other.tokenLimit == tokenLimit)&&(identical(other.error, error) || other.error == error)&&(identical(other.loginMethod, loginMethod) || other.loginMethod == loginMethod));
}


@override
int get hashCode => Object.hash(runtimeType,isLoading,isAuthenticated,userId,email,name,emailVerified,tokensUsed,tokenLimit,error,loginMethod);

@override
String toString({ DiagnosticLevel minLevel = DiagnosticLevel.info }) {
  return 'AuthState(isLoading: $isLoading, isAuthenticated: $isAuthenticated, userId: $userId, email: $email, name: $name, emailVerified: $emailVerified, tokensUsed: $tokensUsed, tokenLimit: $tokenLimit, error: $error, loginMethod: $loginMethod)';
}


}

/// @nodoc
abstract mixin class $AuthStateCopyWith<$Res>  {
  factory $AuthStateCopyWith(AuthState value, $Res Function(AuthState) _then) = _$AuthStateCopyWithImpl;
@useResult
$Res call({
 bool isLoading, bool isAuthenticated, String? userId, String? email, String? name, bool emailVerified, int tokensUsed, int tokenLimit, String? error, String? loginMethod
});




}
/// @nodoc
class _$AuthStateCopyWithImpl<$Res>
    implements $AuthStateCopyWith<$Res> {
  _$AuthStateCopyWithImpl(this._self, this._then);

  final AuthState _self;
  final $Res Function(AuthState) _then;

/// Create a copy of AuthState
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? isLoading = null,Object? isAuthenticated = null,Object? userId = freezed,Object? email = freezed,Object? name = freezed,Object? emailVerified = null,Object? tokensUsed = null,Object? tokenLimit = null,Object? error = freezed,Object? loginMethod = freezed,}) {
  return _then(_self.copyWith(
isLoading: null == isLoading ? _self.isLoading : isLoading // ignore: cast_nullable_to_non_nullable
as bool,isAuthenticated: null == isAuthenticated ? _self.isAuthenticated : isAuthenticated // ignore: cast_nullable_to_non_nullable
as bool,userId: freezed == userId ? _self.userId : userId // ignore: cast_nullable_to_non_nullable
as String?,email: freezed == email ? _self.email : email // ignore: cast_nullable_to_non_nullable
as String?,name: freezed == name ? _self.name : name // ignore: cast_nullable_to_non_nullable
as String?,emailVerified: null == emailVerified ? _self.emailVerified : emailVerified // ignore: cast_nullable_to_non_nullable
as bool,tokensUsed: null == tokensUsed ? _self.tokensUsed : tokensUsed // ignore: cast_nullable_to_non_nullable
as int,tokenLimit: null == tokenLimit ? _self.tokenLimit : tokenLimit // ignore: cast_nullable_to_non_nullable
as int,error: freezed == error ? _self.error : error // ignore: cast_nullable_to_non_nullable
as String?,loginMethod: freezed == loginMethod ? _self.loginMethod : loginMethod // ignore: cast_nullable_to_non_nullable
as String?,
  ));
}

}


/// Adds pattern-matching-related methods to [AuthState].
extension AuthStatePatterns on AuthState {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>(TResult Function( _AuthState value)?  $default,{required TResult orElse(),}){
final _that = this;
switch (_that) {
case _AuthState() when $default != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>(TResult Function( _AuthState value)  $default,){
final _that = this;
switch (_that) {
case _AuthState():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>(TResult? Function( _AuthState value)?  $default,){
final _that = this;
switch (_that) {
case _AuthState() when $default != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>(TResult Function( bool isLoading,  bool isAuthenticated,  String? userId,  String? email,  String? name,  bool emailVerified,  int tokensUsed,  int tokenLimit,  String? error,  String? loginMethod)?  $default,{required TResult orElse(),}) {final _that = this;
switch (_that) {
case _AuthState() when $default != null:
return $default(_that.isLoading,_that.isAuthenticated,_that.userId,_that.email,_that.name,_that.emailVerified,_that.tokensUsed,_that.tokenLimit,_that.error,_that.loginMethod);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>(TResult Function( bool isLoading,  bool isAuthenticated,  String? userId,  String? email,  String? name,  bool emailVerified,  int tokensUsed,  int tokenLimit,  String? error,  String? loginMethod)  $default,) {final _that = this;
switch (_that) {
case _AuthState():
return $default(_that.isLoading,_that.isAuthenticated,_that.userId,_that.email,_that.name,_that.emailVerified,_that.tokensUsed,_that.tokenLimit,_that.error,_that.loginMethod);}
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>(TResult? Function( bool isLoading,  bool isAuthenticated,  String? userId,  String? email,  String? name,  bool emailVerified,  int tokensUsed,  int tokenLimit,  String? error,  String? loginMethod)?  $default,) {final _that = this;
switch (_that) {
case _AuthState() when $default != null:
return $default(_that.isLoading,_that.isAuthenticated,_that.userId,_that.email,_that.name,_that.emailVerified,_that.tokensUsed,_that.tokenLimit,_that.error,_that.loginMethod);case _:
  return null;

}
}

}

/// @nodoc


class _AuthState with DiagnosticableTreeMixin implements AuthState {
  const _AuthState({this.isLoading = true, this.isAuthenticated = false, this.userId, this.email, this.name, this.emailVerified = false, this.tokensUsed = 0, this.tokenLimit = 0, this.error, this.loginMethod});
  

@override@JsonKey() final  bool isLoading;
@override@JsonKey() final  bool isAuthenticated;
@override final  String? userId;
@override final  String? email;
@override final  String? name;
@override@JsonKey() final  bool emailVerified;
@override@JsonKey() final  int tokensUsed;
@override@JsonKey() final  int tokenLimit;
@override final  String? error;
@override final  String? loginMethod;

/// Create a copy of AuthState
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$AuthStateCopyWith<_AuthState> get copyWith => __$AuthStateCopyWithImpl<_AuthState>(this, _$identity);


@override
void debugFillProperties(DiagnosticPropertiesBuilder properties) {
  properties
    ..add(DiagnosticsProperty('type', 'AuthState'))
    ..add(DiagnosticsProperty('isLoading', isLoading))..add(DiagnosticsProperty('isAuthenticated', isAuthenticated))..add(DiagnosticsProperty('userId', userId))..add(DiagnosticsProperty('email', email))..add(DiagnosticsProperty('name', name))..add(DiagnosticsProperty('emailVerified', emailVerified))..add(DiagnosticsProperty('tokensUsed', tokensUsed))..add(DiagnosticsProperty('tokenLimit', tokenLimit))..add(DiagnosticsProperty('error', error))..add(DiagnosticsProperty('loginMethod', loginMethod));
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _AuthState&&(identical(other.isLoading, isLoading) || other.isLoading == isLoading)&&(identical(other.isAuthenticated, isAuthenticated) || other.isAuthenticated == isAuthenticated)&&(identical(other.userId, userId) || other.userId == userId)&&(identical(other.email, email) || other.email == email)&&(identical(other.name, name) || other.name == name)&&(identical(other.emailVerified, emailVerified) || other.emailVerified == emailVerified)&&(identical(other.tokensUsed, tokensUsed) || other.tokensUsed == tokensUsed)&&(identical(other.tokenLimit, tokenLimit) || other.tokenLimit == tokenLimit)&&(identical(other.error, error) || other.error == error)&&(identical(other.loginMethod, loginMethod) || other.loginMethod == loginMethod));
}


@override
int get hashCode => Object.hash(runtimeType,isLoading,isAuthenticated,userId,email,name,emailVerified,tokensUsed,tokenLimit,error,loginMethod);

@override
String toString({ DiagnosticLevel minLevel = DiagnosticLevel.info }) {
  return 'AuthState(isLoading: $isLoading, isAuthenticated: $isAuthenticated, userId: $userId, email: $email, name: $name, emailVerified: $emailVerified, tokensUsed: $tokensUsed, tokenLimit: $tokenLimit, error: $error, loginMethod: $loginMethod)';
}


}

/// @nodoc
abstract mixin class _$AuthStateCopyWith<$Res> implements $AuthStateCopyWith<$Res> {
  factory _$AuthStateCopyWith(_AuthState value, $Res Function(_AuthState) _then) = __$AuthStateCopyWithImpl;
@override @useResult
$Res call({
 bool isLoading, bool isAuthenticated, String? userId, String? email, String? name, bool emailVerified, int tokensUsed, int tokenLimit, String? error, String? loginMethod
});




}
/// @nodoc
class __$AuthStateCopyWithImpl<$Res>
    implements _$AuthStateCopyWith<$Res> {
  __$AuthStateCopyWithImpl(this._self, this._then);

  final _AuthState _self;
  final $Res Function(_AuthState) _then;

/// Create a copy of AuthState
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? isLoading = null,Object? isAuthenticated = null,Object? userId = freezed,Object? email = freezed,Object? name = freezed,Object? emailVerified = null,Object? tokensUsed = null,Object? tokenLimit = null,Object? error = freezed,Object? loginMethod = freezed,}) {
  return _then(_AuthState(
isLoading: null == isLoading ? _self.isLoading : isLoading // ignore: cast_nullable_to_non_nullable
as bool,isAuthenticated: null == isAuthenticated ? _self.isAuthenticated : isAuthenticated // ignore: cast_nullable_to_non_nullable
as bool,userId: freezed == userId ? _self.userId : userId // ignore: cast_nullable_to_non_nullable
as String?,email: freezed == email ? _self.email : email // ignore: cast_nullable_to_non_nullable
as String?,name: freezed == name ? _self.name : name // ignore: cast_nullable_to_non_nullable
as String?,emailVerified: null == emailVerified ? _self.emailVerified : emailVerified // ignore: cast_nullable_to_non_nullable
as bool,tokensUsed: null == tokensUsed ? _self.tokensUsed : tokensUsed // ignore: cast_nullable_to_non_nullable
as int,tokenLimit: null == tokenLimit ? _self.tokenLimit : tokenLimit // ignore: cast_nullable_to_non_nullable
as int,error: freezed == error ? _self.error : error // ignore: cast_nullable_to_non_nullable
as String?,loginMethod: freezed == loginMethod ? _self.loginMethod : loginMethod // ignore: cast_nullable_to_non_nullable
as String?,
  ));
}


}

// dart format on
