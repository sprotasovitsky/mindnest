import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/api/api_client.dart';
import '../widgets/message_bubble.dart';
import '../widgets/chat_input.dart';

class ChatMessage {
  final String content;
  final bool isUser;
  final DateTime timestamp;
  final double? confidence;

  ChatMessage({
    required this.content,
    required this.isUser,
    DateTime? timestamp,
    this.confidence,
  }) : timestamp = timestamp ?? DateTime.now();
}

final messagesProvider = StateProvider<List<ChatMessage>>((ref) => [
      ChatMessage(
        content: 'Hi! I\'m MindNest — your personal assistant for knowledge and task management. How can I help?',
        isUser: false,
      ),
    ]);

final isLoadingProvider = StateProvider<bool>((ref) => false);

class ChatScreen extends ConsumerStatefulWidget {
  const ChatScreen({super.key});

  @override
  ConsumerState<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends ConsumerState<ChatScreen> {
  final ScrollController _scrollController = ScrollController();

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

    // Add user message
    messages.state = [
      ...messages.state,
      ChatMessage(content: text, isUser: true),
    ];
    _scrollToBottom();

    // Set loading state
    ref.read(isLoadingProvider.notifier).state = true;

    try {
      // Call backend API
      final response = await apiClient.chat(text);

      final reply = response['reply'] as String? ?? 'No response';
      final confidence = (response['confidence'] as num?)?.toDouble();

      messages.state = [
        ...messages.state,
        ChatMessage(
          content: reply,
          isUser: false,
          confidence: confidence,
        ),
      ];
    } catch (e) {
      messages.state = [
        ...messages.state,
        ChatMessage(
          content: 'Error: Could not connect to server. Please check if backend is running.',
          isUser: false,
        ),
      ];
    } finally {
      ref.read(isLoadingProvider.notifier).state = false;
      _scrollToBottom();
    }
  }

  @override
  Widget build(BuildContext context) {
    final messages = ref.watch(messagesProvider);
    final isLoading = ref.watch(isLoadingProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('MindNest'),
        actions: [
          IconButton(
            icon: const Icon(Icons.folder_outlined),
            onPressed: () {
              // TODO: Open project switcher
            },
            tooltip: 'Projects',
          ),
        ],
      ),
      body: SafeArea(
        child: Column(
          children: [
            Expanded(
              child: ListView.builder(
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
