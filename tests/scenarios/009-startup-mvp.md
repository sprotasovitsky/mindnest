# Test Scenario 009: Startup MVP Development

## Overview

A team of 5 (CEO Alex, CTO Roman, Designer Lisa, Backend Dev Max, Frontend Dev Yulia) builds an MVP for a food delivery app. They:
1. Define features and priorities
2. Assign tasks with deadlines
3. Track progress and blockers
4. Make technical decisions
5. Plan launch

## Complexity: Complex (5 users, technical domain)

## Prerequisites

- Docker containers running (PostgreSQL, Neo4j, Qdrant)
- Backend running on http://localhost:8080
- Clean database (or isolated test data)

## Users

| Name  | Email            | Password | Role   |
|-------|-----------------|----------|--------|
| Alex  | alex@test.com   | test123  | owner  |
| Roman | roman@test.com  | test123  | member |
| Lisa  | lisa@test.com   | test123  | member |
| Max   | max@test.com    | test123  | member |
| Yulia | yulia@test.com  | test123  | member |

## Project

| Field       | Value                          |
|-------------|--------------------------------|
| Name        | FoodRush MVP                   |

## Onboarding

```
Description: "Startup team building MVP for food delivery app. Need to track features, tasks, blockers, and technical decisions."
Answers: "1. Feature prioritization, task assignment, progress tracking, tech decisions. 2. CEO Alex, CTO Roman, Designer Lisa, Backend Max, Frontend Yulia. 3. Launch MVP on time with core features."
Confirm: "Yes, save it."
```

## Test Execution

### Phase 1: Setup

#### Step 1.1: Register users
```
POST /api/auth/register
{ "email": "alex@test.com", "password": "test123", "name": "Alex" }
{ "email": "roman@test.com", "password": "test123", "name": "Roman" }
{ "email": "lisa@test.com", "password": "test123", "name": "Lisa" }
{ "email": "max@test.com", "password": "test123", "name": "Max" }
{ "email": "yulia@test.com", "password": "test123", "name": "Yulia" }
```

#### Step 1.2: Create project
```
User: Alex
POST /api/projects { "name": "FoodRush MVP", "description": "Food delivery app MVP development" }
```

#### Step 1.3: Add team
```
User: Alex
POST /api/projects/{projectId}/members { "email": "roman@test.com" }
POST /api/projects/{projectId}/members { "email": "lisa@test.com" }
POST /api/projects/{projectId}/members { "email": "max@test.com" }
POST /api/projects/{projectId}/members { "email": "yulia@test.com" }
```

---

### Phase 2: Product Definition

#### Step 2.1: Vision and scope
```
User: Alex
Chat: "FoodRush MVP definition:
Vision: Fast food delivery app focusing on lunch orders for office workers
Target launch: March 1, 2025 (8 weeks from now)
MVP scope: Order food from restaurants, track delivery, pay online
Initial market: Moscow, 10 partner restaurants

Key metrics for launch:
- 100 completed orders in first week
- 4.0+ app store rating
- <30 min average delivery time"
Expected: Agent saves product vision
```

#### Step 2.2: Core features list
```
User: Alex
Chat: "MVP features prioritized:
P0 (Must have):
- User registration/login
- Restaurant list with menus
- Cart and checkout
- Online payment (card)
- Order tracking
- Push notifications

P1 (Should have):
- Search and filters
- Favorites
- Order history
- Ratings and reviews

P2 (Nice to have):
- Promo codes
- Loyalty points
- Schedule orders

P2 features are cut from MVP"
Expected: Agent saves feature list with priorities
```

---

### Phase 3: Technical Architecture

#### Step 3.1: Tech stack decision
```
User: Roman
Chat: "Proposed tech stack for FoodRush:
Backend: Node.js + Express + PostgreSQL
Why: Fast development, team knows it

Frontend: React Native (iOS + Android from one codebase)
Why: Cross-platform, Yulia has experience

Infra: AWS (EC2, RDS, S3)
Why: Scalable, reliable

Payments: CloudPayments SDK
Why: Russian cards supported, good docs

What do you think?"
Expected: Agent saves tech stack
```

#### Step 3.2: Max's input
```
User: Max
Chat: "I agree with Node.js but suggest we add:
- Redis for session caching
- Firebase for push notifications
- TypeScript for type safety
Also need to decide on API architecture: REST vs GraphQL"
Expected: Agent saves technical suggestions
```

#### Step 3.3: API decision
```
User: Roman
Chat: "Let's vote on API:
REST: simpler, faster to implement, team knows it
GraphQL: more flexible, but learning curve

I vote REST for MVP speed"
Expected: Agent starts vote
```

```
User: Max
Chat: "REST - let's move fast"
```

```
User: Yulia
Chat: "REST works for me"
```

```
User: Roman
Chat: "REST confirmed. We can migrate to GraphQL in v2 if needed."
Expected: Agent records decision
```

#### Step 3.4: Final architecture
```
User: Roman
Chat: "Final architecture decision:
- Backend: Node.js + TypeScript + Express
- Database: PostgreSQL + Redis
- Mobile: React Native
- Push: Firebase
- Payments: CloudPayments
- Cloud: AWS
- CI/CD: GitHub Actions

Save this as our official tech stack."
Expected: Agent saves final architecture
```

---

### Phase 4: Design Phase

#### Step 4.1: Design tasks
```
User: Lisa
Chat: "Design deliverables I'll create:
1. App wireframes (all screens) - by Jan 15
2. UI kit (colors, fonts, components) - by Jan 18
3. High-fidelity mockups - by Jan 25
4. Prototype for user testing - by Jan 28
5. Final assets export - by Feb 1

Create these as my tasks"
Expected: Agent creates 5 design tasks
```

#### Step 4.2: Brand identity
```
User: Lisa
Chat: "Brand decisions for FoodRush:
- Primary color: #FF6B35 (energetic orange)
- Secondary: #2E4057 (dark blue)
- Accent: #4CAF50 (green for success states)
- Font: Inter for UI, Montserrat for headings
- Logo: Abstract fork + clock combination
- Tagline: 'Fresh food, fast.'"
Expected: Agent saves brand guidelines
```

#### Step 4.3: Screen list
```
User: Lisa
Chat: "Screens to design:
1. Splash/Onboarding (3 slides)
2. Login/Register
3. Home (restaurant list)
4. Restaurant detail + menu
5. Dish detail
6. Cart
7. Checkout
8. Payment
9. Order tracking
10. Order history
11. Profile/Settings
12. Search/Filters

Total: 15 unique screens"
Expected: Agent saves screen list
```

---

### Phase 5: Development Planning

#### Step 5.1: Sprint planning
```
User: Roman
Chat: "Development sprints:
Sprint 1 (Jan 13-26): Foundation
- Backend: Auth, user API, restaurant API
- Frontend: Auth screens, home screen, navigation

Sprint 2 (Jan 27-Feb 9): Core Flow
- Backend: Cart, orders, payments
- Frontend: Menu, cart, checkout, payment

Sprint 3 (Feb 10-23): Polish
- Order tracking, push notifications
- Bug fixes, performance
- App store preparation

Sprint 4 (Feb 24-28): Launch prep
- Final testing
- Soft launch with beta users
- Bug fixes

Launch: March 1"
Expected: Agent saves sprint plan
```

#### Step 5.2: Backend tasks Sprint 1
```
User: Max
Chat: "My Sprint 1 tasks (deadline Jan 26):
1. Project setup (Node + TS + Express) - 1 day
2. Database schema design - 1 day
3. User authentication API (register, login, JWT) - 2 days
4. Restaurant CRUD API - 2 days
5. Menu items API - 2 days
6. API documentation (Swagger) - 1 day
7. Unit tests for auth - 1 day

Create these tasks for me"
Expected: Agent creates 7 backend tasks
```

#### Step 5.3: Frontend tasks Sprint 1
```
User: Yulia
Chat: "My Sprint 1 tasks (deadline Jan 26):
1. React Native project setup - 1 day
2. Navigation structure - 1 day
3. Auth screens (login, register) - 2 days
4. Home screen (restaurant list) - 2 days
5. API integration layer - 2 days
6. State management setup (Redux) - 1 day

Create tasks"
Expected: Agent creates 6 frontend tasks
```

---

### Phase 6: Sprint 1 Execution

#### Step 6.1: Day 1 progress
```
User: Max
Chat: "Jan 13: Project setup complete. Repo: github.com/foodrush/backend. Node 20, TypeScript 5, Express configured. First commit pushed!"
Expected: Agent logs progress
```

```
User: Yulia
Chat: "Jan 13: RN project initialized. React Native 0.73, navigation working. Repo: github.com/foodrush/mobile"
Expected: Agent logs progress
```

#### Step 6.2: Design delivery
```
User: Lisa
Chat: "Jan 15: Wireframes complete! Shared in Figma. Link: figma.com/foodrush-wireframes. Ready for review."
Expected: Agent marks task complete
```

#### Step 6.3: Blocker identified
```
User: Max
Chat: "Jan 16: Blocker! CloudPayments SDK doesn't work with Node 20. Options:
1. Downgrade to Node 18
2. Use different payment provider
3. Write custom integration

Need Roman's decision"
Expected: Agent logs blocker
```

#### Step 6.4: Blocker resolution
```
User: Roman
Chat: "Let's go with option 1 - downgrade to Node 18. It's LTS and stable. Max, please update. Lower priority than rewriting payment integration."
Expected: Agent records decision, blocker resolved
```

```
User: Max
Chat: "Jan 16: Downgraded to Node 18. CloudPayments SDK works now. Blocker resolved!"
Expected: Agent updates blocker status
```

#### Step 6.5: Mid-sprint check
```
User: Roman
Chat: "Jan 20 standup summary:
- Max: Auth API done, working on restaurants
- Yulia: Auth screens done, starting home screen
- Lisa: UI kit delivered, working on mockups
All on track!"
Expected: Agent logs standup
```

#### Step 6.6: Sprint 1 complete
```
User: Roman
Chat: "Jan 26: Sprint 1 complete!
Delivered:
✓ Backend auth + restaurant + menu APIs
✓ Frontend auth + home screens
✓ Wireframes + UI kit
✓ API docs

Mark all Sprint 1 tasks done."
Expected: Agent marks tasks complete
```

---

### Phase 7: Sprint 2 Execution

#### Step 7.1: Sprint 2 tasks
```
User: Max
Chat: "Sprint 2 backend tasks (deadline Feb 9):
1. Cart API (add/remove/update items)
2. Order creation API
3. Payment integration with CloudPayments
4. Order status webhooks
5. Admin panel for restaurants

Create tasks"
Expected: Agent creates tasks
```

```
User: Yulia
Chat: "Sprint 2 frontend tasks:
1. Restaurant detail screen
2. Menu/dish screens
3. Cart screen
4. Checkout flow
5. Payment screen integration
6. Order confirmation screen

Create tasks"
Expected: Agent creates tasks
```

#### Step 7.2: Technical issue
```
User: Yulia
Chat: "Feb 3: Issue with payment screen - CloudPayments React Native SDK is buggy on Android. Testing fails 30% of time."
Expected: Agent logs issue
```

```
User: Max
Chat: "Feb 3: Let's use WebView for payment instead of native SDK. More reliable, still good UX. I'll create payment web page."
Expected: Agent records solution
```

```
User: Yulia
Chat: "Feb 5: WebView payment working! Tested on both iOS and Android. Issue resolved."
Expected: Agent updates issue status
```

#### Step 7.3: Sprint 2 review
```
User: Alex
Chat: "Feb 9: Sprint 2 demo went well! Core ordering flow works end-to-end. Found some UX issues:
1. Cart total doesn't update immediately
2. Payment loading state unclear
3. Order confirmation needs more detail

Not blockers but should fix in Sprint 3"
Expected: Agent logs feedback
```

---

### Phase 8: Sprint 3 - Polish

#### Step 8.1: Bug tracking
```
User: Roman
Chat: "Bug list from testing:
1. HIGH: Cart total calculation wrong with discounts
2. HIGH: Push notifications not received on iOS
3. MEDIUM: Restaurant images slow to load
4. MEDIUM: Keyboard covers input on checkout
5. LOW: Animation jank on restaurant list scroll
6. LOW: Dark mode colors wrong

Assign: 1,3,5 to Max, 2,4,6 to Yulia"
Expected: Agent creates bug tasks with priority and assignment
```

#### Step 8.2: Bug fixes
```
User: Max
Chat: "Feb 15: Fixed bugs #1 (cart calculation), #3 (image caching added). #5 still investigating."
Expected: Agent updates bug status
```

```
User: Yulia
Chat: "Feb 16: Fixed #2 (iOS push - was missing entitlement), #4 (keyboard avoiding view). #6 done too."
Expected: Agent updates bug status
```

```
User: Max
Chat: "Feb 18: Bug #5 fixed - was re-rendering entire list. All my bugs done!"
Expected: Agent marks all bugs resolved
```

#### Step 8.3: Performance metrics
```
User: Roman
Chat: "Performance testing results:
- App launch: 2.1s (target: <3s) ✓
- Restaurant list load: 0.8s ✓
- Order placement: 1.2s ✓
- Payment: 2.5s ✓

All within targets!"
Expected: Agent saves metrics
```

---

### Phase 9: Launch Preparation

#### Step 9.1: App store prep
```
User: Lisa
Chat: "App store assets ready:
- App icon (all sizes)
- Screenshots (6 for each platform)
- Feature graphic
- App description (short + full)
- Keywords for ASO

Uploading to App Store Connect and Google Play Console"
Expected: Agent logs preparation
```

#### Step 9.2: Beta testing
```
User: Alex
Chat: "Beta test results (50 users, Feb 24-28):
- 127 orders placed
- 3 critical bugs found (all fixed)
- NPS score: 42
- Average order: 850 rubles
- Main complaint: delivery time estimates inaccurate

Good enough for launch with known issues"
Expected: Agent saves test results
```

#### Step 9.3: Launch checklist
```
User: Roman
Chat: "Launch checklist for March 1:
- [ ] App store approval received
- [ ] Production servers scaled
- [ ] Payment gateway live mode
- [ ] Push notification certificates
- [ ] Analytics tracking verified
- [ ] Error monitoring (Sentry) active
- [ ] Restaurant partners notified
- [ ] Customer support ready
- [ ] Marketing materials ready
- [ ] Social media posts scheduled"
Expected: Agent creates launch checklist
```

#### Step 9.4: Checklist completion
```
User: Roman
Chat: "Feb 28: All checklist items done! Mark all as complete. Ready for launch tomorrow!"
Expected: Agent marks all items done
```

---

### Phase 10: Launch Day

#### Step 10.1: Launch announcement
```
User: Alex
Chat: "March 1, 10:00 AM: FoodRush is LIVE! 🚀
- iOS: App Store approved and published
- Android: Google Play approved and published
- 10 restaurant partners active
- Marketing campaign started

Let's monitor closely today."
Expected: Agent logs launch
```

#### Step 10.2: Day 1 metrics
```
User: Alex
Chat: "March 1 EOD metrics:
- Downloads: 847 (target: 500) ✓
- Registrations: 412
- Orders: 89
- Revenue: 76,500 rubles
- Avg order: 860 rubles
- Issues: 2 payment failures (investigating)

Great first day!"
Expected: Agent saves metrics
```

#### Step 10.3: Week 1 review
```
User: Alex
Chat: "Week 1 results:
- Downloads: 3,200
- Active users: 890
- Orders: 312 (target: 100) ✓✓✓
- Revenue: 265,000 rubles
- App Store rating: 4.3 ✓
- Play Store rating: 4.1 ✓
- Avg delivery time: 28 min ✓

All targets exceeded! MVP is a success!"
Expected: Agent saves week 1 results
```

#### Step 10.4: Lessons learned
```
User: Roman
Chat: "Technical lessons learned for future:
1. Always check SDK compatibility before choosing
2. WebView fallback for unreliable native SDKs
3. Beta testing catches issues that QA misses
4. Performance budget should be defined early
5. Push notifications are tricky on iOS - test early

Save for future reference"
Expected: Agent saves lessons
```

#### Step 10.5: Next phase planning
```
User: Alex
Chat: "V1.1 features to prioritize based on user feedback:
1. More accurate delivery estimates
2. Order scheduling
3. Promo codes (restaurants asking)
4. More payment options (SBP, Apple Pay)
5. Expand to 20 more restaurants

Start planning next sprint!"
Expected: Agent saves v1.1 roadmap
```

---

## Verification Queries

### Neo4j Checks
```cypher
// All features
MATCH (k:KnowledgeItem {projectId: '<project_id>'})
WHERE k.content CONTAINS 'P0' OR k.content CONTAINS 'P1' OR k.content CONTAINS 'feature'
RETURN k.content;

// Technical decisions
MATCH (k:KnowledgeItem {projectId: '<project_id>'})
WHERE k.content CONTAINS 'decided' OR k.content CONTAINS 'tech stack' OR k.content CONTAINS 'architecture'
RETURN k.content;

// Tasks by person
MATCH (k:KnowledgeItem {projectId: '<project_id>', type: 'TASK'})
RETURN k.content, k.status, k.ownerId;

// Bugs
MATCH (k:KnowledgeItem {projectId: '<project_id>'})
WHERE k.content CONTAINS 'bug' OR k.content CONTAINS 'issue' OR k.content CONTAINS 'blocker'
RETURN k.content;

// Metrics
MATCH (k:KnowledgeItem {projectId: '<project_id>'})
WHERE k.content CONTAINS 'metric' OR k.content CONTAINS 'target' OR k.content CONTAINS 'result'
RETURN k.content;
```

---

## Expected Data Summary

After successful test:
- 5 users with different roles
- 1 project
- Product vision and feature list
- Technical architecture decisions
- Design deliverables tracked
- Sprint plans (4 sprints)
- 20+ development tasks
- 6 bugs tracked and resolved
- Blockers logged and resolved
- Performance metrics
- Launch checklist
- Post-launch metrics
- Lessons learned

---

## Key Test Points

1. **Role-based work**: Different team members have different responsibilities
2. **Technical decisions**: Record architecture choices with rationale
3. **Sprint tracking**: Tasks organized by sprint with deadlines
4. **Blocker management**: Identify, discuss, resolve blockers
5. **Bug tracking**: Priority levels, assignment, resolution
6. **Metrics logging**: Track KPIs before and after launch
7. **Decision history**: Can trace back why choices were made

---

## Cleanup

```sql
DELETE FROM users WHERE email IN ('alex@test.com', 'roman@test.com', 'lisa@test.com', 'max@test.com', 'yulia@test.com');
```

```cypher
MATCH (k:KnowledgeItem {projectId: '<project_id>'})
DETACH DELETE k;
```
