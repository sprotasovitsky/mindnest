import 'package:freezed_annotation/freezed_annotation.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

part 'settings_provider.freezed.dart';
part 'settings_provider.g.dart';

@freezed
sealed class SettingsState with _$SettingsState {
  const factory SettingsState() = _SettingsState;
}

@Riverpod(keepAlive: true)
class Settings extends _$Settings {
  @override
  SettingsState build() {
    return const SettingsState();
  }
}
