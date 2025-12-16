# MindNest - Project Vision

## Main Goal

Create an **AI-first platform** for knowledge and task management through a **chat interface**, where each user works through their personal agent — like having a secretary who instantly finds any information and manages your affairs.

**Metaphor:** Confluence + Jira, but AI-first and through chat. A secretary who uses these systems very quickly on your behalf.

---

## IMPORTANT: Fundamental Principles

### 1. Knowledge, Not Documents

**MindNest is a knowledge graph, not a document editor.**

- We **DO NOT compete** with Google Docs, Notion as an editor
- A document is just a container for knowledge on input/output
- Inside we store **knowledge structure and connections**, not formatted text
- On output we can generate any document from knowledge when needed

```
Google Docs: editor → formatting → document
MindNest:    knowledge → connection graph → document (when needed)
```

**Example:**
```
Input: Google Doc with meeting notes
      ↓
MindNest: extracts knowledge, decisions, tasks, questions
          builds connections with existing knowledge
      ↓
Output: "Generate a report for management" → beautiful document
```

### 2. Passive Source Externally, Active Internally

**MindNest is the memory and brain of a team, which other agents access.**

```
┌─────────────────────────────────────────────────┐
│                 EXTERNAL WORLD                   │
│                                                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐      │
│  │ Coding   │  │ Email    │  │ Calendar │      │
│  │ Agent    │  │ Agent    │  │ Agent    │      │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘      │
│       │             │             │            │
│       └─────────────┴─────────────┘            │
│                     │                          │
│                     ↓ MCP (requests to MindNest)│
│       ┌─────────────────────────────┐          │
│       │   MindNest MCP Server       │          │
│       └─────────────────────────────┘          │
└─────────────────────────────────────────────────┘
```

| Inside MindNest | Outside |
|-----------------|---------|
| **Active**: validates, connects, creates | **Passive**: only responds to requests |
| Agents work autonomously | DOES NOT command external systems |
| Manages knowledge graph itself | Provides MCP server for others |

**We DO NOT use** MCP to connect to external systems (for now).
**We provide** an MCP server so other agents can access knowledge and intents.

**Why:**
- Simplicity — don't manage external systems
- Reliability — fewer failure points
- Clarity — MindNest = memory, other agents = hands
- Won't get confused at the start

### 3. Display — On Demand

- Primary interface — text chat
- If beautiful display needed (cards, lists) — agent will do it
- No fixed dashboards, but structured output when appropriate

```
User: Show tasks for today

Agent: [displays as cards or list — whatever is more appropriate]

       📋 Tasks for 12/15:
       ┌────────────────────────┐
       │ Configure nginx        │
       │ Deadline: today        │
       │ Related: API Design    │
       └────────────────────────┘
```

---

## Key Principles

### 1. Knowledge and Intents Over Structure
- It doesn't matter how a document looks — what matters is what knowledge is in it
- User dictates/uploads → agent extracts and saves knowledge
- Formatting and structure — on output, when needed (by other agents)

### 2. Everything Through Chat — No Dashboards
- Chat — the only interface
- No task lists, kanban boards, dashboards
- You ask → you receive. Like talking to a secretary

### 3. Everything is Connected
- Knowledge ↔ Tasks ↔ People ↔ Projects
- AI automatically builds connection graph
- Semantic search finds by meaning, not keywords

### 4. Trust Through Transparency
- **Confidence Score** — agent shows confidence in response
- **Show sources** — "According to document X (updated 2 days ago)..."
- Fighting hallucinations through explicit data references

---

## Target Audience

- **Small IT teams** (2-10 people)
- **Small businesses** (not just IT)
- **Families** with joint projects (renovation, vacation, shopping)
- Anyone who needs a simple tool for knowledge + tasks without complex UI

---

## 1. Knowledge Management

### Goal
Store and find information through conversation

### Features
- ✅ Create knowledge through chat (you dictate → agent saves)
- ✅ Upload files → agent extracts knowledge
- ✅ Organization by projects
- ✅ **Semantic search** — by meaning, not words
- ✅ **Automatic connections** — agent finds related items
- ✅ **Versioning** — change history

### Example

```
User: Here are meeting notes: [text or file]

Agent: Extracted from notes:
       - Decision: using PostgreSQL
       - Task: set up replication (@Ivan)
       - Open question: which hosting to choose?

       Saved to "Backend" project. Create task for Ivan?

... later ...

User: What did we decide about the database?

Agent: You decided to use PostgreSQL (meeting from 12/10).
       Related tasks: replication setup (in progress).
       Source: "Meeting Notes 12/10"
```

---

## 2. Task Management

### Goal
Create and track tasks through conversation

### Features
- ✅ Create tasks through description
- ✅ View tasks: "What's on me today?"
- ✅ **Deadlines** — dates on tasks
- ✅ **Automatic linking** with relevant knowledge
- ✅ Change status through chat
- ✅ **Decomposition** — break into subtasks
- ✅ Detect similar/duplicate tasks

### Example

```
User: What tasks for today?

Agent: You have 3 tasks for today:
       1. "Configure nginx" — deadline today
       2. "Code review Anna" — deadline tomorrow
       3. "Prepare presentation" — deadline Friday

       Start with nginx? There's related documentation.

User: Yes, show me what's there

Agent: Task: "Configure nginx"
       Context: need SSL (from discussion 12/08), rate limiting
       Related to: document "API Architecture", task "Deploy to prod"

       Source: task created by Anna 12/05
```

---

## 3. Chat Interface with Personal Agent

### Goal
Work through conversation — like with a secretary

### Principles
- 💬 **Chat only** — no dashboards, lists, kanbans
- 👤 **Personalization** — agent knows your role and preferences
- 🎯 **Onboarding** — agent initiates dialog with new users
- 📱 **Mobile access** — works on phone

### Onboarding (for new users)

```
Agent: Hi! I'm your personal agent in MindNest.

       Tell me a bit about yourself:
       - What's your role? (developer, manager, designer...)
       - What projects are you working on?

       This will help me better understand your requests.
```

### Personas (examples)

```yaml
Developer:
  - Technical details
  - Code/API connections
  - Test reminders

Product Manager:
  - Progress and statuses
  - Business context
  - Team blockers

Family:
  - Simple language
  - Focus on shared tasks
  - Event reminders
```

### Typical Workflow

```
User: Good morning!

Agent: Hi! For today:
       - 2 tasks with deadline
       - New message from Anna on project X

       Where shall we start?
```

---

## 4. Data Model

### Single Entity: KnowledgeItem

Moving away from traditional separate entities (Document, Comment, Task as UI elements).
Everything is knowledge of different types:

```yaml
KnowledgeItem:
  id: unique identifier
  type: fact | task | decision | note | question
  content: knowledge text
  status: (for task) todo | in_progress | done
  deadline: (for task) date, optional
  owner: responsible person
  project_id: project
  relations: connections to other KnowledgeItems
  created_at: when created
  updated_at: when modified
  created_by: who created
```

### Type Examples

| Type | Example |
|------|---------|
| `fact` | "We use PostgreSQL" |
| `task` | "Set up database replication" |
| `decision` | "Decided to use AWS" |
| `note` | "Meeting notes 12/10" |
| `question` | "Which hosting to choose?" |

### Connections Between Knowledge

Agent automatically creates connections:
- `relates_to` — general connection
- `implements` — task implements decision
- `blocks` — task blocks another
- `answers` — knowledge answers a question

### Chat History and LLM Context

**Where we store chat history:**

```yaml
Conversation:
  id: unique identifier
  user_id: user
  project_id: project (context)
  created_at: conversation start

Message:
  id: unique identifier
  conversation_id: conversation
  role: user | assistant
  content: message text
  timestamp: when sent
  tokens_used: how many tokens (for analytics)
  model_used: which model responded
```

**Storage:** PostgreSQL (simple queries, pagination, no graph needed)

**LLM Context Strategy:**

```
┌─────────────────────────────────────────────────────────────┐
│                    CONTEXT WINDOW                           │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 1. System Prompt (persona + instructions)           │   │
│  │    ~500-1000 tokens                                 │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 2. User Context                                     │   │
│  │    - Role, preferences                              │   │
│  │    - Current project                                │   │
│  │    ~200-500 tokens                                  │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 3. Relevant Knowledge (RAG)                         │   │
│  │    - Semantic search by query                       │   │
│  │    - Top-5 relevant KnowledgeItems                  │   │
│  │    ~1000-2000 tokens                                │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 4. Chat History (sliding window)                    │   │
│  │    - Last N messages                                │   │
│  │    - If N > limit → summarize old ones              │   │
│  │    ~2000-4000 tokens                                │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 5. Current User Request                             │   │
│  │    ~100-500 tokens                                  │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  TOTAL: ~4000-8000 tokens per request                      │
│  Gemini Flash context: 1M tokens (plenty of room)          │
└─────────────────────────────────────────────────────────────┘
```

**Sliding window + summary strategy:**

```
Messages 1-10:  Fully in context
Messages 11-30: Summarization → 1 block "Previously discussed: ..."
Messages 31+:   Not in context (but can be found via RAG)
```

**Example:**

```
[System Prompt]
You are a personal assistant in MindNest...

[User Context]
User: Sergey, role: developer
Current project: "MindNest MVP"

[Relevant Knowledge - RAG]
- Task: "Configure nginx" (in_progress, deadline today)
- Fact: "Using PostgreSQL for metadata"
- Decision: "Flutter for mobile app"

[Chat Summary]
Previously discussed: system architecture, technology choices,
MVP plan. Decided to use Java + Spring Boot.

[Recent Messages]
User: What tasks for today?
Assistant: You have 2 tasks with deadline today...
User: Tell me more about nginx

[Current Message]
User: What about SSL?
```

**Cost optimization:**

| Strategy | Savings |
|----------|---------|
| Summarization via Flash-8B | Cheap model for summary |
| Caching RAG results | Fewer embedding requests |
| Short system prompts | Fewer tokens per request |
| Lazy loading context | Load knowledge only if needed |

---

## 5. Multi-Agent Architecture

### Structure

```
┌─────────────────┐
│  User (Chat)    │
└────────┬────────┘
         ↓
┌─────────────────────────┐
│  Personal Agent         │ ← Your personal secretary
│  (knows your context)   │
└────────┬────────────────┘
         │
    ┌────┴────┬─────────────┐
    ↓         ↓             ↓
┌────────┐ ┌────────┐ ┌────────┐
│Knowledge│ │ Task   │ │ Search │
│ Agent   │ │ Agent  │ │ Agent  │
└────────┘ └────────┘ └────────┘
                          ↓
                    ┌────────┐
                    │ Time   │ ← Separate for date handling
                    │ Agent  │    (LLMs poorly understand time)
                    └────────┘
```

### Agent Roles

**Personal Agent:**
- Communicates with user
- Understands context and role
- Delegates to specialized agents
- Shows Confidence Score and sources

**Knowledge Agent:**
- Creates and updates knowledge
- Controls versioning
- Builds connections

**Task Agent:**
- Manages tasks and statuses
- Decomposes large tasks
- Finds duplicates

**Search Agent:**
- Semantic search
- Query vectorization
- Result ranking

**Time Agent:**
- Works with dates and deadlines
- "Tasks for today" filtering
- Programmatic logic (not LLM)

---

## 6. Team Collaboration

### Principles
- Everyone works through their own agent
- Everyone sees shared projects (no separation within project)
- Agents have access to shared knowledge graph

### Example

```
Anna → agent: "Add to nginx task — SSL is required"
Anna's Agent: Added context.

Ivan → agent: "What's with the nginx task?"
Ivan's Agent: Task in progress. Anna noted: SSL required.
              Source: Anna's comment from 12/10
```

### What We DON'T Do
- ❌ Group discussions (use Slack/Telegram for that)
- ❌ Privacy within project (for now)
- ❌ Complex access rights (for now)

---

## 7. AI Capabilities and Limitations

### What AI DOES
- 🤖 Extracts knowledge from text/files
- 🤖 Builds semantic connections
- 🤖 Decomposes tasks
- 🤖 Finds similar items and duplicates
- 🤖 Answers questions from knowledge base
- 🤖 Shows Confidence Score
- 🤖 Cites information sources

### What AI DOES NOT Do
- ❌ Write code
- ❌ Execute tasks for people
- ❌ Integrate with CI/CD
- ❌ Do automatic development

### Fighting Hallucinations
- Always show data source
- Confidence Score for uncertain answers
- Ability to request "raw data"

---

## 8. MVP Scope

### Included in MVP

1. ✅ **Chat interface** (Web + Mobile responsive)
2. ✅ **Onboarding** — agent initiates dialog
3. ✅ **Personal Agent** with basic personas
4. ✅ **Knowledge Agent** (create, search, versioning)
5. ✅ **Task Agent** (create, statuses, deadlines)
6. ✅ **Search Agent** (semantic search)
7. ✅ **Time Agent** (date handling)
8. ✅ **Automatic connections** between knowledge
9. ✅ **Projects** + basic collaboration
10. ✅ **Confidence Score** and source display
11. ✅ **Free tier** with limitations

### MVP Decisions

| Aspect | Decision |
|--------|----------|
| UI | Chat only, no dashboards |
| Long documents | Don't edit, upload/dictate |
| Mobile | Responsive web (not separate app) |
| Privacy | No separation within project |
| Offline | No |
| Group chats | No, only personal agents |

---

## 9. Post-MVP Roadmap

### Next Iteration

| Feature | Description |
|---------|-------------|
| **Reminders** | Automatic deadline reminders |
| **Time Machine** | View state at any date |
| **Migration** | Import from Notion, Jira, Confluence |
| **Voice input** | "Hey MindNest, add task..." |
| **Integrations** | Google Calendar, Slack, GitHub |

### Future

| Feature | Description |
|---------|-------------|
| **Agent-to-Agent** | Agents communicate for automation |
| **Local models** | Self-hosted for privacy |
| **Privacy** | Access rights within project |
| **Mobile app** | Flutter + Dart (native) |
| **Multimodal** | Work with images, diagrams |

---

## 10. Architecture Evolution

### 10.1 Path to Multi-Agent Architecture

**MVP:** One agent with Tools
```
┌─────────────────────────────────┐
│     Orchestrator Agent          │
│                                 │
│  tools: [                       │
│    KnowledgeTools,              │
│    TaskTools,                   │
│    SearchTools,                 │
│    TimeTools                    │
│  ]                              │
└─────────────────────────────────┘
```

**Evolution:** Tools → Agents
```
┌─────────────────────────────────┐
│     Orchestrator Agent          │
│         (Router)                │
└───────────┬─────────────────────┘
            │
    ┌───────┴───────┬───────────────┐
    ↓               ↓               ↓
┌────────┐    ┌────────┐    ┌────────┐
│Knowledge│    │ Task   │    │Search  │
│ Agent   │    │ Agent  │    │ Agent  │
└────────┘    └────────┘    └────────┘
```

**What we do now for easy transition:**
- Tools as separate classes with unified interface
- Dependency Injection everywhere
- Stateless tools
- Clear separation of responsibilities

**Transition = 1-2 day refactor:**
- Each Tool class gets its own system prompt
- Add Router for agent selection
- Orchestrator delegates instead of direct calls

**Frameworks for multi-agents (Java):**
- Spring AI — built-in support
- LangGraph4j — agent graphs
- Custom implementation via message bus

### 10.2 Mobile App (Flutter + Dart)

**Strategy:**

```
MVP: Flutter + Dart
  │
  │  Native iOS + Android app
  │  Single codebase for both platforms
  │  Best UX from day one
  │
  ↓
Post-MVP: Feature expansion
  │
  │  Push notifications
  │  Offline mode
  │  Background sync
  │
  ↓
Future: Platform features
  │
  │  iOS/Android widgets
  │  Siri/Google Assistant integration
  │  Wear OS / Watch support
```

**Why Flutter:**
- Single code → iOS + Android
- Native performance
- Excellent UI toolkit
- Good documentation
- Dart is similar to Java (easy to learn)

**Mobile app architecture:**
```
┌─────────────────────────────────┐
│     Flutter App                 │
│                                 │
│  ┌───────────────────────────┐  │
│  │      Chat UI              │  │
│  │   (same design)           │  │
│  └───────────────────────────┘  │
│                                 │
│  ┌───────────────────────────┐  │
│  │   API Client              │  │
│  │   (REST + WebSocket)      │  │
│  └───────────────────────────┘  │
│                                 │
│  ┌───────────────────────────┐  │
│  │   Local Storage           │  │
│  │   (offline cache)         │  │
│  └───────────────────────────┘  │
└─────────────────────────────────┘
            │
            ↓
┌─────────────────────────────────┐
│     MindNest Backend            │
│     (same API)                  │
└─────────────────────────────────┘
```

### 10.3 Scaling Plan

**Phase 1: MVP (10-100 users)**
```
┌─────────────────────────────────┐
│  Google Compute Engine VM       │
│                                 │
│  Docker Compose:                │
│  - Frontend (SvelteKit)         │
│  - Backend (Spring Boot)        │
│  - Neo4j                        │
│  - Qdrant                       │
│  - PostgreSQL                   │
│  - Nginx                        │
│                                 │
│  ~$50-100/month                 │
└─────────────────────────────────┘
```

**Phase 2: Growth (100-10,000 users)**
```
┌─────────────────────────────────┐
│  Cloud Run (auto-scaling)       │
│  - Frontend                     │
│  - Backend (N instances)        │
└─────────────────────────────────┘
            │
            ↓
┌─────────────────────────────────┐
│  Managed Databases              │
│  - Neo4j AuraDB                 │
│  - Cloud SQL (PostgreSQL)       │
│  - Qdrant Cloud                 │
│                                 │
│  ~$200-500/month                │
└─────────────────────────────────┘
```

**Phase 3: Scale (10,000+ users)**
```
┌─────────────────────────────────┐
│  GKE Kubernetes Cluster         │
│                                 │
│  - Auto-scaling pods            │
│  - Load balancer                │
│  - Redis for cache/sessions     │
└─────────────────────────────────┘
            │
            ↓
┌─────────────────────────────────┐
│  Sharded / Clustered DBs        │
│  - Neo4j Cluster                │
│  - Qdrant sharding              │
│  - PostgreSQL read replicas     │
│                                 │
│  ~$1000+/month                  │
└─────────────────────────────────┘
```

**Scaling principles (do now):**

| Principle | Implementation |
|-----------|----------------|
| Stateless backend | Sessions in DB, not in memory |
| 12-factor app | Config via env variables |
| Health checks | `/actuator/health` |
| Connection pooling | HikariCP |
| Graceful shutdown | Spring Boot automatic |
| Async operations | Virtual Threads |

**Potential bottlenecks:**

| Problem | Solution |
|---------|----------|
| LLM rate limits | Queue + retry, multiple API keys |
| Neo4j load | Read replicas, caching |
| Vector search | Qdrant sharding |
| WebSocket | Redis pub/sub for distribution |

---

## 11. Technology Stack

### Frontend (Mobile + Web)
- **Flutter + Dart** — single code for iOS, Android, Web
- Real-time chat via WebSocket
- Native performance

### Backend
- **Java 21 + Spring Boot 3.2+**
- Virtual Threads (Project Loom)
- Spring AI for LLM integration
- Spring Data Neo4j

### AI Layer (Google Cloud Vertex AI)

**LLM — Gemini with Model Routing:**
```
┌─────────────────────────────────────────────────────────────┐
│                    MODEL ROUTING                            │
│                                                             │
│  Incoming request                                           │
│        │                                                    │
│        ↓                                                    │
│  ┌─────────────────┐                                       │
│  │ Router (Flash)  │ ← Fast/cheap model                    │
│  │ Classifies      │   decides which model to use          │
│  │ request type    │                                       │
│  └────────┬────────┘                                       │
│           │                                                 │
│     ┌─────┴─────┬─────────────┬──────────────┐             │
│     ↓           ↓             ↓              ↓             │
│  ┌──────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │Flash │  │Flash-8B  │  │   Pro    │  │Programm- │       │
│  │      │  │          │  │          │  │atic      │       │
│  │Chat, │  │Simple    │  │Complex   │  │Time,     │       │
│  │search│  │queries   │  │analysis, │  │filters,  │       │
│  │      │  │          │  │decomp.   │  │dates     │       │
│  └──────┘  └──────────┘  └──────────┘  └──────────┘       │
│                                                             │
│  $0.075/M    $0.0375/M     $1.25/M      $0 (code)          │
└─────────────────────────────────────────────────────────────┘
```

| Task | Model | Why |
|------|-------|-----|
| Simple chat, FAQ | Gemini Flash-8B | Cheap, fast |
| Search, extraction | Gemini Flash | Price/quality balance |
| Task decomposition | Gemini Pro | Quality needed |
| Connection analysis | Gemini Pro | Complex logic |
| Dates, filters | Programmatic code | LLM not needed |

**Embeddings:**
- **text-embedding-004** (Vertex AI) — 768 dimensions

### Data Storage (Self-hosted, Docker)
- **Neo4j 5.x** — knowledge graph, connections, versioning
- **Qdrant** — vector search, embeddings
- **PostgreSQL 16** — users, sessions, auth

### Infrastructure (Google Cloud)
- **Compute Engine VM** — Docker Compose for MVP
- **Cloud Run** — scaling later
- **Artifact Registry** — Docker images
- **Secret Manager** — credentials
- **Cloud Logging** — monitoring

---

## 12. Summary

**MindNest is:**

> An AI-first platform for knowledge and task management through chat.
>
> Work like with a personal secretary who:
> - Instantly finds any information
> - Manages your tasks and deadlines
> - Understands context and connections between everything
> - Shows where information came from
>
> No dashboards, lists, kanbans — just conversation.
>
> For small teams, small businesses, and families.
> Replacement for Confluence + Jira, but simpler and through AI.
