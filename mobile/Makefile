.PHONY: run-dev run-staging run-prod build-staging build-prod clean

# Development (local backend)
run-dev:
	flutter run --dart-define=ENVIRONMENT=dev --dart-define=API_URL=http://localhost:8000/api

run-dev-ios:
	flutter run -d iPhone --dart-define=ENVIRONMENT=dev --dart-define=API_URL=http://localhost:8000/api

# Staging (dev-api.mindnest.one)
run-staging:
	flutter run --dart-define=ENVIRONMENT=staging --dart-define=API_URL=https://dev-api.mindnest.one/api

build-staging-ios:
	flutter build ios --dart-define=ENVIRONMENT=staging --dart-define=API_URL=https://dev-api.mindnest.one/api

build-staging-apk:
	flutter build apk --dart-define=ENVIRONMENT=staging --dart-define=API_URL=https://dev-api.mindnest.one/api

# Production (api.mindnest.one)
run-prod:
	flutter run --release --dart-define=ENVIRONMENT=prod --dart-define=API_URL=https://api.mindnest.one/api

build-prod-ios:
	flutter build ios --release --dart-define=ENVIRONMENT=prod --dart-define=API_URL=https://api.mindnest.one/api

build-prod-apk:
	flutter build apk --release --dart-define=ENVIRONMENT=prod --dart-define=API_URL=https://api.mindnest.one/api

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
	@echo "  make run-dev          - Run with local backend"
	@echo "  make run-staging      - Run with staging backend"
	@echo "  make run-prod         - Run with production backend"
	@echo "  make build-staging-ios - Build iOS for staging"
	@echo "  make build-prod-ios   - Build iOS for production"
	@echo "  make clean            - Clean Flutter build"
	@echo "  make deps             - Get dependencies"
