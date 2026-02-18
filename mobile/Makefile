.PHONY: run-dev run-staging run-prod build-dev build-staging build-prod clean setup

# === Setup (run after clone) ===

setup:
	flutter pub get
	cd ios && xcodegen generate && pod install

# === Run (Flutter) ===

run-dev:
	flutter run --flavor dev --dart-define=ENVIRONMENT=dev --dart-define=API_URL=http://192.168.68.104:8000/api

run-staging:
	flutter run --flavor staging --dart-define=ENVIRONMENT=staging --dart-define=API_URL=https://dev-api.mindnest.one/api

run-prod:
	flutter run --flavor prod --dart-define=ENVIRONMENT=prod --dart-define=API_URL=https://api.mindnest.one/api

# === iOS Builds (xcodebuild) ===

build-dev-ios:
	flutter build ios --flavor dev --dart-define=ENVIRONMENT=dev --dart-define=API_URL=http://localhost:8000/api --no-codesign

build-staging-ios:
	flutter build ios --flavor staging --dart-define=ENVIRONMENT=staging --dart-define=API_URL=https://dev-api.mindnest.one/api --no-codesign

build-prod-ios:
	flutter build ios --flavor prod --dart-define=ENVIRONMENT=prod --dart-define=API_URL=https://api.mindnest.one/api --no-codesign

# === Android Builds ===

build-dev-apk:
	flutter build apk --flavor dev --dart-define=ENVIRONMENT=dev --dart-define=API_URL=http://10.0.2.2:8000/api

build-staging-apk:
	flutter build apk --flavor staging --dart-define=ENVIRONMENT=staging --dart-define=API_URL=https://dev-api.mindnest.one/api

build-prod-apk:
	flutter build apk --flavor prod --release --dart-define=ENVIRONMENT=prod --dart-define=API_URL=https://api.mindnest.one/api

# === Android App Bundle (for Play Store) ===

build-staging-aab:
	flutter build appbundle --flavor staging --dart-define=ENVIRONMENT=staging --dart-define=API_URL=https://dev-api.mindnest.one/api

build-prod-aab:
	flutter build appbundle --flavor prod --release --dart-define=ENVIRONMENT=prod --dart-define=API_URL=https://api.mindnest.one/api

# === Utilities ===

clean:
	flutter clean
	cd ios && rm -rf Pods Podfile.lock MindNest.xcodeproj MindNest.xcworkspace

regen:
	cd ios && xcodegen generate && pod install

help:
	@echo "Setup:"
	@echo "  make setup       - Run after clone (flutter pub get, xcodegen, pod install)"
	@echo ""
	@echo "Run:"
	@echo "  make run-dev     - Local backend (dev flavor)"
	@echo "  make run-staging - Staging backend (staging flavor)"
	@echo "  make run-prod    - Production backend (prod flavor)"
	@echo ""
	@echo "Build iOS:"
	@echo "  make build-dev-ios     - Dev build"
	@echo "  make build-staging-ios - Staging build"
	@echo "  make build-prod-ios    - Production build"
	@echo ""
	@echo "Build Android APK:"
	@echo "  make build-dev-apk     - Dev APK"
	@echo "  make build-staging-apk - Staging APK"
	@echo "  make build-prod-apk    - Production APK (signed)"
	@echo ""
	@echo "Build Android AAB (Play Store):"
	@echo "  make build-staging-aab - Staging bundle"
	@echo "  make build-prod-aab    - Production bundle (signed)"
	@echo ""
	@echo "Utilities:"
	@echo "  make clean  - Clean all"
	@echo "  make regen  - Regenerate Xcode project"
