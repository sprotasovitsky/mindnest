// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'chat_message.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

_$ChatMessageImpl _$$ChatMessageImplFromJson(Map<String, dynamic> json) =>
    _$ChatMessageImpl(
      content: json['content'] as String,
      isUser: json['isUser'] as bool,
      timestamp: DateTime.parse(json['timestamp'] as String),
      confidence: (json['confidence'] as num?)?.toDouble(),
      isError: json['isError'] as bool? ?? false,
    );

Map<String, dynamic> _$$ChatMessageImplToJson(_$ChatMessageImpl instance) =>
    <String, dynamic>{
      'content': instance.content,
      'isUser': instance.isUser,
      'timestamp': instance.timestamp.toIso8601String(),
      'confidence': instance.confidence,
      'isError': instance.isError,
    };

_$ChatResponseImpl _$$ChatResponseImplFromJson(Map<String, dynamic> json) =>
    _$ChatResponseImpl(
      reply: json['reply'] as String,
      confidence: (json['confidence'] as num?)?.toDouble(),
      messageType: json['message_type'] as String?,
    );

Map<String, dynamic> _$$ChatResponseImplToJson(_$ChatResponseImpl instance) =>
    <String, dynamic>{
      'reply': instance.reply,
      'confidence': instance.confidence,
      'message_type': instance.messageType,
    };

_$ChatHistoryResponseImpl _$$ChatHistoryResponseImplFromJson(
        Map<String, dynamic> json) =>
    _$ChatHistoryResponseImpl(
      messages: (json['messages'] as List<dynamic>?)
              ?.map((e) => ChatHistoryItem.fromJson(e as Map<String, dynamic>))
              .toList() ??
          const [],
    );

Map<String, dynamic> _$$ChatHistoryResponseImplToJson(
        _$ChatHistoryResponseImpl instance) =>
    <String, dynamic>{
      'messages': instance.messages,
    };

_$ChatHistoryItemImpl _$$ChatHistoryItemImplFromJson(
        Map<String, dynamic> json) =>
    _$ChatHistoryItemImpl(
      userMessage: json['user_message'] as String?,
      assistantReply: json['assistant_reply'] as String?,
      createdAt: json['created_at'] as String?,
    );

Map<String, dynamic> _$$ChatHistoryItemImplToJson(
        _$ChatHistoryItemImpl instance) =>
    <String, dynamic>{
      'user_message': instance.userMessage,
      'assistant_reply': instance.assistantReply,
      'created_at': instance.createdAt,
    };
