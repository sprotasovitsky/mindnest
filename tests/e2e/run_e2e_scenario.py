#!/usr/bin/env python3
"""
E2E Test Runner - runs multi-device UI tests using data from scenario files.

Usage:
    python run_e2e_scenario.py ../scenarios/001-new-year-party.md

Flow:
    1. Parse scenario file (users, project, onboarding, chat messages)
    2. Register all users via API
    3. Get available Android emulators
    4. Owner flow: login → create project → onboarding → add members
    5. Member flows: login → wait for project to appear
    6. Execute chat messages in sequence on the appropriate device
"""

import argparse
import os
import re
import subprocess
import sys
import time
import requests

BASE_URL = os.environ.get("API_URL", "http://localhost:8000")
MAESTRO_PATH = os.path.expanduser("~/.maestro/bin/maestro")
JAVA_HOME = subprocess.run(
    ["brew", "--prefix", "openjdk@17"],
    capture_output=True, text=True
).stdout.strip() + "/libexec/openjdk.jdk/Contents/Home"
FLOWS_DIR = os.path.join(os.path.dirname(__file__), "flows")


def parse_scenario(filepath: str) -> dict:
    """Parse scenario markdown file and extract test data."""
    with open(filepath, 'r') as f:
        content = f.read()

    data = {
        "users": [],
        "project": {},
        "onboarding": {},
        "chats": [],
    }

    # Parse Users table (Name, Email, Password, Role)
    users_match = re.search(
        r'## Users\s*\n\s*\|.*\|\s*\n\s*\|[-\s|]+\|\s*\n((?:\|.*\|\s*\n)+)',
        content
    )
    if users_match:
        for line in users_match.group(1).strip().split('\n'):
            parts = [p.strip() for p in line.split('|')[1:-1]]
            if len(parts) >= 4:
                data["users"].append({
                    "name": parts[0],
                    "email": parts[1],
                    "password": parts[2],
                    "role": parts[3],
                })

    # Parse Project table
    project_match = re.search(
        r'## Project\s*\n\s*\|.*\|.*\|\s*\n\s*\|[-\s|]+\|\s*\n((?:\|.*\|\s*\n)+)',
        content
    )
    if project_match:
        for line in project_match.group(1).strip().split('\n'):
            parts = [p.strip() for p in line.split('|')[1:-1]]
            if len(parts) >= 2:
                data["project"][parts[0].lower()] = parts[1]

    # Parse Onboarding block
    onboarding_match = re.search(
        r'## Onboarding\s*\n\s*```\s*\n(.*?)\n```',
        content, re.DOTALL
    )
    if onboarding_match:
        for line in onboarding_match.group(1).strip().split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                # Remove quotes from value
                value = value.strip().strip('"')
                data["onboarding"][key.strip().lower()] = value

    # Parse Chat messages (User: Name\nChat: "message")
    chat_matches = re.findall(
        r'User:\s*(\w+)\s*\nChat:\s*"([^"]+)"',
        content
    )
    for user, message in chat_matches:
        data["chats"].append({"user": user, "message": message})

    return data


def register_users(users: list, timestamp: str) -> dict:
    """Register users via API and return email mapping."""
    print(f"\n📝 Registering {len(users)} users...")
    email_map = {}

    for user in users:
        # Replace placeholder emails with timestamped ones
        email = user["email"]
        if "@test.com" in email:
            base = email.split("@")[0]
            email = f"{base}_{timestamp}@test.com"

        email_map[user["name"]] = email

        try:
            response = requests.post(
                f"{BASE_URL}/api/auth/register",
                json={"email": email, "password": user["password"], "name": user["name"]},
                timeout=10,
            )
            if response.status_code == 200:
                print(f"  ✓ {user['name']} ({email})")
            elif "already registered" in response.text.lower():
                print(f"  • {user['name']} ({email}) - already exists")
            else:
                print(f"  ✗ {user['name']}: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"  ✗ {user['name']}: {e}")
            return None

    return email_map


def get_android_devices() -> list:
    """Get list of connected Android devices/emulators."""
    result = subprocess.run(
        ["adb", "devices"],
        capture_output=True, text=True
    )
    devices = []
    for line in result.stdout.strip().split('\n')[1:]:
        if '\t' in line and 'device' in line:
            device_id = line.split('\t')[0]
            devices.append(device_id)
    return devices


def run_maestro_flow(flow: str, env: dict, device: str = None) -> bool:
    """Run a Maestro flow with environment variables on a specific device."""
    flow_path = os.path.join(FLOWS_DIR, flow)
    cmd = [MAESTRO_PATH]

    if device:
        cmd.extend(["--device", device])

    cmd.extend(["test", flow_path])

    for key, value in env.items():
        cmd.extend(["-e", f"{key}={value}"])

    my_env = os.environ.copy()
    my_env["JAVA_HOME"] = JAVA_HOME

    result = subprocess.run(cmd, env=my_env, cwd=os.path.dirname(__file__))
    return result.returncode == 0


def run_owner_flow(data: dict, email_map: dict, timestamp: str, device: str) -> bool:
    """Run the owner flow: login, create project, onboarding, add members."""
    owner = next((u for u in data["users"] if u["role"] == "owner"), None)
    if not owner:
        print("❌ No owner found in scenario")
        return False

    members = [u for u in data["users"] if u["role"] == "member"]
    project_name = f"{data['project'].get('name', 'Test Project')} {timestamp}"

    print(f"\n🎯 Owner flow for {owner['name']} on device {device}...")

    # Step 1: Login
    print("  → Login...")
    if not run_maestro_flow("common/login.yaml", {
        "EMAIL": email_map[owner["name"]],
        "PASSWORD": owner["password"],
    }, device):
        print("  ❌ Login failed")
        return False

    # Step 2: Create project
    print(f"  → Creating project: {project_name}")
    if not run_maestro_flow("common/create_project.yaml", {
        "PROJECT_NAME": project_name,
    }, device):
        print("  ❌ Create project failed")
        return False

    # Step 3: Complete onboarding
    print("  → Completing onboarding...")
    if not run_maestro_flow("common/complete_onboarding.yaml", {
        "PROJECT_DESCRIPTION": data["onboarding"].get("description", ""),
        "ONBOARDING_ANSWERS": data["onboarding"].get("answers", ""),
        "ONBOARDING_CONFIRM": data["onboarding"].get("confirm", "Yes, save it."),
    }, device):
        print("  ❌ Onboarding failed")
        return False

    # Step 4: Add members (open once, add all, close once)
    if members:
        if not run_maestro_flow("common/open_members.yaml", {}, device):
            print("  ❌ Failed to open members screen")
            return False

        for member in members:
            print(f"  → Adding member: {member['name']}")
            if not run_maestro_flow("common/add_member_inline.yaml", {
                "MEMBER_EMAIL": email_map[member["name"]],
            }, device):
                print(f"  ❌ Failed to add member {member['name']}")
                return False

        if not run_maestro_flow("common/close_members.yaml", {}, device):
            print("  ❌ Failed to close members screen")
            return False

    print("  ✅ Owner flow completed")
    return True


def run_member_login(user: dict, email: str, project_name: str, device: str) -> bool:
    """Login a member and wait for project to appear."""
    print(f"\n👤 Member flow for {user['name']} on device {device}...")

    # Login
    print("  → Login...")
    if not run_maestro_flow("common/login.yaml", {
        "EMAIL": email,
        "PASSWORD": user["password"],
    }, device):
        print("  ❌ Login failed")
        return False

    # Wait for and open project
    print(f"  → Joining project: {project_name}")
    if not run_maestro_flow("common/join_project.yaml", {
        "PROJECT_NAME": project_name,
    }, device):
        print("  ❌ Join project failed")
        return False

    print("  ✅ Member logged in and ready")
    return True


def sanitize_message(message: str) -> str:
    """Sanitize message for Maestro input (ASCII only, no newlines)."""
    # Replace newlines with spaces
    message = message.replace("\n", " ").replace("\r", " ")
    # Remove multiple spaces
    import re
    message = re.sub(r'\s+', ' ', message)
    # Keep only ASCII printable characters
    message = ''.join(c if ord(c) < 128 and c.isprintable() else ' ' for c in message)
    return message.strip()


def run_chat_messages(chats: list, user_devices: dict) -> bool:
    """Execute chat messages in sequence on the appropriate devices."""
    if not chats:
        print("\n💬 No chat messages in scenario")
        return True

    print(f"\n💬 Executing {len(chats)} chat messages...")

    for i, chat in enumerate(chats, 1):
        user = chat["user"]
        message = sanitize_message(chat["message"])
        device = user_devices.get(user)

        if not device:
            print(f"  ❌ [{i}] No device for user {user}")
            return False

        print(f"  [{i}/{len(chats)}] {user}: {message[:50]}...")

        if not run_maestro_flow("common/send_message.yaml", {
            "MESSAGE": message,
        }, device):
            print(f"  ❌ Failed to send message")
            return False

    print("  ✅ All messages sent")
    return True


def main():
    parser = argparse.ArgumentParser(description="Run E2E tests from scenario file")
    parser.add_argument("scenario", help="Path to scenario .md file")
    parser.add_argument("--timestamp", help="Timestamp for unique emails")
    parser.add_argument("--skip-chat", action="store_true", help="Skip chat messages (only setup)")
    args = parser.parse_args()

    timestamp = args.timestamp or str(int(time.time()))

    print(f"🚀 E2E Test Runner")
    print(f"   Scenario: {args.scenario}")
    print(f"   Timestamp: {timestamp}")

    # Parse scenario
    data = parse_scenario(args.scenario)
    print(f"\n📋 Parsed scenario:")
    print(f"   Users: {len(data['users'])} ({', '.join(u['name'] for u in data['users'])})")
    print(f"   Project: {data['project'].get('name', 'N/A')}")
    print(f"   Onboarding: {'Yes' if data['onboarding'] else 'No'}")
    print(f"   Chat messages: {len(data['chats'])}")

    # Check devices
    devices = get_android_devices()
    required_devices = len(data["users"])
    print(f"\n📱 Devices: {len(devices)} available, {required_devices} required")

    if len(devices) < required_devices:
        print(f"❌ Not enough devices! Need {required_devices}, have {len(devices)}")
        print("   Start more emulators with: emulator -avd <name>")
        sys.exit(1)

    for i, device in enumerate(devices[:required_devices]):
        print(f"   [{i+1}] {device}")

    # Register users
    email_map = register_users(data["users"], timestamp)
    if not email_map:
        print("\n❌ User registration failed")
        sys.exit(1)

    # Assign devices to users
    owner = next((u for u in data["users"] if u["role"] == "owner"), None)
    members = [u for u in data["users"] if u["role"] == "member"]

    user_devices = {}
    user_devices[owner["name"]] = devices[0]
    for i, member in enumerate(members):
        user_devices[member["name"]] = devices[i + 1]

    print(f"\n📱 Device assignments:")
    for user, device in user_devices.items():
        print(f"   {user} → {device}")

    # Project name with timestamp
    project_name = f"{data['project'].get('name', 'Test Project')} {timestamp}"

    # Run owner flow
    if not run_owner_flow(data, email_map, timestamp, devices[0]):
        print("\n❌ Owner flow failed")
        sys.exit(1)

    # Run member flows (login and join project)
    for i, member in enumerate(members):
        if not run_member_login(member, email_map[member["name"]], project_name, devices[i + 1]):
            print(f"\n❌ Member {member['name']} flow failed")
            sys.exit(1)

    # Run chat messages
    if not args.skip_chat:
        if not run_chat_messages(data["chats"], user_devices):
            print("\n❌ Chat messages failed")
            sys.exit(1)
    else:
        print("\n⏭️  Skipping chat messages (--skip-chat)")

    print("\n✅ E2E test completed successfully!")


if __name__ == "__main__":
    main()
