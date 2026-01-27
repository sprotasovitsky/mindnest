// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'api_keys_provider.dart';

// **************************************************************************
// RiverpodGenerator
// **************************************************************************

// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, type=warning

@ProviderFor(ApiKeys)
const apiKeysProvider = ApiKeysProvider._();

final class ApiKeysProvider extends $NotifierProvider<ApiKeys, ApiKeysState> {
  const ApiKeysProvider._()
    : super(
        from: null,
        argument: null,
        retry: null,
        name: r'apiKeysProvider',
        isAutoDispose: true,
        dependencies: null,
        $allTransitiveDependencies: null,
      );

  @override
  String debugGetCreateSourceHash() => _$apiKeysHash();

  @$internal
  @override
  ApiKeys create() => ApiKeys();

  /// {@macro riverpod.override_with_value}
  Override overrideWithValue(ApiKeysState value) {
    return $ProviderOverride(
      origin: this,
      providerOverride: $SyncValueProvider<ApiKeysState>(value),
    );
  }
}

String _$apiKeysHash() => r'7ae780d9f6e9157dee4f01af8aa9731e0d8e6ddc';

abstract class _$ApiKeys extends $Notifier<ApiKeysState> {
  ApiKeysState build();
  @$mustCallSuper
  @override
  void runBuild() {
    final created = build();
    final ref = this.ref as $Ref<ApiKeysState, ApiKeysState>;
    final element =
        ref.element
            as $ClassProviderElement<
              AnyNotifier<ApiKeysState, ApiKeysState>,
              ApiKeysState,
              Object?,
              Object?
            >;
    element.handleValue(ref, created);
  }
}
