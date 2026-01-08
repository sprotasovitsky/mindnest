import 'package:dio/dio.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../api/api_client.dart';
import '../constants/app_config.dart';
import '../error/app_error.dart';
import '../models/chat_message.dart';

part 'chat_repository.g.dart';

/// Repository for chat operations
abstract class ChatRepository {
  Future<ChatResponse> sendMessage(String message, {String? projectId});
  Future<List<ChatMessage>> getChatHistory(String projectId,
      {int limit = AppConfig.chatHistoryLimit});
}

class ChatRepositoryImpl implements ChatRepository {
  final ApiClient _apiClient;

  ChatRepositoryImpl(this._apiClient);

  @override
  Future<ChatResponse> sendMessage(String message, {String? projectId}) async {
    try {
      final response = await _apiClient.chat(message, projectId: projectId);
      return ChatResponse.fromJson(response);
    } on DioException catch (e) {
      throw NetworkError.fromDioException(e);
    }
  }

  @override
  Future<List<ChatMessage>> getChatHistory(String projectId,
      {int limit = AppConfig.chatHistoryLimit}) async {
    try {
      final response = await _apiClient.getChatHistory(projectId, limit: limit);
      final messages = response['messages'] as List<dynamic>? ?? [];

      final chatMessages = <ChatMessage>[];
      for (final msg in messages) {
        final userMessage = msg['user_message'] as String?;
        final assistantReply = msg['assistant_reply'] as String?;
        final createdAt = DateTime.tryParse(msg['created_at'] ?? '') ?? DateTime.now();

        if (userMessage != null && userMessage.isNotEmpty) {
          chatMessages.add(ChatMessage(
            content: userMessage,
            isUser: true,
            timestamp: createdAt,
          ));
        }
        if (assistantReply != null && assistantReply.isNotEmpty) {
          chatMessages.add(ChatMessage(
            content: assistantReply,
            isUser: false,
            timestamp: createdAt,
          ));
        }
      }
      return chatMessages;
    } on DioException catch (e) {
      throw NetworkError.fromDioException(e);
    }
  }
}

@riverpod
ChatRepository chatRepository(ChatRepositoryRef ref) {
  final apiClient = ref.watch(apiClientProvider);
  return ChatRepositoryImpl(apiClient);
}
