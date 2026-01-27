import 'dart:io';

import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:path_provider/path_provider.dart';
import 'package:record/record.dart';

import '../../../../core/providers/whisper_provider.dart';

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
  final AudioRecorder _recorder = AudioRecorder();
  bool _hasText = false;
  bool _isRecording = false;
  bool _isTranscribing = false;
  bool _hasPermission = false;
  Duration _recordingDuration = Duration.zero;
  String? _audioPath;

  @override
  void initState() {
    super.initState();
    _controller.addListener(_onTextChanged);
    _checkPermission();
  }

  void _onTextChanged() {
    final hasText = _controller.text.trim().isNotEmpty;
    if (hasText != _hasText) {
      setState(() {
        _hasText = hasText;
      });
    }
  }

  Future<void> _checkPermission() async {
    try {
      _hasPermission = await _recorder.hasPermission();
      if (mounted) setState(() {});
    } catch (e) {
      if (kDebugMode) debugPrint('Failed to check recording permission: $e');
    }
  }

  Future<String> _getRecordingPath() async {
    final dir = await getTemporaryDirectory();
    final timestamp = DateTime.now().millisecondsSinceEpoch;
    return '${dir.path}/recording_$timestamp.wav';
  }

  Future<void> _startRecording() async {
    if (!_hasPermission) {
      _hasPermission = await _recorder.hasPermission();
      if (!_hasPermission) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Microphone permission required')),
          );
        }
        return;
      }
    }

    // Check if model is downloaded
    final whisperState = ref.read(whisperProvider);
    if (whisperState.modelStatus != WhisperModelStatus.downloaded) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Please download the speech model in Profile settings'),
            duration: Duration(seconds: 3),
          ),
        );
      }
      return;
    }

    try {
      _audioPath = await _getRecordingPath();

      // Configure for Whisper: 16kHz mono WAV
      await _recorder.start(
        const RecordConfig(
          encoder: AudioEncoder.wav,
          sampleRate: 16000,
          numChannels: 1,
        ),
        path: _audioPath!,
      );

      setState(() {
        _isRecording = true;
        _recordingDuration = Duration.zero;
      });

      // Update duration every second
      _updateRecordingDuration();

      if (kDebugMode) debugPrint('Started recording to: $_audioPath');
    } catch (e) {
      if (kDebugMode) debugPrint('Failed to start recording: $e');
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Failed to start recording: $e')),
        );
      }
    }
  }

  Future<void> _updateRecordingDuration() async {
    while (_isRecording && mounted) {
      await Future.delayed(const Duration(seconds: 1));
      if (_isRecording && mounted) {
        setState(() {
          _recordingDuration += const Duration(seconds: 1);
        });
      }
    }
  }

  Future<void> _stopRecording() async {
    if (!_isRecording) return;

    try {
      final path = await _recorder.stop();
      setState(() {
        _isRecording = false;
      });

      if (path == null || path.isEmpty) {
        if (kDebugMode) debugPrint('Recording path is null or empty');
        return;
      }

      // Verify file exists
      final file = File(path);
      if (!await file.exists()) {
        if (kDebugMode) debugPrint('Recording file does not exist: $path');
        return;
      }

      if (kDebugMode) debugPrint('Recording stopped: $path');

      // Transcribe
      await _transcribeRecording(path);
    } catch (e) {
      if (kDebugMode) debugPrint('Failed to stop recording: $e');
      setState(() {
        _isRecording = false;
      });
    }
  }

  Future<void> _cancelRecording() async {
    try {
      await _recorder.stop();
    } catch (e) {
      if (kDebugMode) debugPrint('Failed to cancel recording: $e');
    }

    // Delete the audio file
    if (_audioPath != null) {
      try {
        final file = File(_audioPath!);
        if (await file.exists()) {
          await file.delete();
        }
      } catch (e) {
        if (kDebugMode) debugPrint('Failed to delete audio file: $e');
      }
    }

    setState(() {
      _isRecording = false;
      _recordingDuration = Duration.zero;
      _audioPath = null;
    });
  }

  Future<void> _transcribeRecording(String audioPath) async {
    setState(() {
      _isTranscribing = true;
    });

    try {
      final result = await ref.read(whisperProvider.notifier).transcribe(audioPath);

      if (result != null && result.isNotEmpty && mounted) {
        setState(() {
          _controller.text = result;
          _controller.selection = TextSelection.fromPosition(
            TextPosition(offset: _controller.text.length),
          );
        });
      } else if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Could not transcribe audio')),
        );
      }
    } catch (e) {
      if (kDebugMode) debugPrint('Transcription error: $e');
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Transcription failed: $e')),
        );
      }
    } finally {
      // Clean up audio file
      try {
        final file = File(audioPath);
        if (await file.exists()) {
          await file.delete();
        }
      } catch (e) {
        if (kDebugMode) debugPrint('Failed to delete audio file: $e');
      }

      if (mounted) {
        setState(() {
          _isTranscribing = false;
        });
        ref.read(whisperProvider.notifier).resetTranscriptionStatus();
      }
    }
  }

  @override
  void dispose() {
    _controller.dispose();
    _recorder.dispose();
    super.dispose();
  }

  void _send() {
    final text = _controller.text.trim();
    if (text.isNotEmpty) {
      widget.onSend(text);
      _controller.clear();
    }
  }

  String _formatDuration(Duration duration) {
    final minutes = duration.inMinutes.remainder(60).toString().padLeft(2, '0');
    final seconds = duration.inSeconds.remainder(60).toString().padLeft(2, '0');
    return '$minutes:$seconds';
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final colorScheme = theme.colorScheme;
    final whisperState = ref.watch(whisperProvider);
    final isModelReady = whisperState.modelStatus == WhisperModelStatus.downloaded;

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
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          // Recording indicator
          if (_isRecording)
            Padding(
              padding: const EdgeInsets.only(bottom: 8),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Container(
                    width: 8,
                    height: 8,
                    decoration: BoxDecoration(
                      color: colorScheme.error,
                      shape: BoxShape.circle,
                    ),
                  ),
                  const SizedBox(width: 8),
                  Text(
                    'Recording ${_formatDuration(_recordingDuration)}',
                    style: theme.textTheme.bodySmall?.copyWith(
                      color: colorScheme.error,
                    ),
                  ),
                  const SizedBox(width: 16),
                  TextButton(
                    onPressed: _cancelRecording,
                    style: TextButton.styleFrom(
                      foregroundColor: colorScheme.error,
                      padding: const EdgeInsets.symmetric(horizontal: 8),
                      minimumSize: const Size(0, 32),
                    ),
                    child: const Text('Cancel'),
                  ),
                ],
              ),
            ),
          // Transcribing indicator
          if (_isTranscribing)
            Padding(
              padding: const EdgeInsets.only(bottom: 8),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  SizedBox(
                    width: 16,
                    height: 16,
                    child: CircularProgressIndicator(
                      strokeWidth: 2,
                      color: colorScheme.primary,
                    ),
                  ),
                  const SizedBox(width: 8),
                  Text(
                    'Transcribing...',
                    style: theme.textTheme.bodySmall?.copyWith(
                      color: colorScheme.primary,
                    ),
                  ),
                ],
              ),
            ),
          Row(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Expanded(
                child: TextField(
                  key: const Key('chat_input_field'),
                  controller: _controller,
                  maxLines: 5,
                  minLines: 1,
                  enabled: !_isRecording && !_isTranscribing,
                  textInputAction: TextInputAction.newline,
                  decoration: InputDecoration(
                    hintText: _isRecording
                        ? 'Recording...'
                        : _isTranscribing
                            ? 'Transcribing...'
                            : 'Type a message...',
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
              _buildActionButton(colorScheme, isModelReady),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildActionButton(ColorScheme colorScheme, bool isModelReady) {
    // When recording, show stop button
    if (_isRecording) {
      return Semantics(
        label: 'Stop recording',
        button: true,
        child: IconButton.filled(
          key: const Key('stop_recording_button'),
          onPressed: _stopRecording,
          tooltip: 'Stop',
          icon: const Icon(Icons.stop_rounded),
          style: IconButton.styleFrom(
            backgroundColor: colorScheme.error,
            foregroundColor: colorScheme.onError,
          ),
        ),
      );
    }

    // When transcribing, show loading indicator
    if (_isTranscribing) {
      return Semantics(
        label: 'Transcribing',
        button: true,
        child: Container(
          width: 48,
          height: 48,
          decoration: BoxDecoration(
            color: colorScheme.surfaceContainerHighest,
            shape: BoxShape.circle,
          ),
          child: Center(
            child: SizedBox(
              width: 24,
              height: 24,
              child: CircularProgressIndicator(
                strokeWidth: 2,
                color: colorScheme.primary,
              ),
            ),
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

    // When no text and model ready, show mic button
    if (isModelReady) {
      return Semantics(
        label: 'Voice input',
        button: true,
        child: IconButton.filled(
          key: const Key('voice_input_button'),
          onPressed: _startRecording,
          tooltip: 'Voice input',
          icon: const Icon(Icons.mic_rounded),
          style: IconButton.styleFrom(
            backgroundColor: colorScheme.surfaceContainerHighest,
            foregroundColor: colorScheme.outline,
          ),
        ),
      );
    }

    // When no text and model not ready, show disabled mic button with hint
    return Semantics(
      label: 'Voice input (download model first)',
      button: true,
      child: IconButton.filled(
        key: const Key('voice_input_button_disabled'),
        onPressed: () {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text('Download the speech model in Profile settings to use voice input'),
              duration: Duration(seconds: 3),
            ),
          );
        },
        tooltip: 'Download model to enable',
        icon: const Icon(Icons.mic_off_rounded),
        style: IconButton.styleFrom(
          backgroundColor: colorScheme.surfaceContainerHighest,
          foregroundColor: colorScheme.outline.withValues(alpha: 0.5),
        ),
      ),
    );
  }
}
