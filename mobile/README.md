# MindNest Mobile

Flutter app for MindNest - AI-first knowledge and task management through chat interface.

## Tech Stack

- **Framework**: Flutter 3.2+
- **State Management**: Riverpod with code generation
- **Routing**: go_router
- **HTTP Client**: Dio
- **Storage**: flutter_secure_storage (tokens), shared_preferences (settings)

## Project Structure

```
lib/
├── main.dart               # App entry point
├── core/
│   ├── api/               # HTTP client (Dio-based)
│   │   └── api_client.dart
│   ├── auth/              # Authentication state & service
│   │   ├── auth_service.dart
│   │   └── auth_state.dart
│   ├── projects/          # Project state management
│   │   └── project_state.dart
│   ├── router/            # Navigation (go_router)
│   │   └── app_router.dart
│   └── theme/             # UI theming
│       └── app_theme.dart
└── features/
    ├── auth/
    │   └── presentation/screens/login_screen.dart
    ├── chat/
    │   └── presentation/
    │       ├── screens/chat_screen.dart
    │       └── widgets/
    │           ├── message_bubble.dart
    │           └── chat_input.dart
    └── onboarding/
        └── presentation/screens/onboarding_screen.dart
```

## Setup

### Prerequisites

- Flutter SDK 3.2+
- Running backend on `http://localhost:8000` (see `backend-python/README.md`)

### Installation

```bash
# Install dependencies
flutter pub get

# Generate code (freezed, json_serializable, riverpod)
dart run build_runner build
```

### Running

```bash
# Run on connected device/emulator
flutter run

# Run in web browser
flutter run -d chrome

# Run on specific device
flutter devices  # List available devices
flutter run -d <device_id>
```

### Building

```bash
# Android APK
flutter build apk

# iOS (requires macOS)
flutter build ios

# Web
flutter build web
```

## Code Generation

After modifying providers, data classes with `@freezed`, or models with `@JsonSerializable`:

```bash
dart run build_runner build

# Or watch for changes
dart run build_runner watch
```

## Configuration

The app uses build flavors with `--dart-define` for environment configuration:

| Flavor | API URL | Bundle ID |
|--------|---------|-----------|
| `dev` | `http://localhost:8000/api` | `com.mindnest.app.dev` |
| `staging` | `https://dev-api.mindnest.one/api` | `com.mindnest.app.staging` |
| `prod` | `https://api.mindnest.one/api` | `com.mindnest.app` |

Use Makefile commands for easy flavor management:
```bash
make run-dev        # Local development
make run-staging    # Staging server
make run-prod       # Production server
```

Configuration is in `lib/core/constants/app_config.dart`.

## Web-Specific Notes

- **URL Strategy**: Uses path-based routing (`/path`) instead of hash-based (`/#/path`) via `usePathUrlStrategy()`
- **Deep Links**: Email verification links work on web via `/verify-email?token=...` route
- **Local Development**: Run on `localhost` — `FlutterSecureStorage` requires secure context (HTTPS or localhost)

## Features

- User authentication (login/register)
- Project-based chat interface
- Real-time AI responses
- Markdown support in messages
