// GENERATED CODE - DO NOT MODIFY BY HAND
// coverage:ignore-file
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

part of 'whisper_provider.dart';

// **************************************************************************
// FreezedGenerator
// **************************************************************************

// dart format off
T _$identity<T>(T value) => value;
/// @nodoc
mixin _$WhisperState {

 WhisperModelStatus get modelStatus; double get downloadProgress; TranscriptionStatus get transcriptionStatus; String? get errorMessage; int? get modelSizeBytes;
/// Create a copy of WhisperState
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$WhisperStateCopyWith<WhisperState> get copyWith => _$WhisperStateCopyWithImpl<WhisperState>(this as WhisperState, _$identity);



@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is WhisperState&&(identical(other.modelStatus, modelStatus) || other.modelStatus == modelStatus)&&(identical(other.downloadProgress, downloadProgress) || other.downloadProgress == downloadProgress)&&(identical(other.transcriptionStatus, transcriptionStatus) || other.transcriptionStatus == transcriptionStatus)&&(identical(other.errorMessage, errorMessage) || other.errorMessage == errorMessage)&&(identical(other.modelSizeBytes, modelSizeBytes) || other.modelSizeBytes == modelSizeBytes));
}


@override
int get hashCode => Object.hash(runtimeType,modelStatus,downloadProgress,transcriptionStatus,errorMessage,modelSizeBytes);

@override
String toString() {
  return 'WhisperState(modelStatus: $modelStatus, downloadProgress: $downloadProgress, transcriptionStatus: $transcriptionStatus, errorMessage: $errorMessage, modelSizeBytes: $modelSizeBytes)';
}


}

/// @nodoc
abstract mixin class $WhisperStateCopyWith<$Res>  {
  factory $WhisperStateCopyWith(WhisperState value, $Res Function(WhisperState) _then) = _$WhisperStateCopyWithImpl;
@useResult
$Res call({
 WhisperModelStatus modelStatus, double downloadProgress, TranscriptionStatus transcriptionStatus, String? errorMessage, int? modelSizeBytes
});




}
/// @nodoc
class _$WhisperStateCopyWithImpl<$Res>
    implements $WhisperStateCopyWith<$Res> {
  _$WhisperStateCopyWithImpl(this._self, this._then);

  final WhisperState _self;
  final $Res Function(WhisperState) _then;

/// Create a copy of WhisperState
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? modelStatus = null,Object? downloadProgress = null,Object? transcriptionStatus = null,Object? errorMessage = freezed,Object? modelSizeBytes = freezed,}) {
  return _then(_self.copyWith(
modelStatus: null == modelStatus ? _self.modelStatus : modelStatus // ignore: cast_nullable_to_non_nullable
as WhisperModelStatus,downloadProgress: null == downloadProgress ? _self.downloadProgress : downloadProgress // ignore: cast_nullable_to_non_nullable
as double,transcriptionStatus: null == transcriptionStatus ? _self.transcriptionStatus : transcriptionStatus // ignore: cast_nullable_to_non_nullable
as TranscriptionStatus,errorMessage: freezed == errorMessage ? _self.errorMessage : errorMessage // ignore: cast_nullable_to_non_nullable
as String?,modelSizeBytes: freezed == modelSizeBytes ? _self.modelSizeBytes : modelSizeBytes // ignore: cast_nullable_to_non_nullable
as int?,
  ));
}

}


/// Adds pattern-matching-related methods to [WhisperState].
extension WhisperStatePatterns on WhisperState {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>(TResult Function( _WhisperState value)?  $default,{required TResult orElse(),}){
final _that = this;
switch (_that) {
case _WhisperState() when $default != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>(TResult Function( _WhisperState value)  $default,){
final _that = this;
switch (_that) {
case _WhisperState():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>(TResult? Function( _WhisperState value)?  $default,){
final _that = this;
switch (_that) {
case _WhisperState() when $default != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>(TResult Function( WhisperModelStatus modelStatus,  double downloadProgress,  TranscriptionStatus transcriptionStatus,  String? errorMessage,  int? modelSizeBytes)?  $default,{required TResult orElse(),}) {final _that = this;
switch (_that) {
case _WhisperState() when $default != null:
return $default(_that.modelStatus,_that.downloadProgress,_that.transcriptionStatus,_that.errorMessage,_that.modelSizeBytes);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>(TResult Function( WhisperModelStatus modelStatus,  double downloadProgress,  TranscriptionStatus transcriptionStatus,  String? errorMessage,  int? modelSizeBytes)  $default,) {final _that = this;
switch (_that) {
case _WhisperState():
return $default(_that.modelStatus,_that.downloadProgress,_that.transcriptionStatus,_that.errorMessage,_that.modelSizeBytes);}
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>(TResult? Function( WhisperModelStatus modelStatus,  double downloadProgress,  TranscriptionStatus transcriptionStatus,  String? errorMessage,  int? modelSizeBytes)?  $default,) {final _that = this;
switch (_that) {
case _WhisperState() when $default != null:
return $default(_that.modelStatus,_that.downloadProgress,_that.transcriptionStatus,_that.errorMessage,_that.modelSizeBytes);case _:
  return null;

}
}

}

/// @nodoc


class _WhisperState implements WhisperState {
  const _WhisperState({this.modelStatus = WhisperModelStatus.unknown, this.downloadProgress = 0.0, this.transcriptionStatus = TranscriptionStatus.idle, this.errorMessage, this.modelSizeBytes});
  

@override@JsonKey() final  WhisperModelStatus modelStatus;
@override@JsonKey() final  double downloadProgress;
@override@JsonKey() final  TranscriptionStatus transcriptionStatus;
@override final  String? errorMessage;
@override final  int? modelSizeBytes;

/// Create a copy of WhisperState
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$WhisperStateCopyWith<_WhisperState> get copyWith => __$WhisperStateCopyWithImpl<_WhisperState>(this, _$identity);



@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _WhisperState&&(identical(other.modelStatus, modelStatus) || other.modelStatus == modelStatus)&&(identical(other.downloadProgress, downloadProgress) || other.downloadProgress == downloadProgress)&&(identical(other.transcriptionStatus, transcriptionStatus) || other.transcriptionStatus == transcriptionStatus)&&(identical(other.errorMessage, errorMessage) || other.errorMessage == errorMessage)&&(identical(other.modelSizeBytes, modelSizeBytes) || other.modelSizeBytes == modelSizeBytes));
}


@override
int get hashCode => Object.hash(runtimeType,modelStatus,downloadProgress,transcriptionStatus,errorMessage,modelSizeBytes);

@override
String toString() {
  return 'WhisperState(modelStatus: $modelStatus, downloadProgress: $downloadProgress, transcriptionStatus: $transcriptionStatus, errorMessage: $errorMessage, modelSizeBytes: $modelSizeBytes)';
}


}

/// @nodoc
abstract mixin class _$WhisperStateCopyWith<$Res> implements $WhisperStateCopyWith<$Res> {
  factory _$WhisperStateCopyWith(_WhisperState value, $Res Function(_WhisperState) _then) = __$WhisperStateCopyWithImpl;
@override @useResult
$Res call({
 WhisperModelStatus modelStatus, double downloadProgress, TranscriptionStatus transcriptionStatus, String? errorMessage, int? modelSizeBytes
});




}
/// @nodoc
class __$WhisperStateCopyWithImpl<$Res>
    implements _$WhisperStateCopyWith<$Res> {
  __$WhisperStateCopyWithImpl(this._self, this._then);

  final _WhisperState _self;
  final $Res Function(_WhisperState) _then;

/// Create a copy of WhisperState
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? modelStatus = null,Object? downloadProgress = null,Object? transcriptionStatus = null,Object? errorMessage = freezed,Object? modelSizeBytes = freezed,}) {
  return _then(_WhisperState(
modelStatus: null == modelStatus ? _self.modelStatus : modelStatus // ignore: cast_nullable_to_non_nullable
as WhisperModelStatus,downloadProgress: null == downloadProgress ? _self.downloadProgress : downloadProgress // ignore: cast_nullable_to_non_nullable
as double,transcriptionStatus: null == transcriptionStatus ? _self.transcriptionStatus : transcriptionStatus // ignore: cast_nullable_to_non_nullable
as TranscriptionStatus,errorMessage: freezed == errorMessage ? _self.errorMessage : errorMessage // ignore: cast_nullable_to_non_nullable
as String?,modelSizeBytes: freezed == modelSizeBytes ? _self.modelSizeBytes : modelSizeBytes // ignore: cast_nullable_to_non_nullable
as int?,
  ));
}


}

// dart format on
