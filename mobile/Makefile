.PHONY: run-dev run-staging run-prod build-dev build-staging build-prod clean setup

# === Setup (run after clone) ===

setup:
	flutter pub get
	cd ios && xcodegen generate && pod install

# === Run (Flutter) ===

run-dev:
	flutter run --dart-define=ENVIRONMENT=dev --dart-define=API_URL=http://localhost:8000/api

run-staging:
	flutter run --dart-define=ENVIRONMENT=staging --dart-define=API_URL=https://dev-api.mindnest.one/api

run-prod:
	flutter run --dart-define=ENVIRONMENT=prod --dart-define=API_URL=https://api.mindnest.one/api

# === iOS Builds (xcodebuild) ===

build-dev-ios:
	flutter build bundle --dart-define=ENVIRONMENT=dev --dart-define=API_URL=http://localhost:8000/api
	cd ios && xcodebuild -workspace Runner.xcworkspace -scheme dev -configuration Dev -sdk iphoneos CODE_SIGNING_ALLOWED=NO

build-staging-ios:
	flutter build bundle --dart-define=ENVIRONMENT=staging --dart-define=API_URL=https://dev-api.mindnest.one/api
	cd ios && xcodebuild -workspace Runner.xcworkspace -scheme staging -configuration Staging -sdk iphoneos CODE_SIGNING_ALLOWED=NO

build-prod-ios:
	flutter build bundle --dart-define=ENVIRONMENT=prod --dart-define=API_URL=https://api.mindnest.one/api
	cd ios && xcodebuild -workspace Runner.xcworkspace -scheme prod -configuration Prod -sdk iphoneos CODE_SIGNING_ALLOWED=NO

# === Android Builds ===

build-staging-apk:
	flutter build apk --dart-define=ENVIRONMENT=staging --dart-define=API_URL=https://dev-api.mindnest.one/api

build-prod-apk:
	flutter build apk --release --dart-define=ENVIRONMENT=prod --dart-define=API_URL=https://api.mindnest.one/api

# === Utilities ===

clean:
	flutter clean
	cd ios && rm -rf Pods Podfile.lock Runner.xcodeproj Runner.xcworkspace

regen:
	cd ios && xcodegen generate && pod install

help:
	@echo "Setup:"
	@echo "  make setup       - Run after clone (flutter pub get, xcodegen, pod install)"
	@echo ""
	@echo "Run:"
	@echo "  make run-dev     - Local backend (.dev bundle)"
	@echo "  make run-staging - Staging backend (.staging bundle)"
	@echo "  make run-prod    - Production backend (prod bundle)"
	@echo ""
	@echo "Build iOS:"
	@echo "  make build-dev-ios     - Dev build"
	@echo "  make build-staging-ios - Staging build"
	@echo "  make build-prod-ios    - Production build"
	@echo ""
	@echo "Build Android:"
	@echo "  make build-staging-apk"
	@echo "  make build-prod-apk"
	@echo ""
	@echo "Utilities:"
	@echo "  make clean  - Clean all"
	@echo "  make regen  - Regenerate Xcode project"
