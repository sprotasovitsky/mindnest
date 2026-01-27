// GENERATED CODE - DO NOT MODIFY BY HAND
// coverage:ignore-file
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

part of 'api_keys_provider.dart';

// **************************************************************************
// FreezedGenerator
// **************************************************************************

// dart format off
T _$identity<T>(T value) => value;
/// @nodoc
mixin _$ApiKeysState {

 bool get isLoading; List<ApiKey> get keys; String? get error;/// The newly created key (full key, shown once)
 CreateApiKeyResponse? get newKey;
/// Create a copy of ApiKeysState
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$ApiKeysStateCopyWith<ApiKeysState> get copyWith => _$ApiKeysStateCopyWithImpl<ApiKeysState>(this as ApiKeysState, _$identity);



@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is ApiKeysState&&(identical(other.isLoading, isLoading) || other.isLoading == isLoading)&&const DeepCollectionEquality().equals(other.keys, keys)&&(identical(other.error, error) || other.error == error)&&(identical(other.newKey, newKey) || other.newKey == newKey));
}


@override
int get hashCode => Object.hash(runtimeType,isLoading,const DeepCollectionEquality().hash(keys),error,newKey);

@override
String toString() {
  return 'ApiKeysState(isLoading: $isLoading, keys: $keys, error: $error, newKey: $newKey)';
}


}

/// @nodoc
abstract mixin class $ApiKeysStateCopyWith<$Res>  {
  factory $ApiKeysStateCopyWith(ApiKeysState value, $Res Function(ApiKeysState) _then) = _$ApiKeysStateCopyWithImpl;
@useResult
$Res call({
 bool isLoading, List<ApiKey> keys, String? error, CreateApiKeyResponse? newKey
});


$CreateApiKeyResponseCopyWith<$Res>? get newKey;

}
/// @nodoc
class _$ApiKeysStateCopyWithImpl<$Res>
    implements $ApiKeysStateCopyWith<$Res> {
  _$ApiKeysStateCopyWithImpl(this._self, this._then);

  final ApiKeysState _self;
  final $Res Function(ApiKeysState) _then;

/// Create a copy of ApiKeysState
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? isLoading = null,Object? keys = null,Object? error = freezed,Object? newKey = freezed,}) {
  return _then(_self.copyWith(
isLoading: null == isLoading ? _self.isLoading : isLoading // ignore: cast_nullable_to_non_nullable
as bool,keys: null == keys ? _self.keys : keys // ignore: cast_nullable_to_non_nullable
as List<ApiKey>,error: freezed == error ? _self.error : error // ignore: cast_nullable_to_non_nullable
as String?,newKey: freezed == newKey ? _self.newKey : newKey // ignore: cast_nullable_to_non_nullable
as CreateApiKeyResponse?,
  ));
}
/// Create a copy of ApiKeysState
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$CreateApiKeyResponseCopyWith<$Res>? get newKey {
    if (_self.newKey == null) {
    return null;
  }

  return $CreateApiKeyResponseCopyWith<$Res>(_self.newKey!, (value) {
    return _then(_self.copyWith(newKey: value));
  });
}
}


/// Adds pattern-matching-related methods to [ApiKeysState].
extension ApiKeysStatePatterns on ApiKeysState {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>(TResult Function( _ApiKeysState value)?  $default,{required TResult orElse(),}){
final _that = this;
switch (_that) {
case _ApiKeysState() when $default != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>(TResult Function( _ApiKeysState value)  $default,){
final _that = this;
switch (_that) {
case _ApiKeysState():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>(TResult? Function( _ApiKeysState value)?  $default,){
final _that = this;
switch (_that) {
case _ApiKeysState() when $default != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>(TResult Function( bool isLoading,  List<ApiKey> keys,  String? error,  CreateApiKeyResponse? newKey)?  $default,{required TResult orElse(),}) {final _that = this;
switch (_that) {
case _ApiKeysState() when $default != null:
return $default(_that.isLoading,_that.keys,_that.error,_that.newKey);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>(TResult Function( bool isLoading,  List<ApiKey> keys,  String? error,  CreateApiKeyResponse? newKey)  $default,) {final _that = this;
switch (_that) {
case _ApiKeysState():
return $default(_that.isLoading,_that.keys,_that.error,_that.newKey);}
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>(TResult? Function( bool isLoading,  List<ApiKey> keys,  String? error,  CreateApiKeyResponse? newKey)?  $default,) {final _that = this;
switch (_that) {
case _ApiKeysState() when $default != null:
return $default(_that.isLoading,_that.keys,_that.error,_that.newKey);case _:
  return null;

}
}

}

/// @nodoc


class _ApiKeysState implements ApiKeysState {
  const _ApiKeysState({this.isLoading = false, final  List<ApiKey> keys = const [], this.error, this.newKey}): _keys = keys;
  

@override@JsonKey() final  bool isLoading;
 final  List<ApiKey> _keys;
@override@JsonKey() List<ApiKey> get keys {
  if (_keys is EqualUnmodifiableListView) return _keys;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_keys);
}

@override final  String? error;
/// The newly created key (full key, shown once)
@override final  CreateApiKeyResponse? newKey;

/// Create a copy of ApiKeysState
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$ApiKeysStateCopyWith<_ApiKeysState> get copyWith => __$ApiKeysStateCopyWithImpl<_ApiKeysState>(this, _$identity);



@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _ApiKeysState&&(identical(other.isLoading, isLoading) || other.isLoading == isLoading)&&const DeepCollectionEquality().equals(other._keys, _keys)&&(identical(other.error, error) || other.error == error)&&(identical(other.newKey, newKey) || other.newKey == newKey));
}


@override
int get hashCode => Object.hash(runtimeType,isLoading,const DeepCollectionEquality().hash(_keys),error,newKey);

@override
String toString() {
  return 'ApiKeysState(isLoading: $isLoading, keys: $keys, error: $error, newKey: $newKey)';
}


}

/// @nodoc
abstract mixin class _$ApiKeysStateCopyWith<$Res> implements $ApiKeysStateCopyWith<$Res> {
  factory _$ApiKeysStateCopyWith(_ApiKeysState value, $Res Function(_ApiKeysState) _then) = __$ApiKeysStateCopyWithImpl;
@override @useResult
$Res call({
 bool isLoading, List<ApiKey> keys, String? error, CreateApiKeyResponse? newKey
});


@override $CreateApiKeyResponseCopyWith<$Res>? get newKey;

}
/// @nodoc
class __$ApiKeysStateCopyWithImpl<$Res>
    implements _$ApiKeysStateCopyWith<$Res> {
  __$ApiKeysStateCopyWithImpl(this._self, this._then);

  final _ApiKeysState _self;
  final $Res Function(_ApiKeysState) _then;

/// Create a copy of ApiKeysState
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? isLoading = null,Object? keys = null,Object? error = freezed,Object? newKey = freezed,}) {
  return _then(_ApiKeysState(
isLoading: null == isLoading ? _self.isLoading : isLoading // ignore: cast_nullable_to_non_nullable
as bool,keys: null == keys ? _self._keys : keys // ignore: cast_nullable_to_non_nullable
as List<ApiKey>,error: freezed == error ? _self.error : error // ignore: cast_nullable_to_non_nullable
as String?,newKey: freezed == newKey ? _self.newKey : newKey // ignore: cast_nullable_to_non_nullable
as CreateApiKeyResponse?,
  ));
}

/// Create a copy of ApiKeysState
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$CreateApiKeyResponseCopyWith<$Res>? get newKey {
    if (_self.newKey == null) {
    return null;
  }

  return $CreateApiKeyResponseCopyWith<$Res>(_self.newKey!, (value) {
    return _then(_self.copyWith(newKey: value));
  });
}
}

// dart format on
