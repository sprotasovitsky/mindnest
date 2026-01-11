#!/bin/sh

# Xcode Cloud post-clone script

set -e

echo "=== MindNest iOS CI ==="
echo "Scheme: $CI_XCODE_SCHEME"

cd "$CI_PRIMARY_REPOSITORY_PATH/mobile"

# Install Flutter
git clone https://github.com/flutter/flutter.git --depth 1 -b stable "$HOME/flutter"
export PATH="$PATH:$HOME/flutter/bin"
flutter --version

# Dependencies
flutter pub get
dart run build_runner build --delete-conflicting-outputs

# Generate Xcode project
cd ios
xcodegen generate

# Environment based on scheme
case "$CI_XCODE_SCHEME" in
    prod)
        ENVIRONMENT="prod"
        API_URL="https://api.mindnest.one/api"
        ;;
    staging|*)
        ENVIRONMENT="staging"
        API_URL="https://dev-api.mindnest.one/api"
        ;;
esac

echo "Environment: $ENVIRONMENT"
echo "API URL: $API_URL"

# Build Flutter bundle
cd ..
flutter build bundle \
    --dart-define=ENVIRONMENT=$ENVIRONMENT \
    --dart-define=API_URL=$API_URL

echo "=== Ready for Xcode build ==="
