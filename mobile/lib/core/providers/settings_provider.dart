import 'package:freezed_annotation/freezed_annotation.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';
import 'package:shared_preferences/shared_preferences.dart';

part 'settings_provider.freezed.dart';
part 'settings_provider.g.dart';

@freezed
sealed class SettingsState with _$SettingsState {
  const factory SettingsState({
    String? speechLanguage, // null = auto (system locale)
  }) = _SettingsState;
}

@Riverpod(keepAlive: true)
class Settings extends _$Settings {
  static const _speechLanguageKey = 'speech_language';

  @override
  SettingsState build() {
    _loadSettings();
    return const SettingsState();
  }

  Future<void> _loadSettings() async {
    final prefs = await SharedPreferences.getInstance();
    final lang = prefs.getString(_speechLanguageKey);
    state = state.copyWith(speechLanguage: lang);
  }

  Future<void> setSpeechLanguage(String? localeId) async {
    final prefs = await SharedPreferences.getInstance();
    if (localeId != null) {
      await prefs.setString(_speechLanguageKey, localeId);
    } else {
      await prefs.remove(_speechLanguageKey);
    }
    state = state.copyWith(speechLanguage: localeId);
  }
}
