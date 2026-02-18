import 'dart:io';

import 'package:flutter/foundation.dart';
import 'package:whisper_ggml/whisper_ggml.dart';

/// Singleton service for Whisper speech recognition.
/// Handles model download, management, and transcription.
class WhisperService {
  WhisperService._();

  static final WhisperService _instance = WhisperService._();
  static WhisperService get instance => _instance;

  final WhisperController _controller = WhisperController();
  bool _isModelReady = false;

  /// The Whisper model to use. Base model (~142MB) for better accuracy.
  static const WhisperModel _model = WhisperModel.base;

  /// Model size in bytes (approximate).
  static const int modelSizeBytes = 142 * 1024 * 1024; // ~142MB

  /// Check if the Whisper model is downloaded.
  Future<bool> isModelDownloaded() async {
    try {
      final path = await _controller.getPath(_model);
      return File(path).existsSync();
    } catch (e) {
      if (kDebugMode) debugPrint('Error checking model: $e');
      return false;
    }
  }

  /// Download the Whisper model.
  /// Note: whisper_ggml doesn't support progress callback.
  /// Returns true if download was successful.
  Future<bool> downloadModel({
    void Function(double progress)? onProgress,
  }) async {
    try {
      if (kDebugMode) debugPrint('Starting model download...');

      // Notify start
      onProgress?.call(0.0);

      // whisper_ggml downloads the model
      final path = await _controller.downloadModel(_model);

      // Notify complete
      onProgress?.call(1.0);

      if (File(path).existsSync()) {
        _isModelReady = true;
        if (kDebugMode) debugPrint('Whisper model downloaded to: $path');
        return true;
      }

      return false;
    } catch (e) {
      if (kDebugMode) debugPrint('Failed to download Whisper model: $e');
      return false;
    }
  }

  /// Delete the downloaded model to free up space.
  Future<bool> deleteModel() async {
    try {
      final path = await _controller.getPath(_model);
      final file = File(path);
      if (await file.exists()) {
        await file.delete();
        _isModelReady = false;
        if (kDebugMode) debugPrint('Whisper model deleted');
      }
      return true;
    } catch (e) {
      if (kDebugMode) debugPrint('Failed to delete Whisper model: $e');
      return false;
    }
  }

  /// Get the size of the downloaded model in bytes.
  Future<int?> getModelSize() async {
    try {
      final path = await _controller.getPath(_model);
      final file = File(path);
      if (await file.exists()) {
        return await file.length();
      }
      return null;
    } catch (e) {
      return null;
    }
  }

  /// Initialize the Whisper model.
  Future<bool> initialize() async {
    if (_isModelReady) return true;

    try {
      final isDownloaded = await isModelDownloaded();
      if (isDownloaded) {
        _isModelReady = true;
        if (kDebugMode) debugPrint('Whisper initialized successfully');
        return true;
      }
      return false;
    } catch (e) {
      if (kDebugMode) debugPrint('Failed to initialize Whisper: $e');
      return false;
    }
  }

  /// Transcribe an audio file to text.
  /// The audio file should be in WAV format (16kHz, mono).
  /// Returns the transcribed text or null if transcription fails.
  Future<String?> transcribe(String audioPath) async {
    if (!_isModelReady) {
      final initialized = await initialize();
      if (!initialized) {
        if (kDebugMode) debugPrint('Cannot transcribe: Whisper not initialized');
        return null;
      }
    }

    try {
      if (kDebugMode) debugPrint('Starting transcription of: $audioPath');

      final result = await _controller.transcribe(
        model: _model,
        audioPath: audioPath,
        lang: 'auto', // Auto-detect language
      );

      if (result == null) {
        if (kDebugMode) debugPrint('Transcription returned null');
        return null;
      }

      final text = result.transcription.text.trim();
      if (kDebugMode) debugPrint('Transcription result: $text');
      return text.isNotEmpty ? text : null;
    } catch (e, stack) {
      if (kDebugMode) {
        debugPrint('Transcription failed: $e');
        debugPrint('Stack: $stack');
      }
      return null;
    }
  }

  /// Close and release resources.
  Future<void> close() async {
    _isModelReady = false;
  }
}
