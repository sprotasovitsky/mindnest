// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

part of 'chat_message.dart';

// **************************************************************************
// FreezedGenerator
// **************************************************************************

T _$identity<T>(T value) => value;

final _privateConstructorUsedError = UnsupportedError(
    'It seems like you constructed your class using `MyClass._()`. This constructor is only meant to be used by freezed and you are not supposed to need it nor use it.\nPlease check the documentation here for more information: https://github.com/rrousselGit/freezed#adding-getters-and-methods-to-our-models');

ChatMessage _$ChatMessageFromJson(Map<String, dynamic> json) {
  return _ChatMessage.fromJson(json);
}

/// @nodoc
mixin _$ChatMessage {
  String get content => throw _privateConstructorUsedError;
  bool get isUser => throw _privateConstructorUsedError;
  DateTime get timestamp => throw _privateConstructorUsedError;
  double? get confidence => throw _privateConstructorUsedError;
  bool get isError => throw _privateConstructorUsedError;

  /// Serializes this ChatMessage to a JSON map.
  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;

  /// Create a copy of ChatMessage
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $ChatMessageCopyWith<ChatMessage> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $ChatMessageCopyWith<$Res> {
  factory $ChatMessageCopyWith(
          ChatMessage value, $Res Function(ChatMessage) then) =
      _$ChatMessageCopyWithImpl<$Res, ChatMessage>;
  @useResult
  $Res call(
      {String content,
      bool isUser,
      DateTime timestamp,
      double? confidence,
      bool isError});
}

/// @nodoc
class _$ChatMessageCopyWithImpl<$Res, $Val extends ChatMessage>
    implements $ChatMessageCopyWith<$Res> {
  _$ChatMessageCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of ChatMessage
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? content = null,
    Object? isUser = null,
    Object? timestamp = null,
    Object? confidence = freezed,
    Object? isError = null,
  }) {
    return _then(_value.copyWith(
      content: null == content
          ? _value.content
          : content // ignore: cast_nullable_to_non_nullable
              as String,
      isUser: null == isUser
          ? _value.isUser
          : isUser // ignore: cast_nullable_to_non_nullable
              as bool,
      timestamp: null == timestamp
          ? _value.timestamp
          : timestamp // ignore: cast_nullable_to_non_nullable
              as DateTime,
      confidence: freezed == confidence
          ? _value.confidence
          : confidence // ignore: cast_nullable_to_non_nullable
              as double?,
      isError: null == isError
          ? _value.isError
          : isError // ignore: cast_nullable_to_non_nullable
              as bool,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$ChatMessageImplCopyWith<$Res>
    implements $ChatMessageCopyWith<$Res> {
  factory _$$ChatMessageImplCopyWith(
          _$ChatMessageImpl value, $Res Function(_$ChatMessageImpl) then) =
      __$$ChatMessageImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {String content,
      bool isUser,
      DateTime timestamp,
      double? confidence,
      bool isError});
}

/// @nodoc
class __$$ChatMessageImplCopyWithImpl<$Res>
    extends _$ChatMessageCopyWithImpl<$Res, _$ChatMessageImpl>
    implements _$$ChatMessageImplCopyWith<$Res> {
  __$$ChatMessageImplCopyWithImpl(
      _$ChatMessageImpl _value, $Res Function(_$ChatMessageImpl) _then)
      : super(_value, _then);

  /// Create a copy of ChatMessage
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? content = null,
    Object? isUser = null,
    Object? timestamp = null,
    Object? confidence = freezed,
    Object? isError = null,
  }) {
    return _then(_$ChatMessageImpl(
      content: null == content
          ? _value.content
          : content // ignore: cast_nullable_to_non_nullable
              as String,
      isUser: null == isUser
          ? _value.isUser
          : isUser // ignore: cast_nullable_to_non_nullable
              as bool,
      timestamp: null == timestamp
          ? _value.timestamp
          : timestamp // ignore: cast_nullable_to_non_nullable
              as DateTime,
      confidence: freezed == confidence
          ? _value.confidence
          : confidence // ignore: cast_nullable_to_non_nullable
              as double?,
      isError: null == isError
          ? _value.isError
          : isError // ignore: cast_nullable_to_non_nullable
              as bool,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$ChatMessageImpl implements _ChatMessage {
  const _$ChatMessageImpl(
      {required this.content,
      required this.isUser,
      required this.timestamp,
      this.confidence,
      this.isError = false});

  factory _$ChatMessageImpl.fromJson(Map<String, dynamic> json) =>
      _$$ChatMessageImplFromJson(json);

  @override
  final String content;
  @override
  final bool isUser;
  @override
  final DateTime timestamp;
  @override
  final double? confidence;
  @override
  @JsonKey()
  final bool isError;

  @override
  String toString() {
    return 'ChatMessage(content: $content, isUser: $isUser, timestamp: $timestamp, confidence: $confidence, isError: $isError)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$ChatMessageImpl &&
            (identical(other.content, content) || other.content == content) &&
            (identical(other.isUser, isUser) || other.isUser == isUser) &&
            (identical(other.timestamp, timestamp) ||
                other.timestamp == timestamp) &&
            (identical(other.confidence, confidence) ||
                other.confidence == confidence) &&
            (identical(other.isError, isError) || other.isError == isError));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode =>
      Object.hash(runtimeType, content, isUser, timestamp, confidence, isError);

  /// Create a copy of ChatMessage
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$ChatMessageImplCopyWith<_$ChatMessageImpl> get copyWith =>
      __$$ChatMessageImplCopyWithImpl<_$ChatMessageImpl>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$ChatMessageImplToJson(
      this,
    );
  }
}

abstract class _ChatMessage implements ChatMessage {
  const factory _ChatMessage(
      {required final String content,
      required final bool isUser,
      required final DateTime timestamp,
      final double? confidence,
      final bool isError}) = _$ChatMessageImpl;

  factory _ChatMessage.fromJson(Map<String, dynamic> json) =
      _$ChatMessageImpl.fromJson;

  @override
  String get content;
  @override
  bool get isUser;
  @override
  DateTime get timestamp;
  @override
  double? get confidence;
  @override
  bool get isError;

  /// Create a copy of ChatMessage
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$ChatMessageImplCopyWith<_$ChatMessageImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

ChatResponse _$ChatResponseFromJson(Map<String, dynamic> json) {
  return _ChatResponse.fromJson(json);
}

/// @nodoc
mixin _$ChatResponse {
  String get reply => throw _privateConstructorUsedError;
  double? get confidence => throw _privateConstructorUsedError;
  @JsonKey(name: 'message_type')
  String? get messageType => throw _privateConstructorUsedError;

  /// Serializes this ChatResponse to a JSON map.
  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;

  /// Create a copy of ChatResponse
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $ChatResponseCopyWith<ChatResponse> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $ChatResponseCopyWith<$Res> {
  factory $ChatResponseCopyWith(
          ChatResponse value, $Res Function(ChatResponse) then) =
      _$ChatResponseCopyWithImpl<$Res, ChatResponse>;
  @useResult
  $Res call(
      {String reply,
      double? confidence,
      @JsonKey(name: 'message_type') String? messageType});
}

/// @nodoc
class _$ChatResponseCopyWithImpl<$Res, $Val extends ChatResponse>
    implements $ChatResponseCopyWith<$Res> {
  _$ChatResponseCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of ChatResponse
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? reply = null,
    Object? confidence = freezed,
    Object? messageType = freezed,
  }) {
    return _then(_value.copyWith(
      reply: null == reply
          ? _value.reply
          : reply // ignore: cast_nullable_to_non_nullable
              as String,
      confidence: freezed == confidence
          ? _value.confidence
          : confidence // ignore: cast_nullable_to_non_nullable
              as double?,
      messageType: freezed == messageType
          ? _value.messageType
          : messageType // ignore: cast_nullable_to_non_nullable
              as String?,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$ChatResponseImplCopyWith<$Res>
    implements $ChatResponseCopyWith<$Res> {
  factory _$$ChatResponseImplCopyWith(
          _$ChatResponseImpl value, $Res Function(_$ChatResponseImpl) then) =
      __$$ChatResponseImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {String reply,
      double? confidence,
      @JsonKey(name: 'message_type') String? messageType});
}

/// @nodoc
class __$$ChatResponseImplCopyWithImpl<$Res>
    extends _$ChatResponseCopyWithImpl<$Res, _$ChatResponseImpl>
    implements _$$ChatResponseImplCopyWith<$Res> {
  __$$ChatResponseImplCopyWithImpl(
      _$ChatResponseImpl _value, $Res Function(_$ChatResponseImpl) _then)
      : super(_value, _then);

  /// Create a copy of ChatResponse
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? reply = null,
    Object? confidence = freezed,
    Object? messageType = freezed,
  }) {
    return _then(_$ChatResponseImpl(
      reply: null == reply
          ? _value.reply
          : reply // ignore: cast_nullable_to_non_nullable
              as String,
      confidence: freezed == confidence
          ? _value.confidence
          : confidence // ignore: cast_nullable_to_non_nullable
              as double?,
      messageType: freezed == messageType
          ? _value.messageType
          : messageType // ignore: cast_nullable_to_non_nullable
              as String?,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$ChatResponseImpl implements _ChatResponse {
  const _$ChatResponseImpl(
      {required this.reply,
      this.confidence,
      @JsonKey(name: 'message_type') this.messageType});

  factory _$ChatResponseImpl.fromJson(Map<String, dynamic> json) =>
      _$$ChatResponseImplFromJson(json);

  @override
  final String reply;
  @override
  final double? confidence;
  @override
  @JsonKey(name: 'message_type')
  final String? messageType;

  @override
  String toString() {
    return 'ChatResponse(reply: $reply, confidence: $confidence, messageType: $messageType)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$ChatResponseImpl &&
            (identical(other.reply, reply) || other.reply == reply) &&
            (identical(other.confidence, confidence) ||
                other.confidence == confidence) &&
            (identical(other.messageType, messageType) ||
                other.messageType == messageType));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hash(runtimeType, reply, confidence, messageType);

  /// Create a copy of ChatResponse
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$ChatResponseImplCopyWith<_$ChatResponseImpl> get copyWith =>
      __$$ChatResponseImplCopyWithImpl<_$ChatResponseImpl>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$ChatResponseImplToJson(
      this,
    );
  }
}

abstract class _ChatResponse implements ChatResponse {
  const factory _ChatResponse(
          {required final String reply,
          final double? confidence,
          @JsonKey(name: 'message_type') final String? messageType}) =
      _$ChatResponseImpl;

  factory _ChatResponse.fromJson(Map<String, dynamic> json) =
      _$ChatResponseImpl.fromJson;

  @override
  String get reply;
  @override
  double? get confidence;
  @override
  @JsonKey(name: 'message_type')
  String? get messageType;

  /// Create a copy of ChatResponse
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$ChatResponseImplCopyWith<_$ChatResponseImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

ChatHistoryResponse _$ChatHistoryResponseFromJson(Map<String, dynamic> json) {
  return _ChatHistoryResponse.fromJson(json);
}

/// @nodoc
mixin _$ChatHistoryResponse {
  List<ChatHistoryItem> get messages => throw _privateConstructorUsedError;

  /// Serializes this ChatHistoryResponse to a JSON map.
  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;

  /// Create a copy of ChatHistoryResponse
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $ChatHistoryResponseCopyWith<ChatHistoryResponse> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $ChatHistoryResponseCopyWith<$Res> {
  factory $ChatHistoryResponseCopyWith(
          ChatHistoryResponse value, $Res Function(ChatHistoryResponse) then) =
      _$ChatHistoryResponseCopyWithImpl<$Res, ChatHistoryResponse>;
  @useResult
  $Res call({List<ChatHistoryItem> messages});
}

/// @nodoc
class _$ChatHistoryResponseCopyWithImpl<$Res, $Val extends ChatHistoryResponse>
    implements $ChatHistoryResponseCopyWith<$Res> {
  _$ChatHistoryResponseCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of ChatHistoryResponse
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? messages = null,
  }) {
    return _then(_value.copyWith(
      messages: null == messages
          ? _value.messages
          : messages // ignore: cast_nullable_to_non_nullable
              as List<ChatHistoryItem>,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$ChatHistoryResponseImplCopyWith<$Res>
    implements $ChatHistoryResponseCopyWith<$Res> {
  factory _$$ChatHistoryResponseImplCopyWith(_$ChatHistoryResponseImpl value,
          $Res Function(_$ChatHistoryResponseImpl) then) =
      __$$ChatHistoryResponseImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call({List<ChatHistoryItem> messages});
}

/// @nodoc
class __$$ChatHistoryResponseImplCopyWithImpl<$Res>
    extends _$ChatHistoryResponseCopyWithImpl<$Res, _$ChatHistoryResponseImpl>
    implements _$$ChatHistoryResponseImplCopyWith<$Res> {
  __$$ChatHistoryResponseImplCopyWithImpl(_$ChatHistoryResponseImpl _value,
      $Res Function(_$ChatHistoryResponseImpl) _then)
      : super(_value, _then);

  /// Create a copy of ChatHistoryResponse
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? messages = null,
  }) {
    return _then(_$ChatHistoryResponseImpl(
      messages: null == messages
          ? _value._messages
          : messages // ignore: cast_nullable_to_non_nullable
              as List<ChatHistoryItem>,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$ChatHistoryResponseImpl implements _ChatHistoryResponse {
  const _$ChatHistoryResponseImpl(
      {final List<ChatHistoryItem> messages = const []})
      : _messages = messages;

  factory _$ChatHistoryResponseImpl.fromJson(Map<String, dynamic> json) =>
      _$$ChatHistoryResponseImplFromJson(json);

  final List<ChatHistoryItem> _messages;
  @override
  @JsonKey()
  List<ChatHistoryItem> get messages {
    if (_messages is EqualUnmodifiableListView) return _messages;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_messages);
  }

  @override
  String toString() {
    return 'ChatHistoryResponse(messages: $messages)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$ChatHistoryResponseImpl &&
            const DeepCollectionEquality().equals(other._messages, _messages));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode =>
      Object.hash(runtimeType, const DeepCollectionEquality().hash(_messages));

  /// Create a copy of ChatHistoryResponse
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$ChatHistoryResponseImplCopyWith<_$ChatHistoryResponseImpl> get copyWith =>
      __$$ChatHistoryResponseImplCopyWithImpl<_$ChatHistoryResponseImpl>(
          this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$ChatHistoryResponseImplToJson(
      this,
    );
  }
}

abstract class _ChatHistoryResponse implements ChatHistoryResponse {
  const factory _ChatHistoryResponse({final List<ChatHistoryItem> messages}) =
      _$ChatHistoryResponseImpl;

  factory _ChatHistoryResponse.fromJson(Map<String, dynamic> json) =
      _$ChatHistoryResponseImpl.fromJson;

  @override
  List<ChatHistoryItem> get messages;

  /// Create a copy of ChatHistoryResponse
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$ChatHistoryResponseImplCopyWith<_$ChatHistoryResponseImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

ChatHistoryItem _$ChatHistoryItemFromJson(Map<String, dynamic> json) {
  return _ChatHistoryItem.fromJson(json);
}

/// @nodoc
mixin _$ChatHistoryItem {
  @JsonKey(name: 'user_message')
  String? get userMessage => throw _privateConstructorUsedError;
  @JsonKey(name: 'assistant_reply')
  String? get assistantReply => throw _privateConstructorUsedError;
  @JsonKey(name: 'created_at')
  String? get createdAt => throw _privateConstructorUsedError;

  /// Serializes this ChatHistoryItem to a JSON map.
  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;

  /// Create a copy of ChatHistoryItem
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $ChatHistoryItemCopyWith<ChatHistoryItem> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $ChatHistoryItemCopyWith<$Res> {
  factory $ChatHistoryItemCopyWith(
          ChatHistoryItem value, $Res Function(ChatHistoryItem) then) =
      _$ChatHistoryItemCopyWithImpl<$Res, ChatHistoryItem>;
  @useResult
  $Res call(
      {@JsonKey(name: 'user_message') String? userMessage,
      @JsonKey(name: 'assistant_reply') String? assistantReply,
      @JsonKey(name: 'created_at') String? createdAt});
}

/// @nodoc
class _$ChatHistoryItemCopyWithImpl<$Res, $Val extends ChatHistoryItem>
    implements $ChatHistoryItemCopyWith<$Res> {
  _$ChatHistoryItemCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of ChatHistoryItem
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? userMessage = freezed,
    Object? assistantReply = freezed,
    Object? createdAt = freezed,
  }) {
    return _then(_value.copyWith(
      userMessage: freezed == userMessage
          ? _value.userMessage
          : userMessage // ignore: cast_nullable_to_non_nullable
              as String?,
      assistantReply: freezed == assistantReply
          ? _value.assistantReply
          : assistantReply // ignore: cast_nullable_to_non_nullable
              as String?,
      createdAt: freezed == createdAt
          ? _value.createdAt
          : createdAt // ignore: cast_nullable_to_non_nullable
              as String?,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$ChatHistoryItemImplCopyWith<$Res>
    implements $ChatHistoryItemCopyWith<$Res> {
  factory _$$ChatHistoryItemImplCopyWith(_$ChatHistoryItemImpl value,
          $Res Function(_$ChatHistoryItemImpl) then) =
      __$$ChatHistoryItemImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {@JsonKey(name: 'user_message') String? userMessage,
      @JsonKey(name: 'assistant_reply') String? assistantReply,
      @JsonKey(name: 'created_at') String? createdAt});
}

/// @nodoc
class __$$ChatHistoryItemImplCopyWithImpl<$Res>
    extends _$ChatHistoryItemCopyWithImpl<$Res, _$ChatHistoryItemImpl>
    implements _$$ChatHistoryItemImplCopyWith<$Res> {
  __$$ChatHistoryItemImplCopyWithImpl(
      _$ChatHistoryItemImpl _value, $Res Function(_$ChatHistoryItemImpl) _then)
      : super(_value, _then);

  /// Create a copy of ChatHistoryItem
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? userMessage = freezed,
    Object? assistantReply = freezed,
    Object? createdAt = freezed,
  }) {
    return _then(_$ChatHistoryItemImpl(
      userMessage: freezed == userMessage
          ? _value.userMessage
          : userMessage // ignore: cast_nullable_to_non_nullable
              as String?,
      assistantReply: freezed == assistantReply
          ? _value.assistantReply
          : assistantReply // ignore: cast_nullable_to_non_nullable
              as String?,
      createdAt: freezed == createdAt
          ? _value.createdAt
          : createdAt // ignore: cast_nullable_to_non_nullable
              as String?,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$ChatHistoryItemImpl implements _ChatHistoryItem {
  const _$ChatHistoryItemImpl(
      {@JsonKey(name: 'user_message') this.userMessage,
      @JsonKey(name: 'assistant_reply') this.assistantReply,
      @JsonKey(name: 'created_at') this.createdAt});

  factory _$ChatHistoryItemImpl.fromJson(Map<String, dynamic> json) =>
      _$$ChatHistoryItemImplFromJson(json);

  @override
  @JsonKey(name: 'user_message')
  final String? userMessage;
  @override
  @JsonKey(name: 'assistant_reply')
  final String? assistantReply;
  @override
  @JsonKey(name: 'created_at')
  final String? createdAt;

  @override
  String toString() {
    return 'ChatHistoryItem(userMessage: $userMessage, assistantReply: $assistantReply, createdAt: $createdAt)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$ChatHistoryItemImpl &&
            (identical(other.userMessage, userMessage) ||
                other.userMessage == userMessage) &&
            (identical(other.assistantReply, assistantReply) ||
                other.assistantReply == assistantReply) &&
            (identical(other.createdAt, createdAt) ||
                other.createdAt == createdAt));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode =>
      Object.hash(runtimeType, userMessage, assistantReply, createdAt);

  /// Create a copy of ChatHistoryItem
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$ChatHistoryItemImplCopyWith<_$ChatHistoryItemImpl> get copyWith =>
      __$$ChatHistoryItemImplCopyWithImpl<_$ChatHistoryItemImpl>(
          this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$ChatHistoryItemImplToJson(
      this,
    );
  }
}

abstract class _ChatHistoryItem implements ChatHistoryItem {
  const factory _ChatHistoryItem(
          {@JsonKey(name: 'user_message') final String? userMessage,
          @JsonKey(name: 'assistant_reply') final String? assistantReply,
          @JsonKey(name: 'created_at') final String? createdAt}) =
      _$ChatHistoryItemImpl;

  factory _ChatHistoryItem.fromJson(Map<String, dynamic> json) =
      _$ChatHistoryItemImpl.fromJson;

  @override
  @JsonKey(name: 'user_message')
  String? get userMessage;
  @override
  @JsonKey(name: 'assistant_reply')
  String? get assistantReply;
  @override
  @JsonKey(name: 'created_at')
  String? get createdAt;

  /// Create a copy of ChatHistoryItem
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$ChatHistoryItemImplCopyWith<_$ChatHistoryItemImpl> get copyWith =>
      throw _privateConstructorUsedError;
}
