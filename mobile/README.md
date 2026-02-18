# MindNest Mobile

Flutter app for MindNest — AI-first knowledge and task management through a chat interface. Targets iOS, Android, and Web from a single codebase.

## Tech Stack

- **Framework**: Flutter (iOS, Android, Web)
- **State Management**: Riverpod with code generation (`@riverpod`)
- **Routing**: go_router
- **HTTP Client**: Dio (with auto token refresh on 401)
- **Storage**: flutter_secure_storage (tokens), shared_preferences (settings)

## Setup

```bash
cd mobile

# First-time setup (flutter pub get + XcodeGen + pod install)
make setup

# Regenerate Xcode project if needed
make regen

# Generate code after modifying @freezed, @riverpod, @JsonSerializable
dart run build_runner build
```

**Note:** `.xcodeproj`, `.xcworkspace`, and `Pods/` are gitignored. Always run `make setup` after cloning.

## Running

```bash
make run-dev        # Local backend (http://localhost:8000/api)
make run-staging    # Staging backend (https://dev-api.mindnest.one/api)
make run-prod       # Production backend (https://api.mindnest.one/api)
```

### Running Flutter manually (requires --dart-define)

```bash
# REQUIRED: always pass --dart-define when not using Makefile
# Without it, defaults point to Android emulator localhost — won't work on real devices
flutter run --flavor staging --release -d <device_id> \
  --dart-define=ENVIRONMENT=staging \
  --dart-define=API_URL=https://dev-api.mindnest.one/api
```

## Building

```bash
# iOS
make build-dev-ios
make build-staging-ios
make build-prod-ios

# Android APK
make build-dev-apk
make build-staging-apk
make build-prod-apk     # Signed release

# Android AAB (Play Store)
make build-staging-aab
make build-prod-aab     # Signed release
```

## Architecture

Clean Architecture with Repository pattern:

```
Presentation (features/*/presentation/)
│  - Screens: ConsumerWidget / ConsumerStatefulWidget
│  - Uses: ref.watch(provider), ref.read(provider.notifier)
│
├─► State (core/providers/)
│     - @riverpod Notifier classes
│     - @freezed State with copyWith
│     - loading / error / data states
│
├─► Repository (core/repositories/)
│     - Abstract interface + *RepositoryImpl
│     - Maps API responses to domain models
│
└─► Data (core/api/, core/models/)
      - ApiClient (Dio, auto-refreshes token on 401)
      - @freezed models with @JsonSerializable
      - AuthService (token storage)
```

### Code Generation

Run after modifying `@freezed`, `@riverpod`, or `@JsonSerializable` annotated classes:

```bash
dart run build_runner build   # One-time
dart run build_runner watch   # Watch mode during development
```

Generated files: `*.freezed.dart`, `*.g.dart`

## Project Structure

```
lib/
├── main.dart
├── core/
│   ├── api/              # HTTP client (ApiClient — Dio-based)
│   ├── auth/             # Auth service (token storage)
│   ├── constants/        # AppConfig (API URL, timeouts, storage keys)
│   ├── error/            # AppError sealed classes
│   ├── models/           # @freezed data classes (User, Project, Member, ChatMessage)
│   ├── providers/        # @riverpod state (auth, projects, members, chat, whisper)
│   ├── repositories/     # Abstract + impl for each domain
│   ├── router/           # go_router navigation
│   └── theme/            # UI theming
├── shared/
│   └── widgets/          # LoadingOverlay, ErrorView, EmptyState
└── features/
    ├── auth/             # LoginScreen
    ├── chat/             # ChatScreen, MessageBubble, ChatInput
    ├── members/          # MembersScreen, AddMemberModal
    ├── profile/          # ProfileScreen (includes Whisper model download)
    └── projects/         # ProjectsListScreen, CreateProjectModal, ProjectSettingsSheet
```

## Flavors & Configuration

| Flavor | Application ID | App Name | API URL |
|--------|----------------|----------|---------|
| dev | `com.mindnest.app.dev` | MindNest Dev | `http://localhost:8000/api` |
| staging | `com.mindnest.app.staging` | MindNest Staging | `https://dev-api.mindnest.one/api` |
| prod | `com.mindnest.app` | MindNest | `https://api.mindnest.one/api` |

Configuration is read from `--dart-define` flags at build time via `lib/core/constants/app_config.dart`.

## iOS Project

```
ios/
├── project.yml              # XcodeGen config (source of truth)
├── Podfile
├── Configurations/
│   ├── Dev.xcconfig
│   ├── Staging.xcconfig
│   └── Prod.xcconfig
└── MindNest/
    ├── AppDelegate.swift
    ├── Info.plist
    ├── MindNest-Dev.entitlements      # applinks/webcredentials: dev.mindnest.one
    ├── MindNest-Staging.entitlements  # applinks/webcredentials: dev.mindnest.one
    └── MindNest-Prod.entitlements     # applinks/webcredentials: mindnest.one
```

**Xcode Cloud schemes:** `dev` (development), `staging` (TestFlight), `prod` (App Store)

**Apple Team ID:** `493Z7C2V3J`

## Android Project

```
android/
├── app/
│   ├── build.gradle.kts     # Flavors + signing config
│   ├── proguard-rules.pro   # R8 rules for release
│   └── src/main/AndroidManifest.xml
├── key.properties           # Signing credentials (gitignored)
└── mindnest-release.jks     # Release keystore (gitignored)
```

Release signing activates automatically when `key.properties` exists. Store keystore outside the repo.

## Deep Links

### iOS Universal Links

File: `web/.well-known/apple-app-site-association`

Handles paths: `/verify-email`, `/verify-email?*`, `/change-password`

Entitlements (separate per flavor):
- Dev/Staging: `applinks:dev.mindnest.one`, `webcredentials:dev.mindnest.one`
- Prod: `applinks:mindnest.one`, `webcredentials:mindnest.one`

### Android App Links

File: `web/.well-known/assetlinks.json`

SHA256 fingerprints:
- Release: `D4:97:32:11:78:12:69:5F:9A:2E:9B:5D:2B:82:FC:A1:92:59:E8:1A:7F:43:DC:49:27:DD:96:AA:73:B4:8D:19`
- Debug: `C2:9D:28:3A:0B:59:29:9D:33:38:A8:7E:AB:1E:D4:B3:C7:08:16:19:F1:2D:3A:7F:5A:71:8D:A9:C1:A1:95:9D`

`AndroidManifest.xml` has HTTPS intent-filter for `/verify-email` and `/change-password`.

### Testing Deep Links

```bash
# iOS Simulator
xcrun simctl openurl booted "https://dev.mindnest.one/verify-email?token=test"

# Android Emulator
adb shell am start -a android.intent.action.VIEW -d "https://dev.mindnest.one/verify-email?token=test"
```

### Email Verification Flow

```
User clicks email link (https://mindnest.one/verify-email?token=XXX)
├── Desktop browser → Flutter Web → EmailVerifiedScreen
├── iOS (app installed) → Universal Links → Native App
├── iOS (no app) → Safari → Flutter Web
├── Android (app installed) → App Links → Native App
└── Android (no app) → Chrome → Flutter Web
```

All paths share the same Flutter code (`EmailVerifiedScreen`) calling `POST /api/auth/verify-email`.

## Flutter Web Notes

- **URL Strategy**: `usePathUrlStrategy()` — path-based routing (`/path`) not hash (`/#/path`)
- **Secure Storage**: Requires HTTPS or `localhost` — always use `localhost` for local dev, not IP
- **Routes**: `/` (landing), `/login`, `/verify-email?token=XXX`, `/forgot-password`, `/projects`, `/chat`, `/profile`

## E2E Testing with Maestro

See `tests/e2e/README.md` for full setup.

**Critical:** Use `Semantics` labels for widget targeting, not `tooltip`:

```dart
Semantics(
  label: 'Send message',  // Maestro finds this
  button: true,
  child: IconButton.filled(tooltip: 'Send', ...),  // tooltip unreliable in Maestro
)
```

Key widgets with Semantics labels:

| Widget | Label | File |
|--------|-------|------|
| Send button | `Send message` | `chat_input.dart` |
| Stop recording | `Stop recording` | `chat_input.dart` |
| Send recording | `Send recording` | `chat_input.dart` |
| Voice input | `Voice input` | `chat_input.dart` |

## Mobile Token Handling

`ApiClient` automatically:
1. Attaches `Authorization: Bearer <token>` to all requests
2. Intercepts 401 responses
3. Calls `/api/auth/refresh` with the refresh token
4. Retries the original request with the new token
5. Logs out if refresh fails
