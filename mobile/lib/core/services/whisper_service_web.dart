/// Web stub for WhisperService. dart:ffi is not available on Web.
class WhisperService {
  WhisperService._();

  static final WhisperService _instance = WhisperService._();
  static WhisperService get instance => _instance;

  static const int modelSizeBytes = 0;

  Future<bool> isModelDownloaded() async => false;

  Future<bool> downloadModel({void Function(double progress)? onProgress}) async => false;

  Future<bool> deleteModel() async => false;

  Future<int?> getModelSize() async => null;

  Future<bool> initialize() async => false;

  Future<String?> transcribe(String audioPath) async => null;

  Future<void> close() async {}
}
