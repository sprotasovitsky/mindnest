// GENERATED CODE - DO NOT MODIFY BY HAND
// coverage:ignore-file
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

part of 'api_key.dart';

// **************************************************************************
// FreezedGenerator
// **************************************************************************

// dart format off
T _$identity<T>(T value) => value;

/// @nodoc
mixin _$ApiKey {

 String get id; String get name; String get keyPrefix; String get scopes; DateTime get createdAt; DateTime? get lastUsedAt;
/// Create a copy of ApiKey
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$ApiKeyCopyWith<ApiKey> get copyWith => _$ApiKeyCopyWithImpl<ApiKey>(this as ApiKey, _$identity);

  /// Serializes this ApiKey to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is ApiKey&&(identical(other.id, id) || other.id == id)&&(identical(other.name, name) || other.name == name)&&(identical(other.keyPrefix, keyPrefix) || other.keyPrefix == keyPrefix)&&(identical(other.scopes, scopes) || other.scopes == scopes)&&(identical(other.createdAt, createdAt) || other.createdAt == createdAt)&&(identical(other.lastUsedAt, lastUsedAt) || other.lastUsedAt == lastUsedAt));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,id,name,keyPrefix,scopes,createdAt,lastUsedAt);

@override
String toString() {
  return 'ApiKey(id: $id, name: $name, keyPrefix: $keyPrefix, scopes: $scopes, createdAt: $createdAt, lastUsedAt: $lastUsedAt)';
}


}

/// @nodoc
abstract mixin class $ApiKeyCopyWith<$Res>  {
  factory $ApiKeyCopyWith(ApiKey value, $Res Function(ApiKey) _then) = _$ApiKeyCopyWithImpl;
@useResult
$Res call({
 String id, String name, String keyPrefix, String scopes, DateTime createdAt, DateTime? lastUsedAt
});




}
/// @nodoc
class _$ApiKeyCopyWithImpl<$Res>
    implements $ApiKeyCopyWith<$Res> {
  _$ApiKeyCopyWithImpl(this._self, this._then);

  final ApiKey _self;
  final $Res Function(ApiKey) _then;

/// Create a copy of ApiKey
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? id = null,Object? name = null,Object? keyPrefix = null,Object? scopes = null,Object? createdAt = null,Object? lastUsedAt = freezed,}) {
  return _then(_self.copyWith(
id: null == id ? _self.id : id // ignore: cast_nullable_to_non_nullable
as String,name: null == name ? _self.name : name // ignore: cast_nullable_to_non_nullable
as String,keyPrefix: null == keyPrefix ? _self.keyPrefix : keyPrefix // ignore: cast_nullable_to_non_nullable
as String,scopes: null == scopes ? _self.scopes : scopes // ignore: cast_nullable_to_non_nullable
as String,createdAt: null == createdAt ? _self.createdAt : createdAt // ignore: cast_nullable_to_non_nullable
as DateTime,lastUsedAt: freezed == lastUsedAt ? _self.lastUsedAt : lastUsedAt // ignore: cast_nullable_to_non_nullable
as DateTime?,
  ));
}

}


/// Adds pattern-matching-related methods to [ApiKey].
extension ApiKeyPatterns on ApiKey {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>(TResult Function( _ApiKey value)?  $default,{required TResult orElse(),}){
final _that = this;
switch (_that) {
case _ApiKey() when $default != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>(TResult Function( _ApiKey value)  $default,){
final _that = this;
switch (_that) {
case _ApiKey():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>(TResult? Function( _ApiKey value)?  $default,){
final _that = this;
switch (_that) {
case _ApiKey() when $default != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>(TResult Function( String id,  String name,  String keyPrefix,  String scopes,  DateTime createdAt,  DateTime? lastUsedAt)?  $default,{required TResult orElse(),}) {final _that = this;
switch (_that) {
case _ApiKey() when $default != null:
return $default(_that.id,_that.name,_that.keyPrefix,_that.scopes,_that.createdAt,_that.lastUsedAt);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>(TResult Function( String id,  String name,  String keyPrefix,  String scopes,  DateTime createdAt,  DateTime? lastUsedAt)  $default,) {final _that = this;
switch (_that) {
case _ApiKey():
return $default(_that.id,_that.name,_that.keyPrefix,_that.scopes,_that.createdAt,_that.lastUsedAt);}
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>(TResult? Function( String id,  String name,  String keyPrefix,  String scopes,  DateTime createdAt,  DateTime? lastUsedAt)?  $default,) {final _that = this;
switch (_that) {
case _ApiKey() when $default != null:
return $default(_that.id,_that.name,_that.keyPrefix,_that.scopes,_that.createdAt,_that.lastUsedAt);case _:
  return null;

}
}

}

/// @nodoc
@JsonSerializable()

class _ApiKey extends ApiKey {
  const _ApiKey({required this.id, required this.name, required this.keyPrefix, required this.scopes, required this.createdAt, this.lastUsedAt}): super._();
  factory _ApiKey.fromJson(Map<String, dynamic> json) => _$ApiKeyFromJson(json);

@override final  String id;
@override final  String name;
@override final  String keyPrefix;
@override final  String scopes;
@override final  DateTime createdAt;
@override final  DateTime? lastUsedAt;

/// Create a copy of ApiKey
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$ApiKeyCopyWith<_ApiKey> get copyWith => __$ApiKeyCopyWithImpl<_ApiKey>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$ApiKeyToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _ApiKey&&(identical(other.id, id) || other.id == id)&&(identical(other.name, name) || other.name == name)&&(identical(other.keyPrefix, keyPrefix) || other.keyPrefix == keyPrefix)&&(identical(other.scopes, scopes) || other.scopes == scopes)&&(identical(other.createdAt, createdAt) || other.createdAt == createdAt)&&(identical(other.lastUsedAt, lastUsedAt) || other.lastUsedAt == lastUsedAt));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,id,name,keyPrefix,scopes,createdAt,lastUsedAt);

@override
String toString() {
  return 'ApiKey(id: $id, name: $name, keyPrefix: $keyPrefix, scopes: $scopes, createdAt: $createdAt, lastUsedAt: $lastUsedAt)';
}


}

/// @nodoc
abstract mixin class _$ApiKeyCopyWith<$Res> implements $ApiKeyCopyWith<$Res> {
  factory _$ApiKeyCopyWith(_ApiKey value, $Res Function(_ApiKey) _then) = __$ApiKeyCopyWithImpl;
@override @useResult
$Res call({
 String id, String name, String keyPrefix, String scopes, DateTime createdAt, DateTime? lastUsedAt
});




}
/// @nodoc
class __$ApiKeyCopyWithImpl<$Res>
    implements _$ApiKeyCopyWith<$Res> {
  __$ApiKeyCopyWithImpl(this._self, this._then);

  final _ApiKey _self;
  final $Res Function(_ApiKey) _then;

/// Create a copy of ApiKey
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? id = null,Object? name = null,Object? keyPrefix = null,Object? scopes = null,Object? createdAt = null,Object? lastUsedAt = freezed,}) {
  return _then(_ApiKey(
id: null == id ? _self.id : id // ignore: cast_nullable_to_non_nullable
as String,name: null == name ? _self.name : name // ignore: cast_nullable_to_non_nullable
as String,keyPrefix: null == keyPrefix ? _self.keyPrefix : keyPrefix // ignore: cast_nullable_to_non_nullable
as String,scopes: null == scopes ? _self.scopes : scopes // ignore: cast_nullable_to_non_nullable
as String,createdAt: null == createdAt ? _self.createdAt : createdAt // ignore: cast_nullable_to_non_nullable
as DateTime,lastUsedAt: freezed == lastUsedAt ? _self.lastUsedAt : lastUsedAt // ignore: cast_nullable_to_non_nullable
as DateTime?,
  ));
}


}


/// @nodoc
mixin _$CreateApiKeyResponse {

 String get id; String get name; String get key;// Full key - shown only once
 String get keyPrefix; String get scopes; DateTime get createdAt;
/// Create a copy of CreateApiKeyResponse
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$CreateApiKeyResponseCopyWith<CreateApiKeyResponse> get copyWith => _$CreateApiKeyResponseCopyWithImpl<CreateApiKeyResponse>(this as CreateApiKeyResponse, _$identity);

  /// Serializes this CreateApiKeyResponse to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is CreateApiKeyResponse&&(identical(other.id, id) || other.id == id)&&(identical(other.name, name) || other.name == name)&&(identical(other.key, key) || other.key == key)&&(identical(other.keyPrefix, keyPrefix) || other.keyPrefix == keyPrefix)&&(identical(other.scopes, scopes) || other.scopes == scopes)&&(identical(other.createdAt, createdAt) || other.createdAt == createdAt));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,id,name,key,keyPrefix,scopes,createdAt);

@override
String toString() {
  return 'CreateApiKeyResponse(id: $id, name: $name, key: $key, keyPrefix: $keyPrefix, scopes: $scopes, createdAt: $createdAt)';
}


}

/// @nodoc
abstract mixin class $CreateApiKeyResponseCopyWith<$Res>  {
  factory $CreateApiKeyResponseCopyWith(CreateApiKeyResponse value, $Res Function(CreateApiKeyResponse) _then) = _$CreateApiKeyResponseCopyWithImpl;
@useResult
$Res call({
 String id, String name, String key, String keyPrefix, String scopes, DateTime createdAt
});




}
/// @nodoc
class _$CreateApiKeyResponseCopyWithImpl<$Res>
    implements $CreateApiKeyResponseCopyWith<$Res> {
  _$CreateApiKeyResponseCopyWithImpl(this._self, this._then);

  final CreateApiKeyResponse _self;
  final $Res Function(CreateApiKeyResponse) _then;

/// Create a copy of CreateApiKeyResponse
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? id = null,Object? name = null,Object? key = null,Object? keyPrefix = null,Object? scopes = null,Object? createdAt = null,}) {
  return _then(_self.copyWith(
id: null == id ? _self.id : id // ignore: cast_nullable_to_non_nullable
as String,name: null == name ? _self.name : name // ignore: cast_nullable_to_non_nullable
as String,key: null == key ? _self.key : key // ignore: cast_nullable_to_non_nullable
as String,keyPrefix: null == keyPrefix ? _self.keyPrefix : keyPrefix // ignore: cast_nullable_to_non_nullable
as String,scopes: null == scopes ? _self.scopes : scopes // ignore: cast_nullable_to_non_nullable
as String,createdAt: null == createdAt ? _self.createdAt : createdAt // ignore: cast_nullable_to_non_nullable
as DateTime,
  ));
}

}


/// Adds pattern-matching-related methods to [CreateApiKeyResponse].
extension CreateApiKeyResponsePatterns on CreateApiKeyResponse {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>(TResult Function( _CreateApiKeyResponse value)?  $default,{required TResult orElse(),}){
final _that = this;
switch (_that) {
case _CreateApiKeyResponse() when $default != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>(TResult Function( _CreateApiKeyResponse value)  $default,){
final _that = this;
switch (_that) {
case _CreateApiKeyResponse():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>(TResult? Function( _CreateApiKeyResponse value)?  $default,){
final _that = this;
switch (_that) {
case _CreateApiKeyResponse() when $default != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>(TResult Function( String id,  String name,  String key,  String keyPrefix,  String scopes,  DateTime createdAt)?  $default,{required TResult orElse(),}) {final _that = this;
switch (_that) {
case _CreateApiKeyResponse() when $default != null:
return $default(_that.id,_that.name,_that.key,_that.keyPrefix,_that.scopes,_that.createdAt);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>(TResult Function( String id,  String name,  String key,  String keyPrefix,  String scopes,  DateTime createdAt)  $default,) {final _that = this;
switch (_that) {
case _CreateApiKeyResponse():
return $default(_that.id,_that.name,_that.key,_that.keyPrefix,_that.scopes,_that.createdAt);}
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>(TResult? Function( String id,  String name,  String key,  String keyPrefix,  String scopes,  DateTime createdAt)?  $default,) {final _that = this;
switch (_that) {
case _CreateApiKeyResponse() when $default != null:
return $default(_that.id,_that.name,_that.key,_that.keyPrefix,_that.scopes,_that.createdAt);case _:
  return null;

}
}

}

/// @nodoc
@JsonSerializable()

class _CreateApiKeyResponse extends CreateApiKeyResponse {
  const _CreateApiKeyResponse({required this.id, required this.name, required this.key, required this.keyPrefix, required this.scopes, required this.createdAt}): super._();
  factory _CreateApiKeyResponse.fromJson(Map<String, dynamic> json) => _$CreateApiKeyResponseFromJson(json);

@override final  String id;
@override final  String name;
@override final  String key;
// Full key - shown only once
@override final  String keyPrefix;
@override final  String scopes;
@override final  DateTime createdAt;

/// Create a copy of CreateApiKeyResponse
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$CreateApiKeyResponseCopyWith<_CreateApiKeyResponse> get copyWith => __$CreateApiKeyResponseCopyWithImpl<_CreateApiKeyResponse>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$CreateApiKeyResponseToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _CreateApiKeyResponse&&(identical(other.id, id) || other.id == id)&&(identical(other.name, name) || other.name == name)&&(identical(other.key, key) || other.key == key)&&(identical(other.keyPrefix, keyPrefix) || other.keyPrefix == keyPrefix)&&(identical(other.scopes, scopes) || other.scopes == scopes)&&(identical(other.createdAt, createdAt) || other.createdAt == createdAt));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,id,name,key,keyPrefix,scopes,createdAt);

@override
String toString() {
  return 'CreateApiKeyResponse(id: $id, name: $name, key: $key, keyPrefix: $keyPrefix, scopes: $scopes, createdAt: $createdAt)';
}


}

/// @nodoc
abstract mixin class _$CreateApiKeyResponseCopyWith<$Res> implements $CreateApiKeyResponseCopyWith<$Res> {
  factory _$CreateApiKeyResponseCopyWith(_CreateApiKeyResponse value, $Res Function(_CreateApiKeyResponse) _then) = __$CreateApiKeyResponseCopyWithImpl;
@override @useResult
$Res call({
 String id, String name, String key, String keyPrefix, String scopes, DateTime createdAt
});




}
/// @nodoc
class __$CreateApiKeyResponseCopyWithImpl<$Res>
    implements _$CreateApiKeyResponseCopyWith<$Res> {
  __$CreateApiKeyResponseCopyWithImpl(this._self, this._then);

  final _CreateApiKeyResponse _self;
  final $Res Function(_CreateApiKeyResponse) _then;

/// Create a copy of CreateApiKeyResponse
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? id = null,Object? name = null,Object? key = null,Object? keyPrefix = null,Object? scopes = null,Object? createdAt = null,}) {
  return _then(_CreateApiKeyResponse(
id: null == id ? _self.id : id // ignore: cast_nullable_to_non_nullable
as String,name: null == name ? _self.name : name // ignore: cast_nullable_to_non_nullable
as String,key: null == key ? _self.key : key // ignore: cast_nullable_to_non_nullable
as String,keyPrefix: null == keyPrefix ? _self.keyPrefix : keyPrefix // ignore: cast_nullable_to_non_nullable
as String,scopes: null == scopes ? _self.scopes : scopes // ignore: cast_nullable_to_non_nullable
as String,createdAt: null == createdAt ? _self.createdAt : createdAt // ignore: cast_nullable_to_non_nullable
as DateTime,
  ));
}


}

// dart format on
