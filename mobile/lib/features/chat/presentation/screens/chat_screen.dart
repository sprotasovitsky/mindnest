import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/providers/chat_provider.dart';
import '../../../../core/providers/project_provider.dart';
import '../../../../shared/widgets/widgets.dart';
import '../widgets/message_bubble.dart';
import '../widgets/chat_input.dart';
import '../../../projects/presentation/widgets/project_settings_sheet.dart';

class ChatScreen extends ConsumerStatefulWidget {
  const ChatScreen({super.key});

  @override
  ConsumerState<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends ConsumerState<ChatScreen> {
  final ScrollController _scrollController = ScrollController();

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _initializeChat();
      // Listen for message changes and scroll to bottom
      ref.listenManual(chatProvider, (previous, next) {
        if (previous?.messages.length != next.messages.length) {
          _scrollToBottom();
        }
      });
    });
  }

  Future<void> _initializeChat() async {
    final projectState = ref.read(projectsProvider);
    final project = projectState.currentProject;
    if (project != null) {
      await ref.read(chatProvider.notifier).initializeForProject(project.id);
      _scrollToBottom();
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
    await ref.read(chatProvider.notifier).sendMessage(text);
    // Scroll is handled by listener in initState
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
    final chatState = ref.watch(chatProvider);
    final projectState = ref.watch(projectsProvider);
    final project = projectState.currentProject;
    final canAddMembers = project != null && !project.needsOnboarding;

    // Check if project changed and reinitialize
    if (project != null && chatState.lastProjectId != project.id) {
      WidgetsBinding.instance.addPostFrameCallback((_) {
        _initializeChat();
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
              child: chatState.isLoadingHistory
                  ? const LoadingOverlay(message: 'Loading chat history...')
                  : ListView.builder(
                      controller: _scrollController,
                      padding: const EdgeInsets.all(16),
                      itemCount: chatState.messages.length +
                          (chatState.isLoading ? 1 : 0),
                      itemBuilder: (context, index) {
                        if (index == chatState.messages.length &&
                            chatState.isLoading) {
                          return const LoadingIndicator(message: 'Thinking...');
                        }
                        final message = chatState.messages[index];
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
