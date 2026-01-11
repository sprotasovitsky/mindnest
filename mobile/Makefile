.PHONY: run-dev run-staging run-prod build-staging build-prod clean

# Development (local backend)
run-dev:
	flutter run --flavor dev --dart-define=ENVIRONMENT=dev --dart-define=API_URL=http://localhost:8000/api

run-dev-android:
	flutter run -d emulator --flavor dev --dart-define=ENVIRONMENT=dev --dart-define=API_URL=http://10.0.2.2:8000/api

run-dev-ios:
	flutter run -d iPhone --flavor dev --dart-define=ENVIRONMENT=dev --dart-define=API_URL=http://localhost:8000/api

# Staging (dev-api.mindnest.one)
run-staging:
	flutter run --flavor staging --dart-define=ENVIRONMENT=staging --dart-define=API_URL=https://dev-api.mindnest.one/api

run-staging-ios:
	flutter run -d iPhone --flavor staging --dart-define=ENVIRONMENT=staging --dart-define=API_URL=https://dev-api.mindnest.one/api

build-staging-ios:
	flutter build ios --flavor staging --dart-define=ENVIRONMENT=staging --dart-define=API_URL=https://dev-api.mindnest.one/api

build-staging-apk:
	flutter build apk --flavor staging --dart-define=ENVIRONMENT=staging --dart-define=API_URL=https://dev-api.mindnest.one/api

# Production (api.mindnest.one)
run-prod:
	flutter run --release --flavor prod --dart-define=ENVIRONMENT=prod --dart-define=API_URL=https://api.mindnest.one/api

build-prod-ios:
	flutter build ios --release --flavor prod --dart-define=ENVIRONMENT=prod --dart-define=API_URL=https://api.mindnest.one/api

build-prod-apk:
	flutter build apk --release --flavor prod --dart-define=ENVIRONMENT=prod --dart-define=API_URL=https://api.mindnest.one/api

# Utilities
clean:
	flutter clean

deps:
	flutter pub get

build-runner:
	dart run build_runner build --delete-conflicting-outputs

# Help
help:
	@echo "Available commands:"
	@echo ""
	@echo "  Development (local backend):"
	@echo "    make run-dev          - Run on default device"
	@echo "    make run-dev-android  - Run on Android emulator"
	@echo "    make run-dev-ios      - Run on iPhone"
	@echo ""
	@echo "  Staging (dev-api.mindnest.one):"
	@echo "    make run-staging      - Run on default device"
	@echo "    make run-staging-ios  - Run on iPhone"
	@echo "    make build-staging-ios - Build iOS for staging"
	@echo "    make build-staging-apk - Build Android APK for staging"
	@echo ""
	@echo "  Production (api.mindnest.one):"
	@echo "    make run-prod         - Run release build"
	@echo "    make build-prod-ios   - Build iOS for production"
	@echo "    make build-prod-apk   - Build Android APK for production"
	@echo ""
	@echo "  Utilities:"
	@echo "    make clean            - Clean Flutter build"
	@echo "    make deps             - Get dependencies"
	@echo "    make build-runner     - Run code generation"
	@echo ""
	@echo "  Bundle IDs:"
	@echo "    dev:     com.mindnest.mindnest.dev"
	@echo "    staging: com.mindnest.mindnest.staging"
	@echo "    prod:    com.mindnest.mindnest"
