#!/bin/sh
# ci_post_clone.sh - Xcode Cloud post-clone script for Flutter builds
# This script runs after the repo is cloned but before the build starts

set -e

echo "=== MindNest iOS Build Script ==="
echo "CI_XCODE_SCHEME: $CI_XCODE_SCHEME"
echo "CI_WORKFLOW: $CI_WORKFLOW"

# Navigate to project root (parent of ios directory)
cd "$CI_PRIMARY_REPOSITORY_PATH/mobile"

# Determine flavor from scheme name
# Xcode Cloud uses the scheme name which should be: dev, staging, or prod
FLAVOR="${CI_XCODE_SCHEME:-staging}"

case "$FLAVOR" in
    "dev")
        ENVIRONMENT="dev"
        API_URL="http://localhost:8000/api"
        ;;
    "staging")
        ENVIRONMENT="staging"
        API_URL="https://dev-api.mindnest.one/api"
        ;;
    "prod")
        ENVIRONMENT="prod"
        API_URL="https://api.mindnest.one/api"
        ;;
    *)
        echo "Unknown flavor: $FLAVOR, defaulting to staging"
        FLAVOR="staging"
        ENVIRONMENT="staging"
        API_URL="https://dev-api.mindnest.one/api"
        ;;
esac

echo "Building for flavor: $FLAVOR"
echo "Environment: $ENVIRONMENT"
echo "API URL: $API_URL"

# Install Flutter
echo "=== Installing Flutter ==="
git clone https://github.com/flutter/flutter.git --depth 1 -b stable "$HOME/flutter"
export PATH="$PATH:$HOME/flutter/bin"

# Verify Flutter installation
flutter --version

# Get dependencies
echo "=== Getting Dependencies ==="
flutter pub get

# Generate code (freezed, json_serializable, riverpod)
echo "=== Running Code Generation ==="
dart run build_runner build --delete-conflicting-outputs

# Build iOS without codesigning (Xcode Cloud handles signing)
echo "=== Building iOS ==="
flutter build ios --flavor "$FLAVOR" \
    --dart-define=ENVIRONMENT="$ENVIRONMENT" \
    --dart-define=API_URL="$API_URL" \
    --no-codesign

echo "=== Build Complete ==="
if [ "$FLAVOR" = "prod" ]; then
    echo "Bundle ID: com.mindnest.mindnest"
else
    echo "Bundle ID: com.mindnest.mindnest.$FLAVOR"
fi
