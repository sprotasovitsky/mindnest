import 'package:freezed_annotation/freezed_annotation.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../error/app_error.dart';
import '../models/chat_message.dart';
import '../models/project.dart';
import '../repositories/chat_repository.dart';
import '../utils/logger.dart';
import 'auth_provider.dart';
import 'project_provider.dart';

part 'chat_provider.freezed.dart';
part 'chat_provider.g.dart';

@freezed
class ChatState with _$ChatState {
  const factory ChatState({
    @Default([]) List<ChatMessage> messages,
    @Default(false) bool isLoading,
    @Default(false) bool isLoadingHistory,
    String? lastProjectId,
    String? error,
  }) = _ChatState;
}

@riverpod
class Chat extends _$Chat {
  @override
  ChatState build() {
    return const ChatState();
  }

  /// Get the first message based on project state
  String _getFirstMessage(Project? project, String? userId) {
    if (project == null) {
      return 'Hi! I\'m MindNest — your personal assistant for knowledge and task management. How can I help?';
    }

    final isOwner = userId != null && project.ownerId == userId;

    if (project.needsOnboarding && isOwner) {
      return 'Hi! Let\'s set up your project. Just reply here: what is this project about? What do you want to track or manage?\n\nOnce we finish setup, you\'ll be able to add team members.';
    } else {
      return 'Welcome to "${project.name}"! How can I help you today?';
    }
  }

  Future<void> initializeForProject(String projectId) async {
    if (state.lastProjectId == projectId) return;

    state = state.copyWith(isLoadingHistory: true, lastProjectId: projectId);

    final repository = ref.read(chatRepositoryProvider);

    try {
      final messages = await repository.getChatHistory(projectId);

      if (messages.isNotEmpty) {
        state = state.copyWith(
          messages: messages,
          isLoadingHistory: false,
        );
        return;
      }
    } catch (e) {
      AppLogger.warning(
        'Failed to load chat history: $e',
        tag: 'ChatProvider',
      );
    }

    // No history - show welcome message
    final projectState = ref.read(projectsProvider);
    final authState = ref.read(authProvider);
    final firstMessage = _getFirstMessage(
      projectState.currentProject,
      authState.userId,
    );

    state = state.copyWith(
      messages: [ChatMessageFactory.assistant(firstMessage)],
      isLoadingHistory: false,
    );
  }

  Future<void> sendMessage(String text) async {
    if (text.trim().isEmpty) return;

    // Add user message
    state = state.copyWith(
      messages: [...state.messages, ChatMessageFactory.user(text)],
      isLoading: true,
    );

    try {
      final repository = ref.read(chatRepositoryProvider);
      final projectState = ref.read(projectsProvider);

      final response = await repository.sendMessage(
        text,
        projectId: projectState.currentProject?.id,
      );

      state = state.copyWith(
        messages: [
          ...state.messages,
          ChatMessageFactory.assistant(
            response.reply,
            confidence: response.confidence,
          ),
        ],
        isLoading: false,
      );

      // After onboarding response, refresh project to get updated description
      if (response.messageType == 'ONBOARDING') {
        ref.read(projectsProvider.notifier).loadProjects();
      }
    } catch (e) {
      state = state.copyWith(
        messages: [
          ...state.messages,
          ChatMessageFactory.error('Error: ${e.toUserMessage()}'),
        ],
        isLoading: false,
      );
    }
  }

  void clearMessages() {
    state = const ChatState();
  }
}
