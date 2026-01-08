import 'package:freezed_annotation/freezed_annotation.dart';

part 'chat_message.freezed.dart';
part 'chat_message.g.dart';

@freezed
class ChatMessage with _$ChatMessage {
  const factory ChatMessage({
    required String content,
    required bool isUser,
    required DateTime timestamp,
    double? confidence,
    @Default(false) bool isError,
  }) = _ChatMessage;

  factory ChatMessage.fromJson(Map<String, dynamic> json) =>
      _$ChatMessageFromJson(json);
}

/// Extension for creating messages easily
extension ChatMessageFactory on ChatMessage {
  static ChatMessage user(String content) => ChatMessage(
        content: content,
        isUser: true,
        timestamp: DateTime.now(),
      );

  static ChatMessage assistant(String content, {double? confidence}) =>
      ChatMessage(
        content: content,
        isUser: false,
        timestamp: DateTime.now(),
        confidence: confidence,
      );

  static ChatMessage error(String content) => ChatMessage(
        content: content,
        isUser: false,
        timestamp: DateTime.now(),
        isError: true,
      );
}

@freezed
class ChatResponse with _$ChatResponse {
  const factory ChatResponse({
    required String reply,
    double? confidence,
    @JsonKey(name: 'message_type') String? messageType,
  }) = _ChatResponse;

  factory ChatResponse.fromJson(Map<String, dynamic> json) =>
      _$ChatResponseFromJson(json);
}

@freezed
class ChatHistoryResponse with _$ChatHistoryResponse {
  const factory ChatHistoryResponse({
    @Default([]) List<ChatHistoryItem> messages,
  }) = _ChatHistoryResponse;

  factory ChatHistoryResponse.fromJson(Map<String, dynamic> json) =>
      _$ChatHistoryResponseFromJson(json);
}

@freezed
class ChatHistoryItem with _$ChatHistoryItem {
  const factory ChatHistoryItem({
    @JsonKey(name: 'user_message') String? userMessage,
    @JsonKey(name: 'assistant_reply') String? assistantReply,
    @JsonKey(name: 'created_at') String? createdAt,
  }) = _ChatHistoryItem;

  factory ChatHistoryItem.fromJson(Map<String, dynamic> json) =>
      _$ChatHistoryItemFromJson(json);
}
