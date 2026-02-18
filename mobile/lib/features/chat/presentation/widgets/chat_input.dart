import 'dart:async';
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

class _ChatInputState extends ConsumerState<ChatInput>
    with SingleTickerProviderStateMixin {
  final TextEditingController _controller = TextEditingController();
  final AudioRecorder _recorder = AudioRecorder();
  bool _hasText = false;
  bool _isRecording = false;
  bool _isTranscribing = false;
  bool _hasPermission = false;
  Duration _recordingDuration = Duration.zero;
  String? _audioPath;

  // Waveform state
  List<double> _amplitudes = [];
  StreamSubscription<Amplitude>? _amplitudeSubscription;
  late AnimationController _waveAnimationController;

  @override
  void initState() {
    super.initState();
    _controller.addListener(_onTextChanged);
    _checkPermission();
    _waveAnimationController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 100),
    );
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
        _amplitudes = [];
      });

      // Subscribe to amplitude changes for waveform
      _amplitudeSubscription = _recorder
          .onAmplitudeChanged(const Duration(milliseconds: 100))
          .listen((amp) {
        if (mounted && _isRecording) {
          setState(() {
            _amplitudes.add(amp.current);
            if (_amplitudes.length > 30) {
              _amplitudes.removeAt(0);
            }
          });
        }
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
      await _amplitudeSubscription?.cancel();
      _amplitudeSubscription = null;

      final path = await _recorder.stop();
      setState(() {
        _isRecording = false;
        _amplitudes = [];
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

  Future<void> _stopAndSendRecording() async {
    if (!_isRecording) return;

    try {
      await _amplitudeSubscription?.cancel();
      _amplitudeSubscription = null;

      final path = await _recorder.stop();
      setState(() {
        _isRecording = false;
        _amplitudes = [];
      });

      if (path == null || path.isEmpty) {
        if (kDebugMode) debugPrint('Recording path is null or empty');
        return;
      }

      final file = File(path);
      if (!await file.exists()) {
        if (kDebugMode) debugPrint('Recording file does not exist: $path');
        return;
      }

      if (kDebugMode) debugPrint('Recording stopped, transcribing and sending: $path');

      // Transcribe and send
      await _transcribeAndSendRecording(path);
    } catch (e) {
      if (kDebugMode) debugPrint('Failed to stop recording: $e');
      setState(() {
        _isRecording = false;
      });
    }
  }

  Future<void> _transcribeAndSendRecording(String audioPath) async {
    setState(() {
      _isTranscribing = true;
    });

    try {
      final result = await ref.read(whisperProvider.notifier).transcribe(audioPath);

      if (result != null && result.isNotEmpty && mounted) {
        // Send immediately
        widget.onSend(result);
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
    _amplitudeSubscription?.cancel();
    _waveAnimationController.dispose();
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
    final isModelReady =
        whisperState.modelStatus == WhisperModelStatus.downloaded;

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
          // Left button: + or Stop (when recording)
          _buildLeftButton(colorScheme),
          const SizedBox(width: 8),
          // Center: TextField or Waveform
          Expanded(
            child: _isRecording
                ? _buildWaveform(colorScheme)
                : _buildTextField(colorScheme),
          ),
          const SizedBox(width: 8),
          // Right button: Mic/Send/Loading
          _buildRightButton(colorScheme, isModelReady),
        ],
      ),
    );
  }

  Widget _buildLeftButton(ColorScheme colorScheme) {
    if (_isRecording) {
      // Stop button during recording - stops and transcribes (keeps text)
      return Semantics(
        label: 'Stop recording',
        button: true,
        child: IconButton(
          key: const Key('stop_recording_button'),
          onPressed: _stopRecording,
          tooltip: 'Stop',
          icon: const Icon(Icons.stop_rounded),
          style: IconButton.styleFrom(
            backgroundColor: colorScheme.errorContainer,
            foregroundColor: colorScheme.error,
          ),
        ),
      );
    }

    // Plus button (placeholder for future features)
    return Semantics(
      label: 'More options',
      button: true,
      child: IconButton(
        key: const Key('plus_button'),
        onPressed: _isTranscribing
            ? null
            : () {
                // Placeholder for future features (attachments, etc.)
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(
                    content: Text('Coming soon'),
                    duration: Duration(seconds: 1),
                  ),
                );
              },
        tooltip: 'More options',
        icon: const Icon(Icons.add_rounded),
        style: IconButton.styleFrom(
          backgroundColor: colorScheme.surfaceContainerHighest,
          foregroundColor: _isTranscribing
              ? colorScheme.outline.withValues(alpha: 0.5)
              : colorScheme.outline,
        ),
      ),
    );
  }

  Widget _buildTextField(ColorScheme colorScheme) {
    return TextField(
      key: const Key('chat_input_field'),
      controller: _controller,
      maxLines: 5,
      minLines: 1,
      enabled: !_isTranscribing,
      textInputAction: TextInputAction.newline,
      decoration: InputDecoration(
        hintText: _isTranscribing ? 'Transcribing...' : 'Type a message...',
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
        prefixIcon: _isTranscribing
            ? Padding(
                padding: const EdgeInsets.only(left: 12),
                child: SizedBox(
                  width: 20,
                  height: 20,
                  child: CircularProgressIndicator(
                    strokeWidth: 2,
                    color: colorScheme.primary,
                  ),
                ),
              )
            : null,
        prefixIconConstraints: const BoxConstraints(
          minWidth: 44,
          minHeight: 20,
        ),
      ),
      onSubmitted: (_) => _send(),
    );
  }

  Widget _buildWaveform(ColorScheme colorScheme) {
    const int barCount = 24;

    return Container(
      height: 48,
      decoration: BoxDecoration(
        color: colorScheme.surfaceContainerHighest,
        borderRadius: BorderRadius.circular(24),
      ),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 16),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.center,
          crossAxisAlignment: CrossAxisAlignment.center,
          children: [
            // Recording indicator dot
            Container(
              width: 8,
              height: 8,
              decoration: BoxDecoration(
                color: colorScheme.error,
                shape: BoxShape.circle,
              ),
            ),
            const SizedBox(width: 8),
            // Duration text
            Text(
              _formatDuration(_recordingDuration),
              style: TextStyle(
                color: colorScheme.onSurfaceVariant,
                fontSize: 14,
                fontWeight: FontWeight.w500,
              ),
            ),
            const SizedBox(width: 12),
            // Waveform bars
            Expanded(
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                crossAxisAlignment: CrossAxisAlignment.center,
                children: List.generate(barCount, (i) {
                  // Get amplitude value (reversed so most recent is on the right)
                  final reversedIndex = barCount - 1 - i;
                  final amplitude = reversedIndex < _amplitudes.length
                      ? _amplitudes[_amplitudes.length - 1 - reversedIndex]
                      : -50.0;

                  // Normalize amplitude: typically ranges from -50 (quiet) to 0 (loud)
                  // Map to height between 4 and 20 pixels
                  final normalizedAmplitude = ((amplitude + 50) / 50).clamp(0.0, 1.0);
                  final height = 4.0 + (normalizedAmplitude * 16.0);

                  return AnimatedContainer(
                    duration: const Duration(milliseconds: 100),
                    width: 3,
                    height: height,
                    decoration: BoxDecoration(
                      color: colorScheme.primary,
                      borderRadius: BorderRadius.circular(2),
                    ),
                  );
                }),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildRightButton(ColorScheme colorScheme, bool isModelReady) {
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

    // When recording, show send button (will stop, transcribe and send)
    if (_isRecording) {
      return Semantics(
        label: 'Send recording',
        button: true,
        child: IconButton.filled(
          key: const Key('send_recording_button'),
          onPressed: _stopAndSendRecording,
          tooltip: 'Send',
          icon: const Icon(Icons.send_rounded),
          style: IconButton.styleFrom(
            backgroundColor: colorScheme.primary,
            foregroundColor: colorScheme.onPrimary,
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
              content: Text(
                  'Download the speech model in Profile settings to use voice input'),
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
