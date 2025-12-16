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

## Phase 0: Infrastructure

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

## Phase 1: Backend Core

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
- [ ] `Relation` between KnowledgeItems (Neo4j)
- [x] `User` entity (PostgreSQL)
- [x] `Project` entity (PostgreSQL)
- [ ] `Conversation` entity (PostgreSQL) — schema exists, entity not yet

### 1.3 Repositories

- [x] `KnowledgeRepository` (Neo4j)
  - `findById`
  - `findByProjectId`
  - `findRelated(id, depth)`
  - `findByTypeAndStatus`
- [x] `UserRepository` (PostgreSQL)
- [x] `ProjectRepository` (PostgreSQL)

### 1.4 Vertex AI Integration

- [x] `LlmService` — Gemini calls
- [x] `EmbeddingService` — text-embedding-004
- [x] `ModelRouter` — model selection by task type
- [ ] Rate limiting / error handling — basic error handling exists

### 1.5 Vector Search

- [x] `VectorRepository` (Qdrant)
  - `upsert(id, vector, metadata)`
  - `search(vector, limit, filters)`
- [x] Integration with EmbeddingService

**Completion criteria:** API endpoints work, data persists in DB. ✅

---

## Phase 2: Agent Layer

### 2.1 Tools (Agent Functions)

- [x] **Knowledge Tools:**
  - `createKnowledge(type, content, projectId)`
  - `getKnowledge(id)`
  - `updateKnowledge(id, content)`
  - `searchKnowledge(query)` — semantic search
  - `getRelatedKnowledge(id, depth)`

- [x] **Task Tools:**
  - `createTask(title, description, deadline, projectId)`
  - `updateTaskStatus(id, status)`
  - `getTasksForToday(userId)`
  - `getTasksByStatus(status, projectId)`
  - [ ] `decomposeTask(taskId)` — break into subtasks

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
- [ ] Conversation context management
- [x] Model routing logic
- [x] Confidence score in responses
- [ ] Source attribution — placeholder exists

### 2.3 API Endpoints

- [x] `POST /api/chat` — main chat
  ```json
  Request: { "message": "...", "projectId": "..." }
  Response: { "reply": "...", "sources": [...], "confidence": 0.95 }
  ```
- [x] `GET /api/projects` — list projects
- [x] `POST /api/projects` — create project
- [ ] WebSocket for streaming responses (optional)

**Completion criteria:** Can chat with agent via API, it creates/searches knowledge and tasks. ✅

---

## Phase 3: Frontend (Flutter)

### 3.1 Flutter Scaffold

- [x] Create Flutter project
- [x] Set up structure (clean architecture)
- [x] Set up HTTP client (Dio)
- [x] Set up state management (Riverpod / Bloc)
- [x] Set up routing (go_router)

### 3.2 Auth (Simple)

- [ ] Login screen (email/password for MVP)
- [ ] Secure storage for tokens
- [ ] Auth state management
- [ ] Protected routes

### 3.3 Chat Interface

- [x] Chat screen
  - Message list (ListView)
  - Input field
  - Send button
  - Loading indicator
- [x] Message widget (markdown rendering)
- [x] Auto-scroll to new messages
- [x] Keyboard handling
- [x] Backend API integration

### 3.4 Onboarding

- [ ] Welcome screen for new users
- [ ] Agent initiates dialog
- [ ] Select/create first project

### 3.5 Project Switcher

- [ ] Drawer / Bottom sheet for projects
- [ ] Create new project

### 3.6 Platforms

- [ ] Android build + test on device
- [ ] iOS build + test on simulator
- [x] Web build + test in browser

**Completion criteria:** Can install on phone, log in, select project, chat with agent.

---

## Phase 4: Integration and Polish

### 4.1 End-to-end Scenarios

- [ ] Create project → add knowledge → create task → find connections
- [x] "What tasks do I have today?" works
- [ ] "Break down this task into subtasks" works
- [x] Semantic search finds relevant items

### 4.2 Onboarding Flow

- [ ] Agent greets new user
- [ ] Asks about role and projects
- [ ] Helps create first project

### 4.3 Error Handling

- [ ] Graceful errors in UI
- [ ] Retry logic for API calls
- [ ] Fallback if Vertex AI unavailable

### 4.4 Basic Security

- [ ] CORS configuration
- [ ] Rate limiting
- [ ] Input sanitization

**Completion criteria:** Full flow works without critical bugs.

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

## Priorities for First Iteration

**Must have (don't launch without):**
1. Chat with agent works
2. Create/search knowledge
3. Create/view tasks
4. Single project (no switching)
5. Basic auth

**Should have (desirable):**
1. Semantic search
2. Knowledge connections
3. Project switching
4. Task deadlines
5. Mobile responsive

**Could have (if time permits):**
1. Task decomposition
2. Confidence scores
3. Streaming responses
4. Onboarding flow

**Won't have (definitely not in MVP):**
1. MCP server
2. Team collaboration (multiple users)
3. Reminders
4. Voice input
5. Migration from other systems

---

## Development Order (Recommendation)

```
Week 1-2: Phase 0 + Phase 1.1-1.3
  - Infrastructure
  - Backend scaffold
  - Data models

Week 3-4: Phase 1.4-1.5 + Phase 2.1-2.2
  - Vertex AI integration
  - Tools
  - Orchestrator Agent

Week 5-6: Phase 2.3
  - API endpoints
  - WebSocket for real-time

Week 7-9: Phase 3
  - Flutter app (scaffold, auth, chat)
  - Android/iOS builds

Week 10: Phase 4 + Phase 5
  - Integration
  - Deploy
```

---

## Checklist Before Starting

- [x] Google Cloud account created
- [ ] Billing configured
- [x] Vertex AI API enabled
- [x] Java 21 installed
- [x] Flutter SDK installed
- [ ] Android Studio installed (for emulator)
- [ ] Xcode installed (for iOS simulator)
- [x] Docker installed
- [ ] IDE configured (IntelliJ for Java, VS Code for Flutter)

---

## Next Step

**Current progress:** Phase 0 complete, Phase 1.1-1.4 complete, Phase 3.1 and 3.3 partial.

**Next:** Configure Google Cloud credentials, then continue with Phase 1.5 (Vector Search) or Phase 2 (Agent Tools).
