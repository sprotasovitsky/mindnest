# MindNest MVP - План разработки

## Обзор

**Цель MVP:** Работающий прототип для тебя и жены — чат-интерфейс для управления знаниями и задачами.

**Tech Stack:**
- Frontend: Flutter + Dart (iOS, Android, Web)
- Backend: Java 21 + Spring Boot 3.2
- AI: Google Vertex AI (Gemini + Embeddings)
- Storage: Neo4j + Qdrant + PostgreSQL
- Deploy: Docker Compose на Google Cloud VM

---

## Фаза 0: Инфраструктура

### 0.1 Настройка проекта

- [x] Создать репозиторий (GitHub/GitLab)
- [x] Настроить структуру проекта:
  ```
  mindnest/
  ├── mobile/            # Flutter (iOS, Android, Web)
  ├── backend/           # Spring Boot
  ├── docker/            # Docker Compose
  └── docs/              # Документация
  ```
- [x] Настроить Docker Compose (dev environment)
- [ ] Настроить CI/CD (GitHub Actions)

### 0.2 Google Cloud

- [ ] Создать проект в Google Cloud
- [ ] Включить Vertex AI API
- [ ] Создать Service Account + ключи
- [ ] Настроить billing alerts

### 0.3 Базы данных (Docker)

- [x] Neo4j container + health check
- [x] Qdrant container + health check
- [x] PostgreSQL container + init scripts
- [x] Docker network между сервисами

**Критерий готовности:** `docker-compose up` запускает все сервисы, они доступны. ✅

---

## Фаза 1: Backend Core

### 1.1 Spring Boot каркас

- [x] Создать Spring Boot проект (Java 21, Gradle/Maven)
- [x] Настроить Virtual Threads
- [x] Подключить Spring Data Neo4j
- [x] Подключить Qdrant client
- [x] Подключить Spring Data JPA (PostgreSQL)
- [x] Базовая конфигурация (application.yml)

### 1.2 Модели данных

- [x] `KnowledgeItem` entity (Neo4j)
  ```java
  @Node
  public class KnowledgeItem {
      String id;
      KnowledgeType type;  // fact, task, decision, note, question
      String content;
      TaskStatus status;   // для tasks
      LocalDate deadline;  // для tasks
      String ownerId;
      String projectId;
      LocalDateTime createdAt;
      LocalDateTime updatedAt;
  }
  ```
- [ ] `Relation` между KnowledgeItems (Neo4j)
- [x] `User` entity (PostgreSQL)
- [x] `Project` entity (PostgreSQL)
- [ ] `Conversation` entity (PostgreSQL) — схема есть, entity нет

### 1.3 Repositories

- [x] `KnowledgeRepository` (Neo4j)
  - `findById`
  - `findByProjectId`
  - `findRelated(id, depth)`
  - `findByTypeAndStatus`
- [x] `UserRepository` (PostgreSQL)
- [x] `ProjectRepository` (PostgreSQL)

### 1.4 Vertex AI интеграция

- [x] `LlmService` — вызов Gemini
- [x] `EmbeddingService` — text-embedding-004
- [x] `ModelRouter` — выбор модели по типу задачи
- [ ] Rate limiting / error handling — базовый error handling есть

### 1.5 Vector Search

- [ ] `VectorRepository` (Qdrant)
  - `upsert(id, vector, metadata)`
  - `search(vector, limit, filters)`
- [ ] Интеграция с EmbeddingService

**Критерий готовности:** API endpoints работают, данные сохраняются в БД.

---

## Фаза 2: Agent Layer

### 2.1 Tools (функции агента)

- [ ] **Knowledge Tools:**
  - `createKnowledge(type, content, projectId)`
  - `getKnowledge(id)`
  - `updateKnowledge(id, content)`
  - `searchKnowledge(query)` — семантический поиск
  - `getRelatedKnowledge(id, depth)`

- [ ] **Task Tools:**
  - `createTask(title, description, deadline, projectId)`
  - `updateTaskStatus(id, status)`
  - `getTasksForToday(userId)`
  - `getTasksByStatus(status, projectId)`
  - `decomposeTask(taskId)` — разбить на подзадачи

- [ ] **Project Tools:**
  - `createProject(name)`
  - `getProjects(userId)`
  - `switchProject(projectId)`

- [ ] **Time Tools (программные, без LLM):**
  - `getCurrentDate()`
  - `filterByDeadline(tasks, date)`
  - `getOverdueTasks()`

### 2.2 Orchestrator Agent

- [x] System prompt (персона секретаря)
- [ ] Tool definitions для Gemini
- [ ] Conversation context management
- [x] Model routing logic
- [x] Confidence score в ответах
- [ ] Указание источников — placeholder есть

### 2.3 API Endpoints

- [x] `POST /api/chat` — основной чат
  ```json
  Request: { "message": "...", "projectId": "..." }
  Response: { "reply": "...", "sources": [...], "confidence": 0.95 }
  ```
- [ ] `GET /api/projects` — список проектов
- [ ] `POST /api/projects` — создать проект
- [ ] WebSocket для streaming responses (опционально)

**Критерий готовности:** Можно общаться с агентом через API, он создаёт/ищет знания и задачи.

---

## Фаза 3: Frontend (Flutter)

### 3.1 Flutter каркас

- [x] Создать Flutter проект
- [x] Настроить структуру (clean architecture)
- [x] Настроить HTTP client (Dio)
- [x] Настроить state management (Riverpod / Bloc)
- [x] Настроить роутинг (go_router)

### 3.2 Auth (простой)

- [ ] Login screen (email/password для MVP)
- [ ] Secure storage для токенов
- [ ] Auth state management
- [ ] Protected routes

### 3.3 Chat Interface

- [x] Chat screen
  - Message list (ListView)
  - Input field
  - Send button
  - Loading indicator
- [x] Message widget (markdown rendering)
- [x] Auto-scroll к новым сообщениям
- [x] Keyboard handling

### 3.4 Onboarding

- [ ] Welcome screen для новых пользователей
- [ ] Агент сам начинает диалог
- [ ] Выбор/создание первого проекта

### 3.5 Project Switcher

- [ ] Drawer / Bottom sheet для проектов
- [ ] Создание нового проекта

### 3.6 Платформы

- [ ] Android build + тест на устройстве
- [ ] iOS build + тест на симуляторе
- [ ] Web build + тест в браузере

**Критерий готовности:** Можно установить на телефон, зайти, выбрать проект, общаться с агентом.

---

## Фаза 4: Интеграция и Polish

### 4.1 End-to-end сценарии

- [ ] Создать проект → добавить знание → создать задачу → найти связи
- [ ] "Какие задачи на сегодня?" работает
- [ ] "Разбей задачу на подзадачи" работает
- [ ] Семантический поиск находит релевантное

### 4.2 Onboarding flow

- [ ] Агент приветствует нового пользователя
- [ ] Спрашивает про роль и проекты
- [ ] Помогает создать первый проект

### 4.3 Error handling

- [ ] Graceful errors в UI
- [ ] Retry logic для API calls
- [ ] Fallback если Vertex AI недоступен

### 4.4 Basic security

- [ ] CORS настройка
- [ ] Rate limiting
- [ ] Input sanitization

**Критерий готовности:** Полный flow работает без критических багов.

---

## Фаза 5: Deploy

### 5.1 Production setup

- [ ] Создать Compute Engine VM
- [ ] Настроить Docker Compose для prod
- [ ] Настроить Nginx (reverse proxy + SSL)
- [ ] Domain + HTTPS (Let's Encrypt)

### 5.2 Monitoring

- [ ] Cloud Logging
- [ ] Health checks
- [ ] Basic alerts

### 5.3 Backup

- [ ] Backup скрипты для Neo4j, PostgreSQL, Qdrant
- [ ] Cron job для автоматических бэкапов

**Критерий готовности:** Приложение доступно по домену, работает стабильно.

---

## Приоритеты для первой итерации

**Must have (без этого не запускаем):**
1. Чат с агентом работает
2. Создание/поиск знаний
3. Создание/просмотр задач
4. Один проект (без переключения)
5. Базовый auth

**Should have (желательно):**
1. Семантический поиск
2. Связи между знаниями
3. Переключение проектов
4. Дедлайны на задачах
5. Mobile responsive

**Could have (если останется время):**
1. Декомпозиция задач
2. Confidence scores
3. Streaming responses
4. Onboarding flow

**Won't have (точно не в MVP):**
1. MCP server
2. Командная работа (несколько пользователей)
3. Напоминания
4. Голосовой ввод
5. Миграция из других систем

---

## Порядок разработки (рекомендация)

```
Неделя 1-2: Фаза 0 + Фаза 1.1-1.3
  - Инфраструктура
  - Backend каркас
  - Модели данных

Неделя 3-4: Фаза 1.4-1.5 + Фаза 2.1-2.2
  - Vertex AI интеграция
  - Tools
  - Orchestrator Agent

Неделя 5-6: Фаза 2.3
  - API endpoints
  - WebSocket для real-time

Неделя 7-9: Фаза 3
  - Flutter app (каркас, auth, chat)
  - Android/iOS builds

Неделя 10: Фаза 4 + Фаза 5
  - Интеграция
  - Deploy
```

---

## Чек-лист перед началом

- [ ] Google Cloud account создан
- [ ] Billing настроен
- [ ] Vertex AI API включен
- [x] Java 21 установлена
- [x] Flutter SDK установлен
- [ ] Android Studio установлен (для эмулятора)
- [ ] Xcode установлен (для iOS симулятора)
- [x] Docker установлен
- [ ] IDE настроена (IntelliJ для Java, VS Code для Flutter)

---

## Следующий шаг

**Текущий прогресс:** Фаза 0 завершена, Фаза 1.1-1.4 завершена, Фаза 3.1 и 3.3 частично.

**Следующее:** Настроить Google Cloud credentials, затем продолжить с Фазой 1.5 (Vector Search) или Фазой 2 (Agent Tools).
