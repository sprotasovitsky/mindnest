// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'members_provider.dart';

// **************************************************************************
// RiverpodGenerator
// **************************************************************************

// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, type=warning

@ProviderFor(Members)
const membersProvider = MembersProvider._();

final class MembersProvider extends $NotifierProvider<Members, MembersState> {
  const MembersProvider._()
    : super(
        from: null,
        argument: null,
        retry: null,
        name: r'membersProvider',
        isAutoDispose: true,
        dependencies: null,
        $allTransitiveDependencies: null,
      );

  @override
  String debugGetCreateSourceHash() => _$membersHash();

  @$internal
  @override
  Members create() => Members();

  /// {@macro riverpod.override_with_value}
  Override overrideWithValue(MembersState value) {
    return $ProviderOverride(
      origin: this,
      providerOverride: $SyncValueProvider<MembersState>(value),
    );
  }
}

String _$membersHash() => r'c07db1e10de2dcf3109c3555ad8e4e6c82d1f68c';

abstract class _$Members extends $Notifier<MembersState> {
  MembersState build();
  @$mustCallSuper
  @override
  void runBuild() {
    final created = build();
    final ref = this.ref as $Ref<MembersState, MembersState>;
    final element =
        ref.element
            as $ClassProviderElement<
              AnyNotifier<MembersState, MembersState>,
              MembersState,
              Object?,
              Object?
            >;
    element.handleValue(ref, created);
  }
}
