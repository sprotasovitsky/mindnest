#!/bin/sh

# Xcode Cloud post-clone script
# This script runs after the repository is cloned

set -e

echo "=== MindNest iOS CI Post Clone ==="

# Navigate to project root
cd "$CI_PRIMARY_REPOSITORY_PATH/mobile"

# Install Flutter
git clone https://github.com/flutter/flutter.git --depth 1 -b stable "$HOME/flutter"
export PATH="$PATH:$HOME/flutter/bin"

# Verify Flutter installation
flutter --version

# Get dependencies
flutter pub get

# Generate code (freezed, json_serializable, riverpod)
dart run build_runner build --delete-conflicting-outputs

# Determine environment from Xcode Cloud workflow
# Set MINDNEST_ENV in Xcode Cloud environment variables (staging or prod)
ENV="${MINDNEST_ENV:-staging}"

if [ "$ENV" = "prod" ]; then
    API_URL="https://api.mindnest.one/api"
    ENVIRONMENT="prod"
else
    API_URL="https://dev-api.mindnest.one/api"
    ENVIRONMENT="staging"
fi

echo "Building for environment: $ENVIRONMENT"
echo "API URL: $API_URL"

# Build Flutter iOS
flutter build ios --release \
    --dart-define=ENVIRONMENT=$ENVIRONMENT \
    --dart-define=API_URL=$API_URL \
    --no-codesign

echo "=== Flutter build complete ==="
