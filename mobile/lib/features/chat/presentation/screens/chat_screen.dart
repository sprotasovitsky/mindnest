import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/api/api_client.dart';
import '../../../../core/auth/auth_state.dart';
import '../../../../core/projects/project_state.dart';
import '../widgets/message_bubble.dart';
import '../widgets/chat_input.dart';

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

  @override
  void initState() {
    super.initState();
    // Load projects when chat screen initializes
    Future.microtask(() {
      ref.read(projectProvider.notifier).loadProjects();
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

      messages.state = [
        ...messages.state,
        ChatMessage(
          content: reply,
          isUser: false,
          confidence: confidence,
        ),
      ];
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

  void _showProjectSwitcher(BuildContext context) {
    showModalBottomSheet(
      context: context,
      builder: (context) => const ProjectSwitcherSheet(),
    );
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
              _showProjectSwitcher(context);
            },
            tooltip: 'Projects',
          ),
          IconButton(
            icon: const Icon(Icons.logout),
            onPressed: () {
              ref.read(authProvider.notifier).logout();
            },
            tooltip: 'Logout',
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

class ProjectSwitcherSheet extends ConsumerStatefulWidget {
  const ProjectSwitcherSheet({super.key});

  @override
  ConsumerState<ProjectSwitcherSheet> createState() => _ProjectSwitcherSheetState();
}

class _ProjectSwitcherSheetState extends ConsumerState<ProjectSwitcherSheet> {
  final _nameController = TextEditingController();
  bool _isCreating = false;

  @override
  void dispose() {
    _nameController.dispose();
    super.dispose();
  }

  Future<void> _createProject() async {
    if (_nameController.text.trim().isEmpty) return;

    setState(() => _isCreating = true);
    final project = await ref.read(projectProvider.notifier).createProject(
          _nameController.text.trim(),
          null,
        );
    setState(() => _isCreating = false);

    if (project != null && mounted) {
      _nameController.clear();
      Navigator.pop(context);
    }
  }

  @override
  Widget build(BuildContext context) {
    final projectState = ref.watch(projectProvider);

    return DraggableScrollableSheet(
      initialChildSize: 0.5,
      minChildSize: 0.3,
      maxChildSize: 0.9,
      expand: false,
      builder: (context, scrollController) {
        return Container(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Center(
                child: Container(
                  width: 40,
                  height: 4,
                  decoration: BoxDecoration(
                    color: Colors.grey[300],
                    borderRadius: BorderRadius.circular(2),
                  ),
                ),
              ),
              const SizedBox(height: 16),
              Text(
                'Projects',
                style: Theme.of(context).textTheme.titleLarge,
              ),
              const SizedBox(height: 16),

              // Create new project
              Row(
                children: [
                  Expanded(
                    child: TextField(
                      controller: _nameController,
                      decoration: const InputDecoration(
                        hintText: 'New project name',
                        border: OutlineInputBorder(),
                        contentPadding: EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                      ),
                      onSubmitted: (_) => _createProject(),
                    ),
                  ),
                  const SizedBox(width: 8),
                  IconButton.filled(
                    onPressed: _isCreating ? null : _createProject,
                    icon: _isCreating
                        ? const SizedBox(
                            width: 20,
                            height: 20,
                            child: CircularProgressIndicator(strokeWidth: 2),
                          )
                        : const Icon(Icons.add),
                  ),
                ],
              ),
              const SizedBox(height: 16),

              // Project list
              Expanded(
                child: projectState.isLoading
                    ? const Center(child: CircularProgressIndicator())
                    : projectState.projects.isEmpty
                        ? const Center(
                            child: Text('No projects yet. Create your first project above.'),
                          )
                        : ListView.builder(
                            controller: scrollController,
                            itemCount: projectState.projects.length,
                            itemBuilder: (context, index) {
                              final project = projectState.projects[index];
                              final isSelected = project.id == projectState.currentProject?.id;

                              return ListTile(
                                leading: Icon(
                                  isSelected ? Icons.folder : Icons.folder_outlined,
                                  color: isSelected
                                      ? Theme.of(context).colorScheme.primary
                                      : null,
                                ),
                                title: Text(
                                  project.name,
                                  style: TextStyle(
                                    fontWeight: isSelected ? FontWeight.bold : null,
                                  ),
                                ),
                                subtitle: project.description != null
                                    ? Text(
                                        project.description!,
                                        maxLines: 1,
                                        overflow: TextOverflow.ellipsis,
                                      )
                                    : null,
                                trailing: isSelected
                                    ? Icon(
                                        Icons.check_circle,
                                        color: Theme.of(context).colorScheme.primary,
                                      )
                                    : null,
                                onTap: () {
                                  ref.read(projectProvider.notifier).selectProject(project);
                                  Navigator.pop(context);
                                },
                              );
                            },
                          ),
              ),
            ],
          ),
        );
      },
    );
  }
}
