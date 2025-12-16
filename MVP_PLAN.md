# MindNest MVP - Development Plan

## Overview

**MVP Goal:** Working prototype for personal use — chat interface for knowledge and task management.

**Tech Stack:**
- Frontend: Flutter + Dart (iOS, Android, Web)
- Backend: Java 21 + Spring Boot 3.2
- AI: Google Vertex AI (Gemini + Embeddings)
- Storage: Neo4j + Qdrant + PostgreSQL
- Deploy: Docker Compose on Google Cloud VM

---

## Phase 0: Infrastructure ✅

### 0.1 Project Setup

- [x] Create repository (GitHub/GitLab)
- [x] Set up project structure:
  ```
  mindnest/
  ├── mobile/            # Flutter (iOS, Android, Web)
  ├── backend/           # Spring Boot
  ├── docker/            # Docker Compose
  └── docs/              # Documentation
  ```
- [x] Set up Docker Compose (dev environment)
- [ ] Set up CI/CD (GitHub Actions)

### 0.2 Google Cloud

- [x] Create Google Cloud project
- [x] Enable Vertex AI API
- [x] Create Service Account + keys
- [ ] Set up billing alerts

### 0.3 Databases (Docker)

- [x] Neo4j container + health check
- [x] Qdrant container + health check
- [x] PostgreSQL container + init scripts
- [x] Docker network between services

**Completion criteria:** `docker-compose up` starts all services, they are accessible. ✅

---

## Phase 1: Backend Core ✅

### 1.1 Spring Boot Scaffold

- [x] Create Spring Boot project (Java 21, Gradle/Maven)
- [x] Configure Virtual Threads
- [x] Connect Spring Data Neo4j
- [x] Connect Qdrant client
- [x] Connect Spring Data JPA (PostgreSQL)
- [x] Basic configuration (application.yml)

### 1.2 Data Models

- [x] `KnowledgeItem` entity (Neo4j)
  ```java
  @Node
  public class KnowledgeItem {
      String id;
      KnowledgeType type;  // fact, task, decision, note, question
      String content;
      TaskStatus status;   // for tasks
      LocalDate deadline;  // for tasks
      String ownerId;
      String projectId;
      LocalDateTime createdAt;
      LocalDateTime updatedAt;
  }
  ```
- [x] `KnowledgeRelation` between KnowledgeItems (Neo4j)
  - RelationType: RELATES_TO, DEPENDS_ON, SUBTASK_OF, SUPPORTS, CONTRADICTS, REFERENCES, DERIVED_FROM, SIMILAR_TO
- [x] `User` entity (PostgreSQL)
- [x] `Project` entity (PostgreSQL)
- [x] `Conversation` entity (PostgreSQL)
- [x] `Message` entity (PostgreSQL)

### 1.3 Repositories

- [x] `KnowledgeRepository` (Neo4j)
  - `findById`
  - `findByProjectId`
  - `findRelated(id, depth)`
  - `findByTypeAndStatus`
  - `createRelation`, `deleteRelation`, `findDirectRelations`
- [x] `UserRepository` (PostgreSQL)
- [x] `ProjectRepository` (PostgreSQL)
- [x] `ConversationRepository` (PostgreSQL)
- [x] `MessageRepository` (PostgreSQL)

### 1.4 Vertex AI Integration

- [x] `LlmService` — Gemini calls
- [x] `EmbeddingService` — text-embedding-004
- [x] `ModelRouter` — model selection by task type
- [x] Rate limiting / error handling

### 1.5 Vector Search

- [x] `VectorRepository` (Qdrant)
  - `upsert(id, vector, metadata)`
  - `search(vector, limit, filters)`
- [x] Integration with EmbeddingService

**Completion criteria:** API endpoints work, data persists in DB. ✅

---

## Phase 2: Agent Layer ✅

### 2.1 Tools (Agent Functions)

- [x] **Knowledge Tools:**
  - `createKnowledge(type, content, projectId)`
  - `getKnowledge(id)`
  - `updateKnowledge(id, content)`
  - `searchKnowledge(query)` — semantic search
  - `getRelatedKnowledge(id, depth)`
  - `createRelation(sourceId, targetId, relationType)`
  - `getRelations(itemId)`

- [x] **Task Tools:**
  - `createTask(title, description, deadline, projectId)`
  - `updateTaskStatus(id, status)`
  - `getTasksForToday(userId)`
  - `getTasksByStatus(status, projectId)`
  - `decomposeTask(taskId, subtasks)` — break into subtasks
  - `getSubtasks(parentTaskId)`

- [x] **Project Tools:**
  - `createProject(name)`
  - `getProjects(userId)`
  - `switchProject(projectId)`

- [x] **Time Tools (programmatic, no LLM):**
  - `getCurrentDate()`
  - `filterByDeadline(tasks, date)`
  - `getOverdueTasks()`

### 2.2 Orchestrator Agent

- [x] System prompt (secretary persona)
- [x] Tool definitions for Gemini
- [x] Conversation context management (uses last 10 messages)
- [x] Model routing logic
- [x] Confidence score in responses
- [x] Source attribution (tracks searched items)

### 2.3 API Endpoints

- [x] `POST /api/chat` — main chat
  ```json
  Request: { "message": "...", "projectId": "...", "conversationId": "..." }
  Response: { "reply": "...", "sources": [...], "confidence": 0.95, "conversationId": "..." }
  ```
- [x] `GET /api/projects` — list projects
- [x] `POST /api/projects` — create project
- [ ] WebSocket for streaming responses (optional, not in MVP)

**Completion criteria:** Can chat with agent via API, it creates/searches knowledge and tasks. ✅

---

## Phase 3: Frontend (Flutter) ✅

### 3.1 Flutter Scaffold

- [x] Create Flutter project
- [x] Set up structure (clean architecture)
- [x] Set up HTTP client (Dio)
- [x] Set up state management (Riverpod)
- [x] Set up routing (go_router)

### 3.2 Auth

- [x] Login screen (email/password)
- [x] Register screen
- [x] Secure storage for tokens (flutter_secure_storage)
- [x] Auth state management (AuthNotifier)
- [x] Protected routes with redirect
- [x] JWT token handling in API client

### 3.3 Chat Interface

- [x] Chat screen
  - Message list (ListView)
  - Input field
  - Send button
  - Loading indicator ("Thinking...")
- [x] Message widget (markdown rendering with flutter_markdown)
- [x] Auto-scroll to new messages
- [x] Keyboard handling
- [x] Backend API integration
- [x] Error message display

### 3.4 Onboarding

- [x] Welcome screen for new users
- [x] 4-page onboarding flow:
  - Welcome to MindNest
  - Organize Your Knowledge
  - Manage Tasks Intelligently
  - Chat Naturally
- [x] Skip/Next navigation
- [x] Persisted onboarding completion status

### 3.5 Project Switcher

- [x] Bottom sheet for projects
- [x] Create new project
- [x] Select/switch project
- [x] Current project indicator

### 3.6 Platforms

- [x] Android build + test (`flutter build apk --debug`)
- [x] iOS build + test (`flutter build ios --debug`)
- [x] Web build + test (`flutter build web`)

**Completion criteria:** Can install on phone, log in, select project, chat with agent. ✅

---

## Phase 4: Integration and Polish ✅

### 4.1 End-to-end Scenarios

- [x] Create project → add knowledge → create task → find connections
- [x] "What tasks do I have today?" works
- [x] "Break down this task into subtasks" works
- [x] Semantic search finds relevant items

### 4.2 Onboarding Flow

- [x] Onboarding screens for new users
- [x] Smooth transition to chat after onboarding

### 4.3 Error Handling

- [x] Graceful errors in UI (error message bubbles)
- [x] Retry logic for API calls (3 retries with exponential backoff)
- [x] ApiException class with error details
- [x] Fallback messages if backend unavailable

### 4.4 Basic Security

- [x] CORS configuration (localhost origins)
- [x] Rate limiting (60 req/min per user/IP, sliding window)
- [x] JWT authentication
- [x] BCrypt password encoding

**Completion criteria:** Full flow works without critical bugs. ✅

---

## Phase 5: Deploy

### 5.1 Production Setup

- [ ] Create Compute Engine VM
- [ ] Configure Docker Compose for prod
- [ ] Configure Nginx (reverse proxy + SSL)
- [ ] Domain + HTTPS (Let's Encrypt)

### 5.2 Monitoring

- [ ] Cloud Logging
- [ ] Health checks
- [ ] Basic alerts

### 5.3 Backup

- [ ] Backup scripts for Neo4j, PostgreSQL, Qdrant
- [ ] Cron job for automatic backups

**Completion criteria:** App accessible via domain, runs stable.

---

## MVP Status Summary

| Phase | Status | Notes |
|-------|--------|-------|
| Phase 0: Infrastructure | ✅ Complete | Docker Compose working |
| Phase 1: Backend Core | ✅ Complete | All entities, repos, services |
| Phase 2: Agent Layer | ✅ Complete | All tools, conversation context |
| Phase 3: Frontend | ✅ Complete | Auth, chat, onboarding, projects |
| Phase 4: Integration | ✅ Complete | Error handling, security |
| Phase 5: Deploy | ⏳ Pending | Ready for deployment |

---

## Priorities for First Iteration

**Must have (don't launch without):** ✅ ALL DONE
1. ✅ Chat with agent works
2. ✅ Create/search knowledge
3. ✅ Create/view tasks
4. ✅ Project switching
5. ✅ Basic auth

**Should have (desirable):** ✅ ALL DONE
1. ✅ Semantic search
2. ✅ Knowledge connections (relations)
3. ✅ Project switching
4. ✅ Task deadlines
5. ✅ Mobile responsive

**Could have (if time permits):** ✅ ALL DONE
1. ✅ Task decomposition
2. ✅ Confidence scores
3. ✅ Onboarding flow
4. [ ] Streaming responses (not implemented)

**Won't have (definitely not in MVP):**
1. MCP server
2. Team collaboration (multiple users)
3. Reminders
4. Voice input
5. Migration from other systems

---

## Checklist Before Starting

- [x] Google Cloud account created
- [ ] Billing configured
- [x] Vertex AI API enabled
- [x] Java 21 installed
- [x] Flutter SDK installed
- [x] Android SDK installed
- [x] Xcode installed (for iOS)
- [x] Docker installed
- [x] CocoaPods installed

---

## Next Step

**Current progress:** Phases 0-4 complete. MVP is feature-complete.

**Next:** Phase 5 — Deploy to Google Cloud VM with Docker Compose, Nginx, and SSL.

To run locally:
```bash
# Start databases
docker-compose up -d

# Start backend
cd backend && ./gradlew bootRun

# Start mobile (choose platform)
cd mobile && flutter run -d chrome    # Web
cd mobile && flutter run -d android   # Android
cd mobile && flutter run -d ios       # iOS
```
