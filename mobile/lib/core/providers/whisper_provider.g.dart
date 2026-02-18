// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'whisper_provider.dart';

// **************************************************************************
// RiverpodGenerator
// **************************************************************************

// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, type=warning

@ProviderFor(Whisper)
const whisperProvider = WhisperProvider._();

final class WhisperProvider extends $NotifierProvider<Whisper, WhisperState> {
  const WhisperProvider._()
    : super(
        from: null,
        argument: null,
        retry: null,
        name: r'whisperProvider',
        isAutoDispose: false,
        dependencies: null,
        $allTransitiveDependencies: null,
      );

  @override
  String debugGetCreateSourceHash() => _$whisperHash();

  @$internal
  @override
  Whisper create() => Whisper();

  /// {@macro riverpod.override_with_value}
  Override overrideWithValue(WhisperState value) {
    return $ProviderOverride(
      origin: this,
      providerOverride: $SyncValueProvider<WhisperState>(value),
    );
  }
}

String _$whisperHash() => r'3018d7926bc554e679fbecc22e0f78d5dde46acd';

abstract class _$Whisper extends $Notifier<WhisperState> {
  WhisperState build();
  @$mustCallSuper
  @override
  void runBuild() {
    final created = build();
    final ref = this.ref as $Ref<WhisperState, WhisperState>;
    final element =
        ref.element
            as $ClassProviderElement<
              AnyNotifier<WhisperState, WhisperState>,
              WhisperState,
              Object?,
              Object?
            >;
    element.handleValue(ref, created);
  }
}
