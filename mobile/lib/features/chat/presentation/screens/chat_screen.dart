import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../widgets/message_bubble.dart';
import '../widgets/chat_input.dart';

class ChatMessage {
  final String content;
  final bool isUser;
  final DateTime timestamp;

  ChatMessage({
    required this.content,
    required this.isUser,
    DateTime? timestamp,
  }) : timestamp = timestamp ?? DateTime.now();
}

final messagesProvider = StateProvider<List<ChatMessage>>((ref) => [
      ChatMessage(
        content: 'Привет! Я MindNest — твой персональный помощник для управления знаниями и задачами. Чем могу помочь?',
        isUser: false,
      ),
    ]);

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

  void _sendMessage(String text) {
    if (text.trim().isEmpty) return;

    final messages = ref.read(messagesProvider.notifier);

    // Add user message
    messages.state = [
      ...messages.state,
      ChatMessage(content: text, isUser: true),
    ];
    _scrollToBottom();

    // TODO: Call API and add response
    // For now, add a placeholder response
    Future.delayed(const Duration(milliseconds: 500), () {
      messages.state = [
        ...messages.state,
        ChatMessage(
          content: 'Это placeholder ответ. Интеграция с backend будет добавлена позже.',
          isUser: false,
        ),
      ];
      _scrollToBottom();
    });
  }

  @override
  Widget build(BuildContext context) {
    final messages = ref.watch(messagesProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('MindNest'),
        actions: [
          IconButton(
            icon: const Icon(Icons.folder_outlined),
            onPressed: () {
              // TODO: Open project switcher
            },
            tooltip: 'Проекты',
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
                itemCount: messages.length,
                itemBuilder: (context, index) {
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
