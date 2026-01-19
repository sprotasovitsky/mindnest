# Security Review - MindNest

> Generated: 2026-01-17

## Current Security Posture: GOOD

The project has solid fundamental security practices implemented.

---

## Current Security Measures

### Authentication & Password Security

| Feature | Status | Implementation |
|---------|--------|----------------|
| Password Hashing | ✅ | bcrypt with 12 rounds |
| Password Validation | ✅ | Min 8 chars, letters + digits required |
| JWT Tokens | ✅ | Access (15 min) + Refresh (7 days) |
| Social Auth | ✅ | Google + Apple with proper token verification |
| Email Verification | ✅ | Cryptographic tokens, expiration |
| Legacy Hash Detection | ✅ | Rejects old SHA-256 hashes |

### Password Reset Flow

| Feature | Status | Implementation |
|---------|--------|----------------|
| Multi-step Process | ✅ | Email → 6-digit code → reset token → new password |
| Code Hashing | ✅ | SHA-256 with user_id salt |
| Rate Limiting | ✅ | Max 3 codes/hour, 5 attempts/code |
| Time Limits | ✅ | Codes: 10 min, Reset tokens: 15 min |
| Email Enumeration Protection | ✅ | Same response for existing/non-existing users |

### API Security

| Feature | Status | Implementation |
|---------|--------|----------------|
| Rate Limiting | ✅ | slowapi with environment-specific limits |
| CORS | ✅ | Explicit allowed origins |
| Input Validation | ✅ | Pydantic models |
| Bearer Token Auth | ✅ | All sensitive endpoints protected |

### Database Security

| Feature | Status | Implementation |
|---------|--------|----------------|
| SQL Injection Prevention | ✅ | SQLAlchemy ORM, parameterized queries |
| Connection Pooling | ✅ | pool_pre_ping=True |
| Async Operations | ✅ | Non-blocking database access |

### Mobile Security

| Feature | Status | Implementation |
|---------|--------|----------------|
| Secure Token Storage | ✅ | FlutterSecureStorage |
| Auto Token Refresh | ✅ | 401 → refresh → retry |
| Environment-based Config | ✅ | Separate URLs for dev/staging/prod |

---

## Identified Gaps

### High Priority

| Gap | Risk | Recommendation |
|-----|------|----------------|
| No Security Headers | Medium | Add HSTS, CSP, X-Frame-Options, X-Content-Type-Options |
| No HTTPS Enforcement | Medium | Add HTTPSRedirectMiddleware in production |
| No Certificate Pinning | Medium | Implement in mobile app to prevent MITM |
| No Dependency Scanning | Medium | Add Dependabot/Snyk to CI |

### Medium Priority

| Gap | Risk | Recommendation |
|-----|------|----------------|
| No Audit Logging | Low-Medium | Add structured logging for auth events |
| No Token Revocation List | Low | Implement for account deletion scenarios |
| Debug Mode Rate Limits | Low | Very high limits (100-200/min) could be exploited |
| No SAST in CI | Low | Add Bandit, CodeQL |

### Low Priority

| Gap | Risk | Recommendation |
|-----|------|----------------|
| No Obfuscation | Low | Add --obfuscate for release builds |
| No Root/Jailbreak Detection | Low | Add flutter_jailbreak_detection |
| CORS Wildcard | Low | Remove `https://*.mindnest.one` if possible |

---

## Recommended Security Reviews

### 1. Automated Dependency Scanning (CI/CD)

```yaml
# .github/workflows/security.yml
name: Security Scan

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
  schedule:
    - cron: '0 0 * * 1'  # Weekly on Monday

jobs:
  python-security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6

      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      # Bandit - Python static security analysis
      - name: Run Bandit
        run: |
          pip install bandit
          bandit -r backend-python/app -f json -o bandit-report.json || true
          bandit -r backend-python/app

      # pip-audit - known vulnerabilities in dependencies
      - name: Run pip-audit
        run: |
          pip install pip-audit
          pip-audit -r backend-python/requirements.txt

      # Safety - CVE database check
      - name: Run Safety
        run: |
          pip install safety
          safety check -r backend-python/requirements.txt

  flutter-security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6

      - uses: subosito/flutter-action@v2
        with:
          flutter-version: '3.38.6'

      - name: Get dependencies
        working-directory: mobile
        run: flutter pub get

      # Check for outdated packages
      - name: Check outdated packages
        working-directory: mobile
        run: flutter pub outdated

      # Analyze code
      - name: Flutter analyze
        working-directory: mobile
        run: flutter analyze

  codeql:
    runs-on: ubuntu-latest
    permissions:
      security-events: write
    steps:
      - uses: actions/checkout@v6

      - name: Initialize CodeQL
        uses: github/codeql-action/init@v3
        with:
          languages: python

      - name: Perform CodeQL Analysis
        uses: github/codeql-action/analyze@v3
```

### 2. Security Headers Middleware

Add to `backend-python/app/main.py`:

```python
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

# HTTPS redirect in production
if not settings.debug:
    app.add_middleware(HTTPSRedirectMiddleware)
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["api.mindnest.one", "dev-api.mindnest.one"]
    )

# Security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)

    # Prevent MIME type sniffing
    response.headers["X-Content-Type-Options"] = "nosniff"

    # Prevent clickjacking
    response.headers["X-Frame-Options"] = "DENY"

    # XSS protection (legacy browsers)
    response.headers["X-XSS-Protection"] = "1; mode=block"

    # HSTS - force HTTPS for 1 year
    if not settings.debug:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

    # Content Security Policy
    response.headers["Content-Security-Policy"] = "default-src 'self'; frame-ancestors 'none'"

    # Referrer Policy
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

    # Permissions Policy
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"

    return response
```

### 3. Mobile Certificate Pinning

Add to `mobile/lib/core/api/api_client.dart`:

```dart
import 'dart:io';
import 'package:dio/io.dart';

// In ApiClient constructor or initialization:
void _setupCertificatePinning() {
  if (_dio.httpClientAdapter is IOHttpClientAdapter) {
    (_dio.httpClientAdapter as IOHttpClientAdapter).createHttpClient = () {
      final client = HttpClient();
      client.badCertificateCallback = (cert, host, port) {
        // SHA-256 fingerprint of your certificate
        const expectedFingerprint = 'YOUR_CERTIFICATE_SHA256_FINGERPRINT';
        final actualFingerprint = cert.sha256.map((b) => b.toRadixString(16).padLeft(2, '0')).join(':');
        return actualFingerprint.toUpperCase() == expectedFingerprint.toUpperCase();
      };
      return client;
    };
  }
}
```

### 4. Audit Logging

Add to `backend-python/app/audit.py`:

```python
import structlog
from datetime import datetime, timezone
from typing import Optional

logger = structlog.get_logger()

class AuditLogger:
    @staticmethod
    def log_auth_event(
        event_type: str,
        email_hash: str,
        success: bool,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        reason: Optional[str] = None
    ):
        logger.info(
            "auth_event",
            event_type=event_type,
            email_hash=email_hash[:8],  # Only first 8 chars for privacy
            success=success,
            ip_address=ip_address,
            user_agent=user_agent,
            reason=reason,
            timestamp=datetime.now(timezone.utc).isoformat()
        )

    @staticmethod
    def log_sensitive_action(
        action: str,
        user_id: str,
        resource_type: str,
        resource_id: Optional[str] = None,
        details: Optional[dict] = None
    ):
        logger.info(
            "sensitive_action",
            action=action,
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            timestamp=datetime.now(timezone.utc).isoformat()
        )

# Usage in auth.py:
# AuditLogger.log_auth_event("login", hashlib.sha256(email.encode()).hexdigest(), success=True, ip_address=request.client.host)
```

### 5. Pre-commit Hooks for Secrets Detection

Create `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.4.0
    hooks:
      - id: detect-secrets
        args: ['--baseline', '.secrets.baseline']
        exclude: \.lock$|\.g\.dart$|\.freezed\.dart$

  - repo: https://github.com/PyCQA/bandit
    rev: 1.7.7
    hooks:
      - id: bandit
        args: ['-r', 'backend-python/app', '-ll']

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: check-added-large-files
        args: ['--maxkb=1000']
      - id: check-case-conflict
      - id: check-merge-conflict
      - id: detect-private-key
```

### 6. OWASP ZAP API Scanning

Add to CI for staging deployments:

```yaml
  api-security-scan:
    needs: [build-and-deploy]
    runs-on: ubuntu-latest
    steps:
      - name: OWASP ZAP API Scan
        uses: zaproxy/action-api-scan@v0.7.0
        with:
          target: 'https://dev-api.mindnest.one/openapi.json'
          format: openapi
          allow_issue_writing: false
```

### 7. Flutter Obfuscation

Update `mobile/Makefile`:

```makefile
build-prod-apk:
	flutter build apk --flavor prod --release \
		--dart-define=ENVIRONMENT=prod \
		--dart-define=API_URL=https://api.mindnest.one/api \
		--obfuscate \
		--split-debug-info=build/debug-info

build-prod-aab:
	flutter build appbundle --flavor prod --release \
		--dart-define=ENVIRONMENT=prod \
		--dart-define=API_URL=https://api.mindnest.one/api \
		--obfuscate \
		--split-debug-info=build/debug-info
```

---

## SAST Tools Comparison

| Tool | Language | Free | CI Integration | Depth |
|------|----------|------|----------------|-------|
| **Bandit** | Python | ✅ | GitHub Action | Medium |
| **Semgrep** | Multi | ✅ (OSS) | GitHub Action | High |
| **CodeQL** | Multi | ✅ | GitHub Native | Very High |
| **Snyk** | Multi | Freemium | GitHub App | High |
| **SonarQube** | Multi | Freemium | Self-hosted | Very High |

---

## Action Plan

### Phase 1: Quick Wins (1-2 days)

- [ ] Enable Dependabot in GitHub Settings
- [ ] Add security headers middleware
- [ ] Add CodeQL workflow
- [ ] Enable flutter obfuscation for release builds

### Phase 2: CI/CD Security (3-5 days)

- [ ] Add Bandit + pip-audit to CI
- [ ] Add pre-commit hooks for secrets detection
- [ ] Configure OWASP ZAP for staging

### Phase 3: Advanced (1-2 weeks)

- [ ] Implement certificate pinning in mobile
- [ ] Add audit logging infrastructure
- [ ] Implement token revocation list
- [ ] Add root/jailbreak detection

---

## Files Reference

| Area | File Path |
|------|-----------|
| Backend Auth | `backend-python/app/routers/auth.py` |
| Backend Config | `backend-python/app/config.py` |
| Backend Main | `backend-python/app/main.py` |
| Social Auth | `backend-python/app/routers/social_auth.py` |
| Mobile API Client | `mobile/lib/core/api/api_client.dart` |
| Mobile Auth | `mobile/lib/core/auth/auth_service.dart` |
| Mobile Config | `mobile/lib/core/constants/app_config.dart` |

---

## Compliance Considerations

| Standard | Relevance | Notes |
|----------|-----------|-------|
| GDPR | High | User data, email masking already implemented |
| OWASP Top 10 | High | Most items addressed, some gaps noted |
| SOC 2 | Medium | Would need audit logging, access controls |
| PCI DSS | Low | Not handling payment data directly |

---

*This document should be reviewed and updated quarterly.*
