import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:speech_to_text/speech_recognition_result.dart';
import 'package:speech_to_text/speech_to_text.dart';

import '../../../../core/providers/settings_provider.dart';

class ChatInput extends ConsumerStatefulWidget {
  final void Function(String) onSend;

  const ChatInput({
    super.key,
    required this.onSend,
  });

  @override
  ConsumerState<ChatInput> createState() => _ChatInputState();
}

class _ChatInputState extends ConsumerState<ChatInput> {
  final TextEditingController _controller = TextEditingController();
  final SpeechToText _speech = SpeechToText();
  bool _hasText = false;
  bool _isListening = false;
  bool _speechAvailable = false;

  @override
  void initState() {
    super.initState();
    _controller.addListener(_onTextChanged);
    _initSpeech();
  }

  void _onTextChanged() {
    final hasText = _controller.text.trim().isNotEmpty;
    if (hasText != _hasText) {
      setState(() {
        _hasText = hasText;
      });
    }
  }

  Future<void> _initSpeech() async {
    try {
      _speechAvailable = await _speech.initialize(
        onStatus: (status) {
          if (mounted) {
            setState(() {
              _isListening = status == 'listening';
            });
          }
        },
        onError: (error) {
          if (kDebugMode) debugPrint('Speech error: ${error.errorMsg}');
          if (mounted) {
            setState(() {
              _isListening = false;
            });
          }
        },
      );
      if (mounted) {
        setState(() {});
      }
      if (kDebugMode) debugPrint('Speech available: $_speechAvailable');
    } catch (e) {
      if (kDebugMode) debugPrint('Failed to initialize speech: $e');
    }
  }

  void _onSpeechResult(SpeechRecognitionResult result) {
    if (mounted) {
      setState(() {
        _controller.text = result.recognizedWords;
        _controller.selection = TextSelection.fromPosition(
          TextPosition(offset: _controller.text.length),
        );
      });
    }
  }

  Future<void> _toggleListening() async {
    if (_isListening) {
      await _speech.stop();
      setState(() {
        _isListening = false;
      });
    } else {
      final settings = ref.read(settingsProvider);
      final localeId = settings.speechLanguage;

      if (kDebugMode) {
        debugPrint('Starting speech recognition with locale: $localeId');
      }

      setState(() {
        _isListening = true;
      });

      await _speech.listen(
        onResult: _onSpeechResult,
        listenFor: const Duration(seconds: 30),
        pauseFor: const Duration(seconds: 3),
        listenOptions: SpeechListenOptions(
          partialResults: true,
          listenMode: ListenMode.dictation,
        ),
        localeId: localeId,
      );
    }
  }

  @override
  void dispose() {
    _controller.dispose();
    _speech.stop();
    super.dispose();
  }

  void _send() {
    final text = _controller.text.trim();
    if (text.isNotEmpty) {
      widget.onSend(text);
      _controller.clear();
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final colorScheme = theme.colorScheme;

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: colorScheme.surface,
        border: Border(
          top: BorderSide(
            color: colorScheme.outlineVariant,
          ),
        ),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.end,
        children: [
          Expanded(
            child: TextField(
              key: const Key('chat_input_field'),
              controller: _controller,
              maxLines: 5,
              minLines: 1,
              textInputAction: TextInputAction.newline,
              decoration: InputDecoration(
                hintText: _isListening ? 'Listening...' : 'Type a message...',
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(24),
                  borderSide: BorderSide.none,
                ),
                filled: true,
                fillColor: colorScheme.surfaceContainerHighest,
                contentPadding: const EdgeInsets.symmetric(
                  horizontal: 20,
                  vertical: 12,
                ),
              ),
              onSubmitted: (_) => _send(),
            ),
          ),
          const SizedBox(width: 8),
          _buildActionButton(colorScheme),
        ],
      ),
    );
  }

  Widget _buildActionButton(ColorScheme colorScheme) {
    // When listening, show stop button
    if (_isListening) {
      return Semantics(
        label: 'Stop listening',
        button: true,
        child: IconButton.filled(
          key: const Key('stop_listening_button'),
          onPressed: _toggleListening,
          tooltip: 'Stop',
          icon: const Icon(Icons.stop_rounded),
          style: IconButton.styleFrom(
            backgroundColor: colorScheme.error,
            foregroundColor: colorScheme.onError,
          ),
        ),
      );
    }

    // When there's text, show send button
    if (_hasText) {
      return Semantics(
        label: 'Send message',
        button: true,
        child: IconButton.filled(
          key: const Key('send_button'),
          onPressed: _send,
          tooltip: 'Send',
          icon: const Icon(Icons.send_rounded),
          style: IconButton.styleFrom(
            backgroundColor: colorScheme.primary,
            foregroundColor: colorScheme.onPrimary,
          ),
        ),
      );
    }

    // When no text and speech available, show mic button
    if (_speechAvailable) {
      return Semantics(
        label: 'Voice input',
        button: true,
        child: IconButton.filled(
          key: const Key('voice_input_button'),
          onPressed: _toggleListening,
          tooltip: 'Voice input',
          icon: const Icon(Icons.mic_rounded),
          style: IconButton.styleFrom(
            backgroundColor: colorScheme.surfaceContainerHighest,
            foregroundColor: colorScheme.outline,
          ),
        ),
      );
    }

    // When no text and speech not available, show disabled send button
    return Semantics(
      label: 'Send message',
      button: true,
      child: IconButton.filled(
        key: const Key('send_button'),
        onPressed: null,
        tooltip: 'Send',
        icon: const Icon(Icons.send_rounded),
        style: IconButton.styleFrom(
          backgroundColor: colorScheme.surfaceContainerHighest,
          foregroundColor: colorScheme.outline,
        ),
      ),
    );
  }
}
