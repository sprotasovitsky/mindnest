// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'chat_message.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

_ChatMessage _$ChatMessageFromJson(Map<String, dynamic> json) => _ChatMessage(
  content: json['content'] as String,
  isUser: json['isUser'] as bool,
  timestamp: DateTime.parse(json['timestamp'] as String),
  confidence: (json['confidence'] as num?)?.toDouble(),
  isError: json['isError'] as bool? ?? false,
);

Map<String, dynamic> _$ChatMessageToJson(_ChatMessage instance) =>
    <String, dynamic>{
      'content': instance.content,
      'isUser': instance.isUser,
      'timestamp': instance.timestamp.toIso8601String(),
      'confidence': instance.confidence,
      'isError': instance.isError,
    };

_ChatResponse _$ChatResponseFromJson(Map<String, dynamic> json) =>
    _ChatResponse(
      reply: json['reply'] as String,
      confidence: (json['confidence'] as num?)?.toDouble(),
      messageType: json['message_type'] as String?,
    );

Map<String, dynamic> _$ChatResponseToJson(_ChatResponse instance) =>
    <String, dynamic>{
      'reply': instance.reply,
      'confidence': instance.confidence,
      'message_type': instance.messageType,
    };

_ChatHistoryResponse _$ChatHistoryResponseFromJson(Map<String, dynamic> json) =>
    _ChatHistoryResponse(
      messages:
          (json['messages'] as List<dynamic>?)
              ?.map((e) => ChatHistoryItem.fromJson(e as Map<String, dynamic>))
              .toList() ??
          const [],
    );

Map<String, dynamic> _$ChatHistoryResponseToJson(
  _ChatHistoryResponse instance,
) => <String, dynamic>{'messages': instance.messages};

_ChatHistoryItem _$ChatHistoryItemFromJson(Map<String, dynamic> json) =>
    _ChatHistoryItem(
      userMessage: json['user_message'] as String?,
      assistantReply: json['assistant_reply'] as String?,
      createdAt: json['created_at'] as String?,
    );

Map<String, dynamic> _$ChatHistoryItemToJson(_ChatHistoryItem instance) =>
    <String, dynamic>{
      'user_message': instance.userMessage,
      'assistant_reply': instance.assistantReply,
      'created_at': instance.createdAt,
    };
