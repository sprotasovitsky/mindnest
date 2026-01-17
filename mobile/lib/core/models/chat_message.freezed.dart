// GENERATED CODE - DO NOT MODIFY BY HAND
// coverage:ignore-file
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

part of 'chat_message.dart';

// **************************************************************************
// FreezedGenerator
// **************************************************************************

// dart format off
T _$identity<T>(T value) => value;

/// @nodoc
mixin _$ChatMessage {

 String get content; bool get isUser; DateTime get timestamp; double? get confidence; bool get isError;
/// Create a copy of ChatMessage
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$ChatMessageCopyWith<ChatMessage> get copyWith => _$ChatMessageCopyWithImpl<ChatMessage>(this as ChatMessage, _$identity);

  /// Serializes this ChatMessage to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is ChatMessage&&(identical(other.content, content) || other.content == content)&&(identical(other.isUser, isUser) || other.isUser == isUser)&&(identical(other.timestamp, timestamp) || other.timestamp == timestamp)&&(identical(other.confidence, confidence) || other.confidence == confidence)&&(identical(other.isError, isError) || other.isError == isError));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,content,isUser,timestamp,confidence,isError);

@override
String toString() {
  return 'ChatMessage(content: $content, isUser: $isUser, timestamp: $timestamp, confidence: $confidence, isError: $isError)';
}


}

/// @nodoc
abstract mixin class $ChatMessageCopyWith<$Res>  {
  factory $ChatMessageCopyWith(ChatMessage value, $Res Function(ChatMessage) _then) = _$ChatMessageCopyWithImpl;
@useResult
$Res call({
 String content, bool isUser, DateTime timestamp, double? confidence, bool isError
});




}
/// @nodoc
class _$ChatMessageCopyWithImpl<$Res>
    implements $ChatMessageCopyWith<$Res> {
  _$ChatMessageCopyWithImpl(this._self, this._then);

  final ChatMessage _self;
  final $Res Function(ChatMessage) _then;

/// Create a copy of ChatMessage
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? content = null,Object? isUser = null,Object? timestamp = null,Object? confidence = freezed,Object? isError = null,}) {
  return _then(_self.copyWith(
content: null == content ? _self.content : content // ignore: cast_nullable_to_non_nullable
as String,isUser: null == isUser ? _self.isUser : isUser // ignore: cast_nullable_to_non_nullable
as bool,timestamp: null == timestamp ? _self.timestamp : timestamp // ignore: cast_nullable_to_non_nullable
as DateTime,confidence: freezed == confidence ? _self.confidence : confidence // ignore: cast_nullable_to_non_nullable
as double?,isError: null == isError ? _self.isError : isError // ignore: cast_nullable_to_non_nullable
as bool,
  ));
}

}


/// Adds pattern-matching-related methods to [ChatMessage].
extension ChatMessagePatterns on ChatMessage {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>(TResult Function( _ChatMessage value)?  $default,{required TResult orElse(),}){
final _that = this;
switch (_that) {
case _ChatMessage() when $default != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>(TResult Function( _ChatMessage value)  $default,){
final _that = this;
switch (_that) {
case _ChatMessage():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>(TResult? Function( _ChatMessage value)?  $default,){
final _that = this;
switch (_that) {
case _ChatMessage() when $default != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>(TResult Function( String content,  bool isUser,  DateTime timestamp,  double? confidence,  bool isError)?  $default,{required TResult orElse(),}) {final _that = this;
switch (_that) {
case _ChatMessage() when $default != null:
return $default(_that.content,_that.isUser,_that.timestamp,_that.confidence,_that.isError);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>(TResult Function( String content,  bool isUser,  DateTime timestamp,  double? confidence,  bool isError)  $default,) {final _that = this;
switch (_that) {
case _ChatMessage():
return $default(_that.content,_that.isUser,_that.timestamp,_that.confidence,_that.isError);}
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>(TResult? Function( String content,  bool isUser,  DateTime timestamp,  double? confidence,  bool isError)?  $default,) {final _that = this;
switch (_that) {
case _ChatMessage() when $default != null:
return $default(_that.content,_that.isUser,_that.timestamp,_that.confidence,_that.isError);case _:
  return null;

}
}

}

/// @nodoc
@JsonSerializable()

class _ChatMessage implements ChatMessage {
  const _ChatMessage({required this.content, required this.isUser, required this.timestamp, this.confidence, this.isError = false});
  factory _ChatMessage.fromJson(Map<String, dynamic> json) => _$ChatMessageFromJson(json);

@override final  String content;
@override final  bool isUser;
@override final  DateTime timestamp;
@override final  double? confidence;
@override@JsonKey() final  bool isError;

/// Create a copy of ChatMessage
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$ChatMessageCopyWith<_ChatMessage> get copyWith => __$ChatMessageCopyWithImpl<_ChatMessage>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$ChatMessageToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _ChatMessage&&(identical(other.content, content) || other.content == content)&&(identical(other.isUser, isUser) || other.isUser == isUser)&&(identical(other.timestamp, timestamp) || other.timestamp == timestamp)&&(identical(other.confidence, confidence) || other.confidence == confidence)&&(identical(other.isError, isError) || other.isError == isError));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,content,isUser,timestamp,confidence,isError);

@override
String toString() {
  return 'ChatMessage(content: $content, isUser: $isUser, timestamp: $timestamp, confidence: $confidence, isError: $isError)';
}


}

/// @nodoc
abstract mixin class _$ChatMessageCopyWith<$Res> implements $ChatMessageCopyWith<$Res> {
  factory _$ChatMessageCopyWith(_ChatMessage value, $Res Function(_ChatMessage) _then) = __$ChatMessageCopyWithImpl;
@override @useResult
$Res call({
 String content, bool isUser, DateTime timestamp, double? confidence, bool isError
});




}
/// @nodoc
class __$ChatMessageCopyWithImpl<$Res>
    implements _$ChatMessageCopyWith<$Res> {
  __$ChatMessageCopyWithImpl(this._self, this._then);

  final _ChatMessage _self;
  final $Res Function(_ChatMessage) _then;

/// Create a copy of ChatMessage
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? content = null,Object? isUser = null,Object? timestamp = null,Object? confidence = freezed,Object? isError = null,}) {
  return _then(_ChatMessage(
content: null == content ? _self.content : content // ignore: cast_nullable_to_non_nullable
as String,isUser: null == isUser ? _self.isUser : isUser // ignore: cast_nullable_to_non_nullable
as bool,timestamp: null == timestamp ? _self.timestamp : timestamp // ignore: cast_nullable_to_non_nullable
as DateTime,confidence: freezed == confidence ? _self.confidence : confidence // ignore: cast_nullable_to_non_nullable
as double?,isError: null == isError ? _self.isError : isError // ignore: cast_nullable_to_non_nullable
as bool,
  ));
}


}


/// @nodoc
mixin _$ChatResponse {

 String get reply; double? get confidence;@JsonKey(name: 'message_type') String? get messageType;
/// Create a copy of ChatResponse
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$ChatResponseCopyWith<ChatResponse> get copyWith => _$ChatResponseCopyWithImpl<ChatResponse>(this as ChatResponse, _$identity);

  /// Serializes this ChatResponse to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is ChatResponse&&(identical(other.reply, reply) || other.reply == reply)&&(identical(other.confidence, confidence) || other.confidence == confidence)&&(identical(other.messageType, messageType) || other.messageType == messageType));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,reply,confidence,messageType);

@override
String toString() {
  return 'ChatResponse(reply: $reply, confidence: $confidence, messageType: $messageType)';
}


}

/// @nodoc
abstract mixin class $ChatResponseCopyWith<$Res>  {
  factory $ChatResponseCopyWith(ChatResponse value, $Res Function(ChatResponse) _then) = _$ChatResponseCopyWithImpl;
@useResult
$Res call({
 String reply, double? confidence,@JsonKey(name: 'message_type') String? messageType
});




}
/// @nodoc
class _$ChatResponseCopyWithImpl<$Res>
    implements $ChatResponseCopyWith<$Res> {
  _$ChatResponseCopyWithImpl(this._self, this._then);

  final ChatResponse _self;
  final $Res Function(ChatResponse) _then;

/// Create a copy of ChatResponse
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? reply = null,Object? confidence = freezed,Object? messageType = freezed,}) {
  return _then(_self.copyWith(
reply: null == reply ? _self.reply : reply // ignore: cast_nullable_to_non_nullable
as String,confidence: freezed == confidence ? _self.confidence : confidence // ignore: cast_nullable_to_non_nullable
as double?,messageType: freezed == messageType ? _self.messageType : messageType // ignore: cast_nullable_to_non_nullable
as String?,
  ));
}

}


/// Adds pattern-matching-related methods to [ChatResponse].
extension ChatResponsePatterns on ChatResponse {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>(TResult Function( _ChatResponse value)?  $default,{required TResult orElse(),}){
final _that = this;
switch (_that) {
case _ChatResponse() when $default != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>(TResult Function( _ChatResponse value)  $default,){
final _that = this;
switch (_that) {
case _ChatResponse():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>(TResult? Function( _ChatResponse value)?  $default,){
final _that = this;
switch (_that) {
case _ChatResponse() when $default != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>(TResult Function( String reply,  double? confidence, @JsonKey(name: 'message_type')  String? messageType)?  $default,{required TResult orElse(),}) {final _that = this;
switch (_that) {
case _ChatResponse() when $default != null:
return $default(_that.reply,_that.confidence,_that.messageType);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>(TResult Function( String reply,  double? confidence, @JsonKey(name: 'message_type')  String? messageType)  $default,) {final _that = this;
switch (_that) {
case _ChatResponse():
return $default(_that.reply,_that.confidence,_that.messageType);}
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>(TResult? Function( String reply,  double? confidence, @JsonKey(name: 'message_type')  String? messageType)?  $default,) {final _that = this;
switch (_that) {
case _ChatResponse() when $default != null:
return $default(_that.reply,_that.confidence,_that.messageType);case _:
  return null;

}
}

}

/// @nodoc
@JsonSerializable()

class _ChatResponse implements ChatResponse {
  const _ChatResponse({required this.reply, this.confidence, @JsonKey(name: 'message_type') this.messageType});
  factory _ChatResponse.fromJson(Map<String, dynamic> json) => _$ChatResponseFromJson(json);

@override final  String reply;
@override final  double? confidence;
@override@JsonKey(name: 'message_type') final  String? messageType;

/// Create a copy of ChatResponse
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$ChatResponseCopyWith<_ChatResponse> get copyWith => __$ChatResponseCopyWithImpl<_ChatResponse>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$ChatResponseToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _ChatResponse&&(identical(other.reply, reply) || other.reply == reply)&&(identical(other.confidence, confidence) || other.confidence == confidence)&&(identical(other.messageType, messageType) || other.messageType == messageType));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,reply,confidence,messageType);

@override
String toString() {
  return 'ChatResponse(reply: $reply, confidence: $confidence, messageType: $messageType)';
}


}

/// @nodoc
abstract mixin class _$ChatResponseCopyWith<$Res> implements $ChatResponseCopyWith<$Res> {
  factory _$ChatResponseCopyWith(_ChatResponse value, $Res Function(_ChatResponse) _then) = __$ChatResponseCopyWithImpl;
@override @useResult
$Res call({
 String reply, double? confidence,@JsonKey(name: 'message_type') String? messageType
});




}
/// @nodoc
class __$ChatResponseCopyWithImpl<$Res>
    implements _$ChatResponseCopyWith<$Res> {
  __$ChatResponseCopyWithImpl(this._self, this._then);

  final _ChatResponse _self;
  final $Res Function(_ChatResponse) _then;

/// Create a copy of ChatResponse
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? reply = null,Object? confidence = freezed,Object? messageType = freezed,}) {
  return _then(_ChatResponse(
reply: null == reply ? _self.reply : reply // ignore: cast_nullable_to_non_nullable
as String,confidence: freezed == confidence ? _self.confidence : confidence // ignore: cast_nullable_to_non_nullable
as double?,messageType: freezed == messageType ? _self.messageType : messageType // ignore: cast_nullable_to_non_nullable
as String?,
  ));
}


}


/// @nodoc
mixin _$ChatHistoryResponse {

 List<ChatHistoryItem> get messages;
/// Create a copy of ChatHistoryResponse
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$ChatHistoryResponseCopyWith<ChatHistoryResponse> get copyWith => _$ChatHistoryResponseCopyWithImpl<ChatHistoryResponse>(this as ChatHistoryResponse, _$identity);

  /// Serializes this ChatHistoryResponse to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is ChatHistoryResponse&&const DeepCollectionEquality().equals(other.messages, messages));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,const DeepCollectionEquality().hash(messages));

@override
String toString() {
  return 'ChatHistoryResponse(messages: $messages)';
}


}

/// @nodoc
abstract mixin class $ChatHistoryResponseCopyWith<$Res>  {
  factory $ChatHistoryResponseCopyWith(ChatHistoryResponse value, $Res Function(ChatHistoryResponse) _then) = _$ChatHistoryResponseCopyWithImpl;
@useResult
$Res call({
 List<ChatHistoryItem> messages
});




}
/// @nodoc
class _$ChatHistoryResponseCopyWithImpl<$Res>
    implements $ChatHistoryResponseCopyWith<$Res> {
  _$ChatHistoryResponseCopyWithImpl(this._self, this._then);

  final ChatHistoryResponse _self;
  final $Res Function(ChatHistoryResponse) _then;

/// Create a copy of ChatHistoryResponse
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? messages = null,}) {
  return _then(_self.copyWith(
messages: null == messages ? _self.messages : messages // ignore: cast_nullable_to_non_nullable
as List<ChatHistoryItem>,
  ));
}

}


/// Adds pattern-matching-related methods to [ChatHistoryResponse].
extension ChatHistoryResponsePatterns on ChatHistoryResponse {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>(TResult Function( _ChatHistoryResponse value)?  $default,{required TResult orElse(),}){
final _that = this;
switch (_that) {
case _ChatHistoryResponse() when $default != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>(TResult Function( _ChatHistoryResponse value)  $default,){
final _that = this;
switch (_that) {
case _ChatHistoryResponse():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>(TResult? Function( _ChatHistoryResponse value)?  $default,){
final _that = this;
switch (_that) {
case _ChatHistoryResponse() when $default != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>(TResult Function( List<ChatHistoryItem> messages)?  $default,{required TResult orElse(),}) {final _that = this;
switch (_that) {
case _ChatHistoryResponse() when $default != null:
return $default(_that.messages);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>(TResult Function( List<ChatHistoryItem> messages)  $default,) {final _that = this;
switch (_that) {
case _ChatHistoryResponse():
return $default(_that.messages);}
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>(TResult? Function( List<ChatHistoryItem> messages)?  $default,) {final _that = this;
switch (_that) {
case _ChatHistoryResponse() when $default != null:
return $default(_that.messages);case _:
  return null;

}
}

}

/// @nodoc
@JsonSerializable()

class _ChatHistoryResponse implements ChatHistoryResponse {
  const _ChatHistoryResponse({final  List<ChatHistoryItem> messages = const []}): _messages = messages;
  factory _ChatHistoryResponse.fromJson(Map<String, dynamic> json) => _$ChatHistoryResponseFromJson(json);

 final  List<ChatHistoryItem> _messages;
@override@JsonKey() List<ChatHistoryItem> get messages {
  if (_messages is EqualUnmodifiableListView) return _messages;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_messages);
}


/// Create a copy of ChatHistoryResponse
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$ChatHistoryResponseCopyWith<_ChatHistoryResponse> get copyWith => __$ChatHistoryResponseCopyWithImpl<_ChatHistoryResponse>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$ChatHistoryResponseToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _ChatHistoryResponse&&const DeepCollectionEquality().equals(other._messages, _messages));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,const DeepCollectionEquality().hash(_messages));

@override
String toString() {
  return 'ChatHistoryResponse(messages: $messages)';
}


}

/// @nodoc
abstract mixin class _$ChatHistoryResponseCopyWith<$Res> implements $ChatHistoryResponseCopyWith<$Res> {
  factory _$ChatHistoryResponseCopyWith(_ChatHistoryResponse value, $Res Function(_ChatHistoryResponse) _then) = __$ChatHistoryResponseCopyWithImpl;
@override @useResult
$Res call({
 List<ChatHistoryItem> messages
});




}
/// @nodoc
class __$ChatHistoryResponseCopyWithImpl<$Res>
    implements _$ChatHistoryResponseCopyWith<$Res> {
  __$ChatHistoryResponseCopyWithImpl(this._self, this._then);

  final _ChatHistoryResponse _self;
  final $Res Function(_ChatHistoryResponse) _then;

/// Create a copy of ChatHistoryResponse
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? messages = null,}) {
  return _then(_ChatHistoryResponse(
messages: null == messages ? _self._messages : messages // ignore: cast_nullable_to_non_nullable
as List<ChatHistoryItem>,
  ));
}


}


/// @nodoc
mixin _$ChatHistoryItem {

@JsonKey(name: 'user_message') String? get userMessage;@JsonKey(name: 'assistant_reply') String? get assistantReply;@JsonKey(name: 'created_at') String? get createdAt;
/// Create a copy of ChatHistoryItem
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$ChatHistoryItemCopyWith<ChatHistoryItem> get copyWith => _$ChatHistoryItemCopyWithImpl<ChatHistoryItem>(this as ChatHistoryItem, _$identity);

  /// Serializes this ChatHistoryItem to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is ChatHistoryItem&&(identical(other.userMessage, userMessage) || other.userMessage == userMessage)&&(identical(other.assistantReply, assistantReply) || other.assistantReply == assistantReply)&&(identical(other.createdAt, createdAt) || other.createdAt == createdAt));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,userMessage,assistantReply,createdAt);

@override
String toString() {
  return 'ChatHistoryItem(userMessage: $userMessage, assistantReply: $assistantReply, createdAt: $createdAt)';
}


}

/// @nodoc
abstract mixin class $ChatHistoryItemCopyWith<$Res>  {
  factory $ChatHistoryItemCopyWith(ChatHistoryItem value, $Res Function(ChatHistoryItem) _then) = _$ChatHistoryItemCopyWithImpl;
@useResult
$Res call({
@JsonKey(name: 'user_message') String? userMessage,@JsonKey(name: 'assistant_reply') String? assistantReply,@JsonKey(name: 'created_at') String? createdAt
});




}
/// @nodoc
class _$ChatHistoryItemCopyWithImpl<$Res>
    implements $ChatHistoryItemCopyWith<$Res> {
  _$ChatHistoryItemCopyWithImpl(this._self, this._then);

  final ChatHistoryItem _self;
  final $Res Function(ChatHistoryItem) _then;

/// Create a copy of ChatHistoryItem
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? userMessage = freezed,Object? assistantReply = freezed,Object? createdAt = freezed,}) {
  return _then(_self.copyWith(
userMessage: freezed == userMessage ? _self.userMessage : userMessage // ignore: cast_nullable_to_non_nullable
as String?,assistantReply: freezed == assistantReply ? _self.assistantReply : assistantReply // ignore: cast_nullable_to_non_nullable
as String?,createdAt: freezed == createdAt ? _self.createdAt : createdAt // ignore: cast_nullable_to_non_nullable
as String?,
  ));
}

}


/// Adds pattern-matching-related methods to [ChatHistoryItem].
extension ChatHistoryItemPatterns on ChatHistoryItem {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>(TResult Function( _ChatHistoryItem value)?  $default,{required TResult orElse(),}){
final _that = this;
switch (_that) {
case _ChatHistoryItem() when $default != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>(TResult Function( _ChatHistoryItem value)  $default,){
final _that = this;
switch (_that) {
case _ChatHistoryItem():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>(TResult? Function( _ChatHistoryItem value)?  $default,){
final _that = this;
switch (_that) {
case _ChatHistoryItem() when $default != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>(TResult Function(@JsonKey(name: 'user_message')  String? userMessage, @JsonKey(name: 'assistant_reply')  String? assistantReply, @JsonKey(name: 'created_at')  String? createdAt)?  $default,{required TResult orElse(),}) {final _that = this;
switch (_that) {
case _ChatHistoryItem() when $default != null:
return $default(_that.userMessage,_that.assistantReply,_that.createdAt);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>(TResult Function(@JsonKey(name: 'user_message')  String? userMessage, @JsonKey(name: 'assistant_reply')  String? assistantReply, @JsonKey(name: 'created_at')  String? createdAt)  $default,) {final _that = this;
switch (_that) {
case _ChatHistoryItem():
return $default(_that.userMessage,_that.assistantReply,_that.createdAt);}
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>(TResult? Function(@JsonKey(name: 'user_message')  String? userMessage, @JsonKey(name: 'assistant_reply')  String? assistantReply, @JsonKey(name: 'created_at')  String? createdAt)?  $default,) {final _that = this;
switch (_that) {
case _ChatHistoryItem() when $default != null:
return $default(_that.userMessage,_that.assistantReply,_that.createdAt);case _:
  return null;

}
}

}

/// @nodoc
@JsonSerializable()

class _ChatHistoryItem implements ChatHistoryItem {
  const _ChatHistoryItem({@JsonKey(name: 'user_message') this.userMessage, @JsonKey(name: 'assistant_reply') this.assistantReply, @JsonKey(name: 'created_at') this.createdAt});
  factory _ChatHistoryItem.fromJson(Map<String, dynamic> json) => _$ChatHistoryItemFromJson(json);

@override@JsonKey(name: 'user_message') final  String? userMessage;
@override@JsonKey(name: 'assistant_reply') final  String? assistantReply;
@override@JsonKey(name: 'created_at') final  String? createdAt;

/// Create a copy of ChatHistoryItem
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$ChatHistoryItemCopyWith<_ChatHistoryItem> get copyWith => __$ChatHistoryItemCopyWithImpl<_ChatHistoryItem>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$ChatHistoryItemToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _ChatHistoryItem&&(identical(other.userMessage, userMessage) || other.userMessage == userMessage)&&(identical(other.assistantReply, assistantReply) || other.assistantReply == assistantReply)&&(identical(other.createdAt, createdAt) || other.createdAt == createdAt));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,userMessage,assistantReply,createdAt);

@override
String toString() {
  return 'ChatHistoryItem(userMessage: $userMessage, assistantReply: $assistantReply, createdAt: $createdAt)';
}


}

/// @nodoc
abstract mixin class _$ChatHistoryItemCopyWith<$Res> implements $ChatHistoryItemCopyWith<$Res> {
  factory _$ChatHistoryItemCopyWith(_ChatHistoryItem value, $Res Function(_ChatHistoryItem) _then) = __$ChatHistoryItemCopyWithImpl;
@override @useResult
$Res call({
@JsonKey(name: 'user_message') String? userMessage,@JsonKey(name: 'assistant_reply') String? assistantReply,@JsonKey(name: 'created_at') String? createdAt
});




}
/// @nodoc
class __$ChatHistoryItemCopyWithImpl<$Res>
    implements _$ChatHistoryItemCopyWith<$Res> {
  __$ChatHistoryItemCopyWithImpl(this._self, this._then);

  final _ChatHistoryItem _self;
  final $Res Function(_ChatHistoryItem) _then;

/// Create a copy of ChatHistoryItem
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? userMessage = freezed,Object? assistantReply = freezed,Object? createdAt = freezed,}) {
  return _then(_ChatHistoryItem(
userMessage: freezed == userMessage ? _self.userMessage : userMessage // ignore: cast_nullable_to_non_nullable
as String?,assistantReply: freezed == assistantReply ? _self.assistantReply : assistantReply // ignore: cast_nullable_to_non_nullable
as String?,createdAt: freezed == createdAt ? _self.createdAt : createdAt // ignore: cast_nullable_to_non_nullable
as String?,
  ));
}


}

// dart format on
