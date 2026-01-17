// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'members_repository.dart';

// **************************************************************************
// RiverpodGenerator
// **************************************************************************

// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, type=warning

@ProviderFor(membersRepository)
const membersRepositoryProvider = MembersRepositoryProvider._();

final class MembersRepositoryProvider
    extends
        $FunctionalProvider<
          MembersRepository,
          MembersRepository,
          MembersRepository
        >
    with $Provider<MembersRepository> {
  const MembersRepositoryProvider._()
    : super(
        from: null,
        argument: null,
        retry: null,
        name: r'membersRepositoryProvider',
        isAutoDispose: true,
        dependencies: null,
        $allTransitiveDependencies: null,
      );

  @override
  String debugGetCreateSourceHash() => _$membersRepositoryHash();

  @$internal
  @override
  $ProviderElement<MembersRepository> $createElement(
    $ProviderPointer pointer,
  ) => $ProviderElement(pointer);

  @override
  MembersRepository create(Ref ref) {
    return membersRepository(ref);
  }

  /// {@macro riverpod.override_with_value}
  Override overrideWithValue(MembersRepository value) {
    return $ProviderOverride(
      origin: this,
      providerOverride: $SyncValueProvider<MembersRepository>(value),
    );
  }
}

String _$membersRepositoryHash() => r'e95d5f606f871ff1b6aee0f98a7bdbd0faa40c43';
