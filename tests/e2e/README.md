# E2E Multi-User Tests

End-to-end tests using [Maestro](https://maestro.mobile.dev/) for multi-device testing.

**Key Feature:** Uses scenario `.md` files from `tests/scenarios/` - same format as API tests!

## Quick Start

```bash
# Run scenario on multiple emulators
python run_e2e_scenario.py ../scenarios/001-new-year-party.md

# Skip chat messages (only setup - useful for debugging)
python run_e2e_scenario.py ../scenarios/001-new-year-party.md --skip-chat
```

## Prerequisites

1. **Install Maestro**
   ```bash
   curl -Ls "https://get.maestro.mobile.dev" | bash
   ```

2. **Android SDK** with emulators configured
   ```bash
   # List available AVDs
   emulator -list-avds

   # Start emulators (one per user in scenario)
   emulator -avd Pixel_6_API_33 &
   emulator -avd Pixel_7_API_34 &
   # etc...
   ```

3. **Build and install Flutter app**
   ```bash
   cd mobile
   flutter build apk --debug

   # Install on all devices
   adb devices  # list devices
   adb -s emulator-5554 install build/app/outputs/flutter-apk/app-debug.apk
   adb -s emulator-5556 install build/app/outputs/flutter-apk/app-debug.apk
   ```

4. **Backend running**
   ```bash
   cd backend-python
   source venv/bin/activate
   uvicorn app.main:app --reload --port 8000
   ```

## How It Works

The `run_e2e_scenario.py` script:

1. **Parses** scenario `.md` file (users, project, onboarding, chat messages)
2. **Registers** all users via API (only registration via API!)
3. **Assigns** each user to a device
4. **Runs owner flow**: login → create project → onboarding → add members
5. **Runs member flows**: login → join project
6. **Executes** chat messages in sequence on correct devices

```
Scenario File (001-new-year-party.md)
         │
         ▼
┌─────────────────────────────────────────┐
│  Parser extracts:                       │
│  - Users: Andrey (owner), Boris, Vika   │
│  - Project: "New Year Party 2025"       │
│  - Onboarding: description, answers     │
│  - Chat: 20+ messages                   │
└─────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│  API: Register all users                │
└─────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│  Device Assignment:                     │
│  - emulator-5554 → Andrey (owner)       │
│  - emulator-5556 → Boris                │
│  - emulator-5558 → Vika                 │
└─────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│  Owner Flow (Device 1):                 │
│  1. Login                               │
│  2. Create project                      │
│  3. Complete onboarding                 │
│  4. Add all members                     │
└─────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│  Member Flows (Devices 2-N):            │
│  1. Login                               │
│  2. Wait for project to appear          │
│  3. Open project                        │
└─────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│  Chat Messages (in sequence):           │
│  Execute each message on correct device │
└─────────────────────────────────────────┘
```

## Scenario Format

The script parses scenario `.md` files with these sections:

```markdown
## Users

| Name   | Email            | Password | Role   |
|--------|------------------|----------|--------|
| Andrey | andrey@test.com  | test123  | owner  |
| Boris  | boris@test.com   | test123  | member |

## Project

| Field | Value           |
|-------|-----------------|
| Name  | My Project      |

## Onboarding

```
Description: "Project description for LLM"
Answers: "Answers to clarifying questions"
Confirm: "Yes, save it."
```

## Chat Messages

User: Andrey
Chat: "Let's start planning!"
Expected: Agent responds

User: Boris
Chat: "I'll add some items..."
```

## Directory Structure

```
tests/e2e/
├── run_e2e_scenario.py      # Main test runner
├── config.yaml              # Maestro configuration
├── README.md
└── flows/
    └── common/              # Reusable Maestro flows
        ├── login.yaml
        ├── create_project.yaml
        ├── complete_onboarding.yaml
        ├── add_member.yaml
        ├── join_project.yaml
        └── send_message.yaml
```

## Flows

| Flow | Description | Required ENV |
|------|-------------|--------------|
| `login.yaml` | Login existing user | EMAIL, PASSWORD |
| `create_project.yaml` | Create new project | PROJECT_NAME |
| `complete_onboarding.yaml` | Complete onboarding | PROJECT_DESCRIPTION, ONBOARDING_ANSWERS, ONBOARDING_CONFIRM |
| `add_member.yaml` | Add member to project | MEMBER_EMAIL |
| `join_project.yaml` | Wait for and open project | PROJECT_NAME |
| `send_message.yaml` | Send chat message | MESSAGE |

## Debugging

### View Maestro Studio (interactive mode)
```bash
maestro studio
```

### Run single flow manually
```bash
~/.maestro/bin/maestro test flows/common/login.yaml \
  -e EMAIL="test@test.com" \
  -e PASSWORD="test123"
```

### Check device logs
```bash
adb -s emulator-5554 logcat | grep -i flutter
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "Maestro not found" | Install: `curl -Ls "https://get.maestro.mobile.dev" \| bash` |
| "Not enough devices" | Start more emulators: `emulator -avd <name> &` |
| "APK not found" | Run: `flutter build apk --debug` and install |
| "Element not found" | Check widget Keys, run `maestro studio` |
| "Timeout" | Increase timeout in flow yaml files |
| "Login failed" | Check backend is running, user registered |
