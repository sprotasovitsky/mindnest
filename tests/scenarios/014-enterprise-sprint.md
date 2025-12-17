# Test Scenario 014: Enterprise Sprint - High Volume Stress Test

## Overview

A development team of 6 people runs a 4-week sprint on a complex e-commerce project. This scenario tests:
- **High volume data**: 200+ items across categories (tasks, decisions, notes, facts)
- **Performance under load**: Search, update, delete in large dataset
- **Multi-user concurrent work**: 6 users with different responsibilities
- **Graph relations**: Complex item relationships
- **Edge cases**: Long content, special characters, rapid operations
- **Data integrity**: No duplicates, correct updates, clean deletes

## Complexity: Very High (6 users, 200+ items, 10 phases)

## Key Testing Focus
- System handles 200+ knowledge items per project
- Search returns relevant results quickly (<3s)
- Updates don't create duplicates
- Deletes are clean (no orphans)
- Graph relations work at scale
- Long text content is handled
- Special characters preserved

## Prerequisites

- Docker containers running
- Backend running on http://localhost:8080
- Clean database
- **NOTE**: This test takes 15-20 minutes to execute fully

## Users

| Name    | Role              | Email             | Password |
|---------|-------------------|-------------------|----------|
| Alexei  | Tech Lead         | alexei@test.com   | test123  |
| Marina  | Product Manager   | marina@test.com   | test123  |
| Pavel   | Backend Dev       | pavel@test.com    | test123  |
| Yana    | Frontend Dev      | yana@test.com     | test123  |
| Dmitry  | QA Engineer       | dmitry@test.com   | test123  |
| Olga    | Designer          | olga@test.com     | test123  |

## Test Execution

### Phase 1: Setup

#### Step 1.1: Register all users
```
POST /api/auth/register for all 6 users:
{ "email": "alexei@test.com", "password": "test123", "name": "Alexei" }
{ "email": "marina@test.com", "password": "test123", "name": "Marina" }
{ "email": "pavel@test.com", "password": "test123", "name": "Pavel" }
{ "email": "yana@test.com", "password": "test123", "name": "Yana" }
{ "email": "dmitry@test.com", "password": "test123", "name": "Dmitry" }
{ "email": "olga@test.com", "password": "test123", "name": "Olga" }
```

#### Step 1.2: Create project
```
User: Alexei
POST /api/projects { "name": "E-Commerce Platform Sprint", "description": "4-week sprint for online store MVP" }
Add all members
```

---

### Phase 2: Sprint Planning (Week 1, Day 1)

#### Step 2.1: Project overview
```
User: Marina
Chat: "Sprint planning for E-Commerce Platform. Key information:

Project: Online store for electronics retailer 'TechZone'
Client: ООО 'ТехЗона' (contract #2025-EC-047)
Budget: 2,500,000 rubles
Deadline: February 28, 2025
Sprint duration: 4 weeks (Feb 1-28)

Team allocation:
- Alexei: Tech Lead, architecture decisions, code review
- Marina: PM, client communication, requirements
- Pavel: Backend (Java, Spring Boot, PostgreSQL)
- Yana: Frontend (React, TypeScript, Next.js)
- Dmitry: QA, testing, documentation
- Olga: UI/UX design, assets

MVP scope:
1. Product catalog with categories
2. Shopping cart
3. User authentication
4. Order placement
5. Admin panel (basic)
6. Payment integration (later phase)"
Expected: Agent saves comprehensive project overview
```

#### Step 2.2: Technical architecture
```
User: Alexei
Chat: "Technical stack decision:

Backend:
- Java 21 + Spring Boot 3.2
- PostgreSQL 16 for main data
- Redis for sessions and cache
- Elasticsearch for product search
- MinIO for product images

Frontend:
- Next.js 14 with App Router
- TypeScript strict mode
- Tailwind CSS + Shadcn/ui
- React Query for data fetching
- Zustand for state management

Infrastructure:
- Docker Compose for local dev
- GitHub Actions for CI/CD
- Kubernetes for production (later)
- CloudFlare for CDN

API design:
- REST for CRUD operations
- GraphQL for complex product queries (later consideration)
- OpenAPI 3.0 documentation

Save this as our technical architecture document."
Expected: Agent saves architecture
```

#### Step 2.3: Initial backlog creation
```
User: Marina
Chat: "Sprint backlog - User Stories:

US-001: As a customer, I want to browse products by category
US-002: As a customer, I want to search products by name
US-003: As a customer, I want to view product details with images
US-004: As a customer, I want to add products to cart
US-005: As a customer, I want to modify cart quantities
US-006: As a customer, I want to register an account
US-007: As a customer, I want to log in to my account
US-008: As a customer, I want to place an order
US-009: As a customer, I want to view my order history
US-010: As an admin, I want to add new products
US-011: As an admin, I want to edit product information
US-012: As an admin, I want to manage categories
US-013: As an admin, I want to view all orders
US-014: As an admin, I want to update order status
US-015: As a customer, I want to filter products by price

Save all user stories."
Expected: Agent saves all 15 user stories
```

---

### Phase 3: Week 1 Sprint Work

#### Step 3.1: Backend tasks breakdown
```
User: Pavel
Chat: "Backend tasks for sprint:

T-BE-001: Setup Spring Boot project with dependencies [4h]
T-BE-002: Create Product entity and repository [3h]
T-BE-003: Create Category entity and repository [2h]
T-BE-004: Implement product CRUD API [6h]
T-BE-005: Implement category management API [4h]
T-BE-006: Setup PostgreSQL with Flyway migrations [3h]
T-BE-007: Implement product search with Elasticsearch [8h]
T-BE-008: Create User entity and authentication [6h]
T-BE-009: Implement JWT token authentication [4h]
T-BE-010: Create Cart entity and logic [5h]
T-BE-011: Implement cart API endpoints [4h]
T-BE-012: Create Order entity and workflow [6h]
T-BE-013: Implement order placement API [5h]
T-BE-014: Setup MinIO for image storage [3h]
T-BE-015: Implement product image upload [4h]
T-BE-016: Create admin endpoints for products [4h]
T-BE-017: Create admin endpoints for orders [4h]
T-BE-018: Implement price filter in search [3h]
T-BE-019: Add pagination to all list endpoints [3h]
T-BE-020: Setup Redis for session caching [4h]

Total estimate: 85 hours
Assigned to: Pavel"
Expected: Agent saves all 20 backend tasks
```

#### Step 3.2: Frontend tasks breakdown
```
User: Yana
Chat: "Frontend tasks for sprint:

T-FE-001: Setup Next.js project with TypeScript [3h]
T-FE-002: Configure Tailwind and Shadcn/ui [2h]
T-FE-003: Create layout components (Header, Footer, Nav) [4h]
T-FE-004: Implement product catalog page [6h]
T-FE-005: Create product card component [3h]
T-FE-006: Implement category navigation [4h]
T-FE-007: Create product detail page [5h]
T-FE-008: Implement image gallery component [4h]
T-FE-009: Create shopping cart drawer/page [6h]
T-FE-010: Implement cart item component [3h]
T-FE-011: Create quantity selector component [2h]
T-FE-012: Implement registration form [4h]
T-FE-013: Implement login form [3h]
T-FE-014: Create user profile page [4h]
T-FE-015: Implement order history page [5h]
T-FE-016: Create checkout flow (3 steps) [8h]
T-FE-017: Implement order confirmation page [3h]
T-FE-018: Create search component with filters [5h]
T-FE-019: Implement price range slider [3h]
T-FE-020: Setup React Query for API calls [3h]
T-FE-021: Create admin dashboard layout [4h]
T-FE-022: Implement product management table [5h]
T-FE-023: Create product form (add/edit) [5h]
T-FE-024: Implement order management table [4h]
T-FE-025: Create category management page [4h]

Total estimate: 102 hours
Assigned to: Yana"
Expected: Agent saves all 25 frontend tasks
```

#### Step 3.3: QA tasks breakdown
```
User: Dmitry
Chat: "QA tasks for sprint:

T-QA-001: Create test plan document [4h]
T-QA-002: Setup Playwright for E2E tests [3h]
T-QA-003: Write tests for product catalog [4h]
T-QA-004: Write tests for product detail page [3h]
T-QA-005: Write tests for cart operations [5h]
T-QA-006: Write tests for checkout flow [6h]
T-QA-007: Write tests for user registration [3h]
T-QA-008: Write tests for user login [3h]
T-QA-009: Write tests for admin product CRUD [5h]
T-QA-010: Write tests for admin orders [4h]
T-QA-011: Performance testing setup (k6) [4h]
T-QA-012: Load test for product search [4h]
T-QA-013: Security audit checklist [3h]
T-QA-014: API documentation review [3h]
T-QA-015: Create bug report templates [2h]

Total estimate: 56 hours
Assigned to: Dmitry"
Expected: Agent saves all 15 QA tasks
```

#### Step 3.4: Design tasks breakdown
```
User: Olga
Chat: "Design tasks for sprint:

T-DS-001: Create design system in Figma [6h]
T-DS-002: Design product card variants [4h]
T-DS-003: Design product detail page [5h]
T-DS-004: Design shopping cart UI [4h]
T-DS-005: Design checkout flow screens [6h]
T-DS-006: Design registration/login forms [3h]
T-DS-007: Design user profile page [3h]
T-DS-008: Design order history UI [3h]
T-DS-009: Design admin dashboard [5h]
T-DS-010: Design admin tables and forms [4h]
T-DS-011: Create icon set [3h]
T-DS-012: Design responsive breakpoints [4h]
T-DS-013: Create loading states and skeletons [3h]
T-DS-014: Design error states and empty states [3h]
T-DS-015: Prepare design handoff documentation [4h]

Total estimate: 60 hours
Assigned to: Olga"
Expected: Agent saves all 15 design tasks
```

#### Step 3.5: Task summary
```
User: Marina
Chat: "Sprint task summary:
- Backend: 20 tasks (85h) - Pavel
- Frontend: 25 tasks (102h) - Yana
- QA: 15 tasks (56h) - Dmitry
- Design: 15 tasks (60h) - Olga
- Total: 75 tasks, 303 hours

Given 4 weeks (80h per person available), we need to track carefully. What's the current status breakdown?"
Expected: Agent calculates and confirms totals
```

---

### Phase 4: Week 1 Daily Progress

#### Step 4.1: Day 1 progress
```
User: Pavel
Chat: "День 1 завершён:
✓ T-BE-001: Setup Spring Boot project - DONE
✓ T-BE-006: PostgreSQL + Flyway - DONE
В процессе: T-BE-002 (Product entity)"
Expected: Agent marks tasks complete
Intent: COMPLETE (x2)
```

```
User: Yana
Chat: "День 1:
✓ T-FE-001: Next.js setup - готово
✓ T-FE-002: Tailwind + Shadcn - готово
Начала T-FE-003 (Layout)"
Expected: Agent marks tasks complete
Intent: COMPLETE (x2)
```

```
User: Olga
Chat: "День 1:
✓ T-DS-001: Design system в Figma создан
Цвета:
- Primary: #2563EB (blue-600)
- Secondary: #10B981 (emerald-500)
- Error: #EF4444 (red-500)
- Background: #F8FAFC
- Text: #1E293B
Типография: Inter для UI, Playfair Display для заголовков"
Expected: Agent saves design system details
Intent: COMPLETE (x1), SAVE
```

#### Step 4.2: Day 2 progress
```
User: Pavel
Chat: "День 2:
✓ T-BE-002: Product entity готов
✓ T-BE-003: Category entity готов

Модель Product:
- id (UUID)
- name (String, max 200)
- description (Text)
- price (BigDecimal)
- categoryId (UUID FK)
- imageUrls (List<String>)
- stock (Integer)
- sku (String unique)
- createdAt, updatedAt

Модель Category:
- id (UUID)
- name (String, max 100)
- slug (String unique)
- parentId (UUID nullable - для подкатегорий)
- imageUrl (String)"
Expected: Agent saves data models, marks complete
```

```
User: Dmitry
Chat: "День 2:
✓ T-QA-001: Тест план готов
- 5 test suites: Catalog, Cart, Auth, Checkout, Admin
- Priority levels: P0 (critical), P1 (high), P2 (medium)
- Total planned: 47 E2E tests
Начинаю T-QA-002 (Playwright setup)"
Expected: Agent marks complete, saves test plan info
```

#### Step 4.3: Day 3-5 summary
```
User: Marina
Chat: "Статус конца недели 1:

Pavel (Backend):
✓ T-BE-001, T-BE-002, T-BE-003, T-BE-004, T-BE-005, T-BE-006
В работе: T-BE-007 (Elasticsearch - 50%)
Блокер: нет

Yana (Frontend):
✓ T-FE-001, T-FE-002, T-FE-003, T-FE-004
В работе: T-FE-005, T-FE-006
Блокер: ждёт финальные макеты от Olga

Dmitry (QA):
✓ T-QA-001, T-QA-002
В работе: T-QA-003, T-QA-004
Блокер: нет

Olga (Design):
✓ T-DS-001, T-DS-002, T-DS-003, T-DS-004
В работе: T-DS-005 (checkout flow)
Блокер: нет

Итого неделя 1: 17 задач закрыто из 75 (23%)
Скорость: соответствует плану"
Expected: Agent saves weekly summary with all statuses
```

---

### Phase 5: Week 2 Development

#### Step 5.1: Technical decisions
```
User: Alexei
Chat: "Решение по архитектуре поиска:

После исследования выбираем Elasticsearch вместо PostgreSQL full-text search:
- Причина: клиент ожидает 50,000+ товаров в будущем
- PostgreSQL FTS не масштабируется выше 10k товаров эффективно
- Elasticsearch даёт: fuzzy search, faceted filters, suggest/autocomplete

Конфигурация индекса products:
- Analyzer: russian + english stemming
- Fields: name (boost 3), description (boost 1), category_name (boost 2)
- Filters: price_range, category_id, in_stock

Оценка влияния:
- Pavel: +4h на интеграцию
- Dmitry: +2h на тесты поиска
- Общий бюджет: в пределах резерва

Сохранить как архитектурное решение ADR-001."
Expected: Agent saves ADR
Intent: SAVE
```

#### Step 5.2: Bug reports start
```
User: Dmitry
Chat: "BUG-001 (P1, Backend): Product API возвращает 500 при пустом description
Шаги:
1. POST /api/products с description: null
2. Ожидание: 400 Bad Request с валидацией
3. Факт: 500 Internal Server Error
Причина: @NotNull отсутствует
Назначен: Pavel"
Expected: Agent saves bug
Intent: SAVE
```

```
User: Dmitry
Chat: "BUG-002 (P2, Frontend): Карточка товара не показывает скидку
Шаги:
1. Открыть каталог
2. Товар с oldPrice должен показывать зачёркнутую цену
3. Факт: только текущая цена видна
Назначен: Yana"
Expected: Agent saves bug
Intent: SAVE
```

```
User: Dmitry
Chat: "BUG-003 (P1, Backend): Cart не пересчитывает total при изменении quantity
Шаги:
1. Добавить товар в корзину
2. Изменить количество через PUT /api/cart/items/{id}
3. Ожидание: total обновляется
4. Факт: total остаётся прежним
Назначен: Pavel"
Expected: Agent saves bug
Intent: SAVE
```

#### Step 5.3: Bug fixes
```
User: Pavel
Chat: "BUG-001 исправлен:
- Добавил @NotBlank на description
- Добавил validation handler для 400 ответов
- Тест: ProductControllerTest.shouldReturn400WhenDescriptionEmpty
Закрыть BUG-001"
Expected: Agent marks bug fixed
Intent: COMPLETE
```

```
User: Yana
Chat: "BUG-002 исправлен:
- Добавила проверку oldPrice в ProductCard.tsx
- Стили для зачёркнутой цены
- Storybook story для скидки
Закрыть BUG-002"
Expected: Agent marks bug fixed
Intent: COMPLETE
```

#### Step 5.4: Week 2 progress
```
User: Marina
Chat: "Статус конца недели 2:

Выполнено на этой неделе:
Pavel: T-BE-007, T-BE-008, T-BE-009, T-BE-010, T-BE-011 + 2 bugfix
Yana: T-FE-005, T-FE-006, T-FE-007, T-FE-008, T-FE-009, T-FE-010 + 1 bugfix
Dmitry: T-QA-003, T-QA-004, T-QA-005 + filed 3 bugs
Olga: T-DS-005, T-DS-006, T-DS-007, T-DS-008

Всего закрыто: 35 из 75 задач (47%)
Багов найдено: 3
Багов закрыто: 2
Открыто: 1 (BUG-003)

Риск: Pavel отстаёт на 1 день по cart. Yana ждёт backend API.
Решение: параллельная работа с моками"
Expected: Agent saves weekly summary
```

---

### Phase 6: Week 2 Client Demo & Feedback

#### Step 6.1: Demo notes
```
User: Marina
Chat: "Демо для клиента 2025-02-14:

Присутствовали: Иван Смирнов (CEO TechZone), Анна Волкова (маркетинг TechZone), наша команда

Показали:
1. Каталог товаров с категориями ✓
2. Поиск по названию ✓
3. Карточка товара с изображениями ✓
4. Добавление в корзину ✓
5. Корзина с изменением количества ✓

Фидбек клиента:
+ 'Дизайн очень современный, нравится'
+ 'Поиск работает быстро'
- 'Хотим фильтр по бренду (новое требование!)'
- 'Нужны отзывы на товары (новое требование!)'
- 'Корзина должна сохраняться для незарегистрированных'

Решение команды:
- Фильтр по бренду: добавляем в scope (Pavel +6h, Yana +4h)
- Отзывы: переносим на Phase 2 (после MVP)
- Guest cart: добавляем (Pavel +3h, Yana +2h)"
Expected: Agent saves demo notes with decisions
```

#### Step 6.2: Scope change
```
User: Marina
Chat: "CHANGE REQUEST CR-001:
- Описание: Добавить фильтр по бренду
- Причина: Запрос клиента на демо
- Влияние: +6h backend, +4h frontend
- Решение: Approved, укладываемся в буфер

Новые задачи:
T-BE-021: Add brand field to Product [2h] - Pavel
T-BE-022: Implement brand filter in search [4h] - Pavel
T-FE-026: Add brand filter UI [4h] - Yana"
Expected: Agent saves change request and new tasks
```

#### Step 6.3: Guest cart decision
```
User: Alexei
Chat: "ADR-002: Guest Cart Implementation

Проблема: Незарегистрированные пользователи теряют корзину при закрытии браузера

Варианты:
A) LocalStorage - простое, но не синхронизируется между устройствами
B) Cookie + Server-side - сложнее, но надёжнее
C) LocalStorage + merge при регистрации - компромисс

Решение: Вариант C
- Корзина хранится в localStorage
- При логине/регистрации мержится с серверной
- Конфликты: серверная корзина приоритетнее

Задачи:
T-BE-023: Cart merge API endpoint [3h] - Pavel
T-FE-027: LocalStorage cart implementation [2h] - Yana

Сохранить как ADR-002."
Expected: Agent saves ADR
```

---

### Phase 7: Week 3 Integration

#### Step 7.1: API integration issues
```
User: Yana
Chat: "ISSUE-001: API contract mismatch

Backend возвращает:
{
  'products': [...],
  'totalCount': 100,
  'page': 1
}

Frontend ожидает:
{
  'data': [...],
  'meta': { 'total': 100, 'page': 1 }
}

Нужно синхронизировать. @Alexei какой формат правильный?"
Expected: Agent saves issue
Intent: SAVE
```

```
User: Alexei
Chat: "По ISSUE-001: используем стандарт JSON:API для пагинации.

Финальный формат:
{
  'data': [...],
  'meta': {
    'total': 100,
    'page': 1,
    'perPage': 20,
    'totalPages': 5
  }
}

Pavel: обнови все list endpoints
Yana: обнови типы и fetchers

Закрываем ISSUE-001."
Expected: Agent saves decision, marks issue resolved
```

#### Step 7.2: More bugs
```
User: Dmitry
Chat: "Новые баги недели 3:

BUG-004 (P0, Critical): Checkout падает при пустой корзине
- Шаги: POST /api/orders с пустым cartItems
- Ожидание: 400 с ошибкой 'Cart is empty'
- Факт: NullPointerException, 500 error
Назначен: Pavel, СРОЧНО

BUG-005 (P1): Поиск не находит товары с буквой Ё
- Запрос 'ёлка' не находит 'Ёлочные украшения'
- Причина: Elasticsearch не нормализует ё/е
Назначен: Pavel

BUG-006 (P2): Изображения загружаются медленно
- Время загрузки карточки: 3-4 секунды
- Причина: нет lazy loading, большие изображения
Назначен: Yana"
Expected: Agent saves all 3 bugs
```

```
User: Pavel
Chat: "BUG-004 исправлен срочно:
- Добавил проверку cartItems.isEmpty() в OrderService
- Unit test для пустой корзины
- Integration test для checkout flow
Закрыть BUG-004"
Expected: Agent marks critical bug fixed
```

```
User: Pavel
Chat: "BUG-005 исправлен:
- Добавил ICU Analysis plugin в Elasticsearch
- Конфиг: 'nfkc_cf' normalizer для русского
- Теперь ё = е при поиске
Закрыть BUG-005"
Expected: Agent marks bug fixed
```

#### Step 7.3: Week 3 summary
```
User: Marina
Chat: "Статус конца недели 3:

Выполнено:
- Backend: 18/23 задач (включая новые CR-001)
- Frontend: 21/27 задач (включая новые)
- QA: 11/15 задач
- Design: 14/15 задач

Баги: 6 найдено, 5 закрыто, 1 открыт (BUG-006)

Проблемы:
1. BUG-006 (медленные изображения) - нужен CloudFlare CDN
2. Checkout flow ещё не полностью протестирован
3. Admin panel 60% готовности

Решение: фокус недели 4 на завершении и стабилизации"
Expected: Agent saves summary
```

---

### Phase 8: Week 4 Final Sprint

#### Step 8.1: Daily standup format
```
User: Alexei
Chat: "Неделя 4 - режим завершения. Ежедневные standups:

День 1 (понедельник):
Pavel: T-BE-015, T-BE-016 done. Working on T-BE-017
Yana: T-FE-016 (checkout) 80% done. Blocked by payment mock
Dmitry: Running full regression suite
Olga: Final assets handoff complete

День 2:
Pavel: T-BE-017 done. Starting T-BE-018
Yana: Checkout done! Moving to admin (T-FE-21-23)
Dmitry: 12 tests passing, 3 flaky tests fixing
Olga: Documentation done

День 3:
Pavel: T-BE-018, T-BE-019 done. Last task T-BE-020
Yana: Admin dashboard done. Product forms in progress
Dmitry: All 47 tests green! Performance testing started
Olga: Supporting Yana with admin UI tweaks

День 4:
Pavel: ALL BACKEND TASKS COMPLETE
Yana: T-FE-22, T-FE-23 done. T-FE-24, T-FE-25 remaining
Dmitry: Load test results: 500 concurrent users OK, 1000 needs optimization
Olga: Done, helping with documentation

День 5 (пятница):
Yana: ALL FRONTEND TASKS COMPLETE
Dmitry: ALL QA TASKS COMPLETE
Full system test: PASS
Ready for release!

Сохранить историю standups."
Expected: Agent saves full standup history
```

#### Step 8.2: Performance test results
```
User: Dmitry
Chat: "Performance test results (k6):

Test 1: Product catalog load
- 100 concurrent users: avg 120ms, p95 250ms ✓
- 500 concurrent users: avg 180ms, p95 400ms ✓
- 1000 concurrent users: avg 450ms, p95 1200ms ⚠️

Test 2: Product search
- Simple query: avg 80ms ✓
- Complex filters: avg 150ms ✓
- Fuzzy search: avg 200ms ✓

Test 3: Checkout flow
- Cart operations: avg 50ms ✓
- Order placement: avg 200ms ✓
- Concurrent orders (100): no race conditions ✓

Test 4: Admin operations
- Product CRUD: avg 100ms ✓
- Order list (1000 orders): avg 300ms ✓

Recommendations:
1. Enable Redis caching for catalog (done)
2. Add database connection pooling (done)
3. Consider CDN for images (TODO for prod)

Save performance baseline for future comparison."
Expected: Agent saves performance results
```

#### Step 8.3: Final bug triage
```
User: Dmitry
Chat: "Финальный баг-трекинг:

Закрыто в спринте: 8 багов
Открыто: 2 бага (оба P3, non-blocking)

BUG-007 (P3): Footer links не работают на мобильном
- Workaround: используйте десктоп версию
- Fix in next sprint

BUG-008 (P3): Админка не сохраняет draft товара
- Workaround: заполнять все поля сразу
- Fix in next sprint

MVP GO/NO-GO: GO
Критических багов: 0
High priority багов: 0
Regression tests: 47/47 passing"
Expected: Agent saves final bug status
```

---

### Phase 9: Sprint Retrospective

#### Step 9.1: What went well
```
User: Marina
Chat: "Sprint Retrospective - What went well:

1. Alexei: 'Архитектурные решения приняты быстро, ADR документация помогла'
2. Pavel: 'Elasticsearch интеграция прошла гладко, хорошая документация'
3. Yana: 'Shadcn/ui сэкономил кучу времени на компонентах'
4. Dmitry: 'Playwright E2E тесты очень стабильные, поймали 8 багов до релиза'
5. Olga: 'Figma handoff процесс работает отлично, почти не было вопросов'
6. Marina: 'Клиент доволен промежуточными демо, меньше сюрпризов'"
Expected: Agent saves positive feedback
```

#### Step 9.2: What could be improved
```
User: Marina
Chat: "Sprint Retrospective - What to improve:

1. Alexei: 'Code review bottleneck в середине спринта - нужно распределить'
2. Pavel: 'API контракты нужно фиксировать раньше (ISSUE-001 был болезненным)'
3. Yana: 'Больше парного программирования на сложных фичах'
4. Dmitry: 'Тесты писать параллельно с разработкой, не после'
5. Olga: 'Дизайн для мобильных нужно делать первым, не последним'
6. Marina: 'Scope changes (CR-001) добавлять через формальный процесс'"
Expected: Agent saves improvement areas
```

#### Step 9.3: Action items
```
User: Marina
Chat: "Retrospective Action Items:

AI-001: Внедрить API-first подход с OpenAPI specs - Alexei, Pavel
AI-002: Добавить второго code reviewer - распределить Alexei + Pavel
AI-003: Mobile-first дизайн в следующем спринте - Olga
AI-004: TDD для критичных модулей - Pavel, Yana
AI-005: Формализовать Change Request процесс - Marina

Все action items занести как задачи для следующего спринта."
Expected: Agent creates tasks from action items
Intent: TASK (x5)
```

---

### Phase 10: Project Metrics & Knowledge Base

#### Step 10.1: Sprint metrics
```
User: Marina
Chat: "Финальные метрики спринта:

Время:
- Запланировано: 303 часа
- Фактически: 318 часов (+5%)
- Причина превышения: CR-001 scope change

Задачи:
- Запланировано: 75
- Добавлено: 5 (CR-001, guest cart)
- Выполнено: 80
- Completion rate: 100%

Качество:
- Баги найдено: 8
- Баги закрыто: 6
- Баги в бэклоге: 2 (P3)
- Test coverage: 78%
- E2E tests: 47

Velocity:
- Story points planned: 89
- Story points completed: 89
- Velocity: 22.25 points/week

Client satisfaction: 9/10 (по результатам демо)"
Expected: Agent saves final metrics
```

#### Step 10.2: Knowledge base articles
```
User: Alexei
Chat: "Создать статьи в базе знаний:

KB-001: Elasticsearch конфигурация для русского языка
- ICU plugin обязателен
- nfkc_cf normalizer для ё/е
- Boosting: name x3, description x1, category x2

KB-002: Стек проекта TechZone
- Backend: Java 21, Spring Boot 3.2, PostgreSQL 16
- Frontend: Next.js 14, TypeScript, Tailwind
- Search: Elasticsearch 8.x
- Cache: Redis 7.x
- Storage: MinIO

KB-003: Пагинация API
- Формат JSON:API
- meta: total, page, perPage, totalPages
- Дефолт: 20 items per page

Сохранить все статьи."
Expected: Agent saves KB articles
Intent: SAVE (x3)
```

#### Step 10.3: Team learnings
```
User: Alexei
Chat: "Технические уроки спринта:

1. Elasticsearch vs PostgreSQL FTS:
   - До 10k записей: PostgreSQL достаточно
   - Больше 10k: Elasticsearch оправдан
   - Fuzzy search: только Elasticsearch

2. Next.js App Router:
   - Server Components по умолчанию
   - 'use client' только где нужно
   - Caching сложный, документировать

3. Tailwind + Shadcn:
   - Быстрый старт
   - Кастомизация через CSS variables
   - Избегать !important

4. Jest vs Playwright:
   - Unit tests: Jest/Vitest
   - Integration: Testing Library
   - E2E: Playwright (стабильнее Cypress)

5. Redis caching patterns:
   - Cache-aside для каталога
   - Write-through для корзины
   - TTL: 5min для списков, 1h для деталей

Сохранить как technical learnings."
Expected: Agent saves learnings
```

---

### Phase 11: Stress Testing (High Volume)

#### Step 11.1: Bulk data creation
```
User: Marina
Chat: "Импорт тестовых данных для нагрузочного тестирования:

Категории (10):
- Смартфоны
- Ноутбуки
- Планшеты
- Наушники
- Часы
- Телевизоры
- Камеры
- Игровые консоли
- Аксессуары
- Умный дом

Бренды (15):
Apple, Samsung, Xiaomi, Sony, LG, Huawei, Lenovo, ASUS, Dell, HP, JBL, Bose, Canon, Nikon, Nintendo

Товары: сгенерировано 500 позиций
Цены: от 990₽ до 299990₽
Рейтинги: от 3.5 до 5.0

Сохранить структуру тестовых данных."
Expected: Agent saves test data structure
```

#### Step 11.2: Create 50 expense records quickly
```
User: Dmitry
Chat: "Тест расходов на разработку (50 записей):

Январь 2025:
- 01.01: Домен techzone.ru - 1500₽
- 02.01: SSL сертификат - 3000₽
- 03.01: GitHub Team - $25 (2000₽)
- 05.01: Figma Professional - $15 (1200₽)
- 08.01: AWS credits - $100 (8000₽)
- 10.01: Лицензия IntelliJ - €599 (55000₽)
- 12.01: JetBrains All Products - €249 (23000₽)
- 15.01: Slack Business - $12.50/user x 6 (6000₽)
- 18.01: Zoom Pro - $15.99 (1300₽)
- 20.01: Notion Team - $10/user x 6 (4800₽)
- 22.01: Vercel Pro - $20 (1600₽)
- 25.01: Elasticsearch Cloud - $95 (7600₽)
- 28.01: Redis Cloud - $30 (2400₽)
- 30.01: MinIO storage - $15 (1200₽)

Февраль 2025:
- 01.02: AWS EC2 - $150 (12000₽)
- 03.02: AWS RDS - $80 (6400₽)
- 05.02: CloudFlare Pro - $20 (1600₽)
- 07.02: Sentry Business - $26 (2080₽)
- 10.02: DataDog monitoring - $15 (1200₽)
- 12.02: PagerDuty - $25 (2000₽)
- 15.02: 1Password Teams - $7.99/user x 6 (3840₽)
- 17.02: Мебель в офис - 45000₽
- 19.02: Второй монитор x 3 - 60000₽
- 21.02: Клавиатуры механические x 6 - 36000₽
- 23.02: MacBook Pro (Pavel) - 250000₽
- 25.02: MacBook Air (Yana) - 180000₽
- 27.02: Наушники Sony x 3 - 45000₽

Март 2025 (планируемые):
- Серверы production - 50000₽
- Резерв на баги - 30000₽
- Маркетинговые материалы - 25000₽
- Конференция TeamLead Conf - 15000₽ x 2
- Обучение команды - 40000₽

И ещё 20 мелких расходов по 1000-5000₽ каждый.

Сохранить все расходы."
Expected: Agent saves expense records
```

#### Step 11.3: Search in large dataset
```
User: Marina
Chat: "Поиск в большом наборе данных - тестируем:
Сколько всего потратили на AWS?"
Expected: Agent searches and aggregates AWS expenses
Intent: SEARCH
```

```
User: Marina
Chat: "Какие расходы были больше 50000 рублей?"
Expected: Agent finds high-value expenses
Intent: SEARCH
```

```
User: Marina
Chat: "Что купили для команды в феврале?"
Expected: Agent finds February team purchases
Intent: SEARCH
```

#### Step 11.4: Update in large dataset
```
User: Marina
Chat: "На самом деле MacBook для Pavel стоил 245000₽, а не 250000₽"
Expected: Agent updates specific record
Intent: UPDATE
```

```
User: Marina
Chat: "Исправь: AWS EC2 стоил $160, не $150"
Expected: Agent updates AWS record
Intent: UPDATE
```

#### Step 11.5: Delete in large dataset
```
User: Marina
Chat: "Удали запись про резерв на баги - мы решили не планировать это отдельно"
Expected: Agent deletes specific record
Intent: DELETE
```

---

### Phase 12: Graph Relations at Scale

#### Step 12.1: Create complex relations
```
User: Alexei
Chat: "Связи между элементами проекта:

1. US-001 (Product catalog) DEPENDS_ON T-BE-002 (Product entity)
2. US-001 DEPENDS_ON T-FE-004 (Catalog page)
3. US-002 (Search) DEPENDS_ON T-BE-007 (Elasticsearch)
4. T-FE-004 DEPENDS_ON T-DS-002 (Product card design)
5. ADR-001 (Search architecture) RELATES_TO US-002
6. BUG-005 (ё/е issue) RELATES_TO ADR-001

Создай все эти связи."
Expected: Agent creates 6 relations
Intent: RELATION (x6)
```

#### Step 12.2: Query relations
```
User: Marina
Chat: "Что зависит от Product entity (T-BE-002)?"
Expected: Agent finds US-001 through relation
Intent: SEARCH (uses get_related)
```

```
User: Marina
Chat: "Как связаны BUG-005 и User Story US-002?"
Expected: Agent finds path: BUG-005 -> ADR-001 -> US-002
Intent: SEARCH (uses find_path)
```

---

## Verification Queries

### Item Count Verification
```bash
# Qdrant - should have 200+ items
curl -s "http://localhost:6333/collections/knowledge_vectors/points/count" \
  -H "Content-Type: application/json" \
  -d '{"filter":{"must":[{"key":"projectId","match":{"value":"<project_id>"}}]}}'
```

### Neo4j Verification
```cypher
// Count by type
MATCH (k:KnowledgeItem {projectId: '<project_id>'})
RETURN k.type, count(*) ORDER BY count(*) DESC;

// Tasks status
MATCH (k:KnowledgeItem {projectId: '<project_id>', type: 'TASK'})
RETURN k.status, count(*);

// Relations count
MATCH (a:KnowledgeItem {projectId: '<project_id>'})-[r]->(b)
RETURN type(r), count(*);
```

### Performance Check
```bash
# Response time for search
time curl -s -X POST "http://localhost:8080/api/chat" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"projectId":"<project_id>","message":"Найди все баги"}'
```

---

## Expected Results

| Metric | Expected | Acceptable |
|--------|----------|------------|
| Total items | 200+ | 180+ |
| Tasks created | 80+ | 75+ |
| Bugs tracked | 8+ | 6+ |
| ADRs | 2+ | 2 |
| Relations | 6+ | 4+ |
| Search time (simple) | <2s | <3s |
| Search time (complex) | <3s | <5s |
| Update accuracy | 100% | 95%+ |
| Delete precision | 100% | 95%+ |

---

## Performance Baseline

| Operation | Target | Notes |
|-----------|--------|-------|
| Create item | <1s | Per item |
| Search (simple) | <2s | With 200+ items |
| Search (complex) | <3s | Aggregations |
| Update | <2s | Find + update |
| Delete | <2s | Find + delete |
| Graph query | <3s | Traversal |
| Full test run | <20min | All phases |

---

## Cleanup

```sql
DELETE FROM users WHERE email IN ('alexei@test.com', 'marina@test.com', 'pavel@test.com', 'yana@test.com', 'dmitry@test.com', 'olga@test.com');
```

```cypher
MATCH (k:KnowledgeItem {projectId: '<project_id>'})
DETACH DELETE k;
```
