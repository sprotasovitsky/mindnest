// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'api_keys_repository.dart';

// **************************************************************************
// RiverpodGenerator
// **************************************************************************

// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, type=warning

@ProviderFor(apiKeysRepository)
const apiKeysRepositoryProvider = ApiKeysRepositoryProvider._();

final class ApiKeysRepositoryProvider
    extends
        $FunctionalProvider<
          ApiKeysRepository,
          ApiKeysRepository,
          ApiKeysRepository
        >
    with $Provider<ApiKeysRepository> {
  const ApiKeysRepositoryProvider._()
    : super(
        from: null,
        argument: null,
        retry: null,
        name: r'apiKeysRepositoryProvider',
        isAutoDispose: true,
        dependencies: null,
        $allTransitiveDependencies: null,
      );

  @override
  String debugGetCreateSourceHash() => _$apiKeysRepositoryHash();

  @$internal
  @override
  $ProviderElement<ApiKeysRepository> $createElement(
    $ProviderPointer pointer,
  ) => $ProviderElement(pointer);

  @override
  ApiKeysRepository create(Ref ref) {
    return apiKeysRepository(ref);
  }

  /// {@macro riverpod.override_with_value}
  Override overrideWithValue(ApiKeysRepository value) {
    return $ProviderOverride(
      origin: this,
      providerOverride: $SyncValueProvider<ApiKeysRepository>(value),
    );
  }
}

String _$apiKeysRepositoryHash() => r'e2eeab3b3a0f24f1ba95bf82980a6c558b916746';
