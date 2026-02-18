import 'package:freezed_annotation/freezed_annotation.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../services/whisper_service.dart';

part 'whisper_provider.freezed.dart';
part 'whisper_provider.g.dart';

enum WhisperModelStatus {
  unknown,
  notDownloaded,
  downloading,
  downloaded,
  error,
}

enum TranscriptionStatus {
  idle,
  transcribing,
  completed,
  error,
}

@freezed
sealed class WhisperState with _$WhisperState {
  const factory WhisperState({
    @Default(WhisperModelStatus.unknown) WhisperModelStatus modelStatus,
    @Default(0.0) double downloadProgress,
    @Default(TranscriptionStatus.idle) TranscriptionStatus transcriptionStatus,
    String? errorMessage,
    int? modelSizeBytes,
  }) = _WhisperState;
}

@Riverpod(keepAlive: true)
class Whisper extends _$Whisper {
  @override
  WhisperState build() {
    _checkModelStatus();
    return const WhisperState();
  }

  Future<void> _checkModelStatus() async {
    final service = WhisperService.instance;
    final isDownloaded = await service.isModelDownloaded();
    final modelSize = await service.getModelSize();

    state = state.copyWith(
      modelStatus:
          isDownloaded ? WhisperModelStatus.downloaded : WhisperModelStatus.notDownloaded,
      modelSizeBytes: modelSize,
    );
  }

  Future<bool> downloadModel() async {
    state = state.copyWith(
      modelStatus: WhisperModelStatus.downloading,
      downloadProgress: 0.0,
      errorMessage: null,
    );

    final service = WhisperService.instance;
    final success = await service.downloadModel(
      onProgress: (progress) {
        state = state.copyWith(downloadProgress: progress);
      },
    );

    if (success) {
      final modelSize = await service.getModelSize();
      state = state.copyWith(
        modelStatus: WhisperModelStatus.downloaded,
        downloadProgress: 1.0,
        modelSizeBytes: modelSize,
      );
    } else {
      state = state.copyWith(
        modelStatus: WhisperModelStatus.error,
        errorMessage: 'Failed to download model',
      );
    }

    return success;
  }

  Future<bool> deleteModel() async {
    final service = WhisperService.instance;
    final success = await service.deleteModel();

    if (success) {
      state = state.copyWith(
        modelStatus: WhisperModelStatus.notDownloaded,
        downloadProgress: 0.0,
        modelSizeBytes: null,
      );
    }

    return success;
  }

  Future<String?> transcribe(String audioPath) async {
    state = state.copyWith(
      transcriptionStatus: TranscriptionStatus.transcribing,
      errorMessage: null,
    );

    final service = WhisperService.instance;
    final result = await service.transcribe(audioPath);

    if (result != null) {
      state = state.copyWith(transcriptionStatus: TranscriptionStatus.completed);
    } else {
      state = state.copyWith(
        transcriptionStatus: TranscriptionStatus.error,
        errorMessage: 'Transcription failed',
      );
    }

    return result;
  }

  void resetTranscriptionStatus() {
    state = state.copyWith(
      transcriptionStatus: TranscriptionStatus.idle,
      errorMessage: null,
    );
  }
}
