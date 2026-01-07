import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../../core/api/api_client.dart';
import '../../../../core/auth/auth_state.dart';
import '../../../../core/projects/project_state.dart';
import '../widgets/message_bubble.dart';
import '../widgets/chat_input.dart';
import '../../../projects/presentation/widgets/project_settings_sheet.dart';

class ChatMessage {
  final String content;
  final bool isUser;
  final DateTime timestamp;
  final double? confidence;
  final bool isError;

  ChatMessage({
    required this.content,
    required this.isUser,
    DateTime? timestamp,
    this.confidence,
    this.isError = false,
  }) : timestamp = timestamp ?? DateTime.now();
}

/// Get the appropriate first message based on project state
String _getFirstMessage(Project? project, String? userId) {
  if (project == null) {
    return 'Hi! I\'m MindNest — your personal assistant for knowledge and task management. How can I help?';
  }

  final isOwner = userId != null && project.ownerId == userId;

  if (project.needsOnboarding && isOwner) {
    // Owner sees onboarding prompt
    return 'Welcome to your new project! Please tell me what this project is about so I can help you better. What are you working on?';
  } else if (!project.needsOnboarding) {
    // Member (or owner after onboarding) sees welcome with project name
    return 'Welcome to "${project.name}"! How can I help you today?';
  } else {
    // Edge case: member joined project without description (shouldn't happen with backend check)
    return 'Welcome to "${project.name}"! How can I help you today?';
  }
}

final messagesProvider = StateProvider<List<ChatMessage>>((ref) => []);

final isLoadingProvider = StateProvider<bool>((ref) => false);

final isLoadingHistoryProvider = StateProvider<bool>((ref) => false);

class ChatScreen extends ConsumerStatefulWidget {
  const ChatScreen({super.key});

  @override
  ConsumerState<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends ConsumerState<ChatScreen> {
  final ScrollController _scrollController = ScrollController();
  String? _lastProjectId;

  @override
  void initState() {
    super.initState();
    // Initialize messages after first frame when providers are ready
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _initializeMessages();
    });
  }

  Future<void> _initializeMessages() async {
    final projectState = ref.read(projectProvider);
    final authState = ref.read(authProvider);
    final apiClient = ref.read(apiClientProvider);
    final project = projectState.currentProject;

    if (project != null && _lastProjectId != project.id) {
      _lastProjectId = project.id;
      ref.read(isLoadingHistoryProvider.notifier).state = true;

      // Try to load chat history from backend
      try {
        final historyData = await apiClient.getChatHistory(project.id);
        final messages = historyData['messages'] as List<dynamic>? ?? [];

        if (messages.isNotEmpty) {
          // Convert history to ChatMessage list (already oldest first from backend)
          final chatMessages = messages.map((msg) {
            final userMessage = msg['user_message'] as String?;
            final assistantReply = msg['assistant_reply'] as String?;
            final createdAt = DateTime.tryParse(msg['created_at'] ?? '');

            return [
              if (userMessage != null && userMessage.isNotEmpty)
                ChatMessage(
                  content: userMessage,
                  isUser: true,
                  timestamp: createdAt,
                ),
              if (assistantReply != null && assistantReply.isNotEmpty)
                ChatMessage(
                  content: assistantReply,
                  isUser: false,
                  timestamp: createdAt,
                ),
            ];
          }).expand((e) => e).toList();

          ref.read(messagesProvider.notifier).state = chatMessages;
          ref.read(isLoadingHistoryProvider.notifier).state = false;
          _scrollToBottom();
          return;
        }
      } catch (e) {
        // If history loading fails, show welcome message
        print('Failed to load chat history: $e');
      }

      ref.read(isLoadingHistoryProvider.notifier).state = false;

      // No history - show welcome message
      final firstMessage = _getFirstMessage(project, authState.userId);
      ref.read(messagesProvider.notifier).state = [
        ChatMessage(content: firstMessage, isUser: false),
      ];
    }
  }

  @override
  void dispose() {
    _scrollController.dispose();
    super.dispose();
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  Future<void> _sendMessage(String text) async {
    if (text.trim().isEmpty) return;

    final messages = ref.read(messagesProvider.notifier);
    final apiClient = ref.read(apiClientProvider);
    final projectState = ref.read(projectProvider);

    // Add user message
    messages.state = [
      ...messages.state,
      ChatMessage(content: text, isUser: true),
    ];
    _scrollToBottom();

    // Set loading state
    ref.read(isLoadingProvider.notifier).state = true;

    try {
      // Call backend API with current project
      final response = await apiClient.chat(
        text,
        projectId: projectState.currentProject?.id,
      );

      final reply = response['reply'] as String? ?? 'No response';
      final confidence = (response['confidence'] as num?)?.toDouble();
      final messageType = response['message_type'] as String? ?? '';

      messages.state = [
        ...messages.state,
        ChatMessage(
          content: reply,
          isUser: false,
          confidence: confidence,
        ),
      ];

      // After onboarding response, refresh project to get updated description
      if (messageType == 'ONBOARDING') {
        await ref.read(projectProvider.notifier).loadProjects();
      }
    } catch (e) {
      String errorMessage;
      if (e is ApiException) {
        errorMessage = e.message;
      } else {
        errorMessage = 'Could not connect to server. Please check if backend is running.';
      }
      messages.state = [
        ...messages.state,
        ChatMessage(
          content: 'Error: $errorMessage',
          isUser: false,
          isError: true,
        ),
      ];
    } finally {
      ref.read(isLoadingProvider.notifier).state = false;
      _scrollToBottom();
    }
  }

  void _showProjectSettings() {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      builder: (context) => Padding(
        padding: EdgeInsets.only(
          bottom: MediaQuery.of(context).viewInsets.bottom,
        ),
        child: const ProjectSettingsSheet(),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final messages = ref.watch(messagesProvider);
    final isLoading = ref.watch(isLoadingProvider);
    final isLoadingHistory = ref.watch(isLoadingHistoryProvider);
    final projectState = ref.watch(projectProvider);
    final project = projectState.currentProject;
    final canAddMembers = project != null && !project.needsOnboarding;

    // Check if project changed and reinitialize messages
    if (project != null && _lastProjectId != project.id) {
      WidgetsBinding.instance.addPostFrameCallback((_) {
        _initializeMessages();
      });
    }

    return Scaffold(
      appBar: AppBar(
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () => context.go('/projects'),
        ),
        title: Text(project?.name ?? 'Chat'),
        actions: [
          // Only show members button after onboarding is complete
          if (canAddMembers)
            IconButton(
              key: const Key('members_button'),
              icon: const Icon(Icons.group_outlined),
              onPressed: () => context.push('/members'),
              tooltip: 'Members',
            ),
          IconButton(
            key: const Key('settings_button'),
            icon: const Icon(Icons.settings_outlined),
            onPressed: _showProjectSettings,
            tooltip: 'Settings',
          ),
        ],
      ),
      body: SafeArea(
        child: Column(
          children: [
            Expanded(
              child: isLoadingHistory
                  ? const Center(
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          CircularProgressIndicator(),
                          SizedBox(height: 16),
                          Text('Loading chat history...'),
                        ],
                      ),
                    )
                  : ListView.builder(
                      controller: _scrollController,
                      padding: const EdgeInsets.all(16),
                      itemCount: messages.length + (isLoading ? 1 : 0),
                      itemBuilder: (context, index) {
                        if (index == messages.length && isLoading) {
                          return const Padding(
                            padding: EdgeInsets.symmetric(vertical: 8),
                            child: Row(
                              children: [
                                SizedBox(
                                  width: 20,
                                  height: 20,
                                  child: CircularProgressIndicator(strokeWidth: 2),
                                ),
                                SizedBox(width: 8),
                                Text('Thinking...'),
                              ],
                            ),
                          );
                        }
                        final message = messages[index];
                        return MessageBubble(
                          message: message.content,
                          isUser: message.isUser,
                          isError: message.isError,
                        );
                      },
                    ),
            ),
            ChatInput(onSend: _sendMessage),
          ],
        ),
      ),
    );
  }
}
