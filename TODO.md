# MindNest TODO / Future Improvements

## Priority: High

### 1. Emergent Schema Layer

**Vision:** Emergent Schema — это self-describing, evolving knowledge structure. Схема не задаётся заранее, а возникает из использования и стабилизируется AI.

**Архитектурные слои:**

```
┌─────────────────────────────────────────────────────────────┐
│  5. Temporal Dimension                                       │
│     Schema versioning, lineage, evolution history            │
├─────────────────────────────────────────────────────────────┤
│  4. Schema Stabilization                                     │
│     Frequency analysis, clustering, synonym merging          │
│     deadline/due_date/finish_by → due_date                   │
├─────────────────────────────────────────────────────────────┤
│  3. Schema Memory (Meta-Schema)                              │
│     EntityTypes, RelationTypes, confidence scores            │
│     📌 Schema = данные в том же графе                        │
├─────────────────────────────────────────────────────────────┤
│  2. Semantic Normalization (LLM)                             │
│     Entity extraction, intent classification, relations      │
├─────────────────────────────────────────────────────────────┤
│  1. Raw Knowledge Layer                                      │
│     Chat messages, documents, AI actions                     │
└─────────────────────────────────────────────────────────────┘
```

**Implementation Steps:**

- [ ] **Layer 3: Schema Memory** — store EntityType/RelationType as meta-nodes in Neo4j
  - [ ] Create `SchemaNode` label for meta-schema nodes
  - [ ] Track `confidence_score` based on usage frequency
  - [ ] Store semantic descriptions for each type

- [ ] **Layer 4: Schema Stabilization** — normalize synonyms automatically
  - [ ] Frequency analysis: track how often each type is used
  - [ ] Synonym clustering: group similar types (bought/purchased/acquired)
  - [ ] Merge algorithm: consolidate to canonical type when confidence is high
  - [ ] Conflict detection: alert when types semantically overlap

- [ ] **Layer 5: Temporal Schema** — version schema evolution
  - [ ] Timestamp when each type was first created
  - [ ] Track lineage: how types evolved/merged
  - [ ] Don't break old data when schema changes

- [ ] **API & Tooling**
  - [ ] Schema introspection endpoint: view all types, their confidence, usage
  - [ ] Admin UI for manual merge/split of types
  - [ ] Schema health metrics: entropy, fragmentation

**Key Principle:**
> AI-агент не ломает систему, он расширяет её язык.
> Schema стабилизируется со временем, а не навязывается заранее.

**Questions to resolve:**
- How does this integrate with Graphiti's existing edge types?
- Should stabilization run in background or on-demand?
- What confidence threshold triggers auto-merge?

**Discussion topics (next session):**
- [ ] Алгоритмы стабилизации — embedding similarity vs LLM clustering?
- [ ] Schema graph example — как meta-schema выглядит в Neo4j
- [ ] Как избежать хаоса — confidence threshold, human-in-the-loop?
- [ ] Product moat — Emergent Schema как конкурентное преимущество

---

### 2. Project Description / Context
**Problem:** LLM lacks domain context. "Buy wine" means different things for wedding planning vs personal budget.

**Ideas:**
- [ ] Add `description` field to Project model (simple text)
- [ ] Include project description in system prompt for better LLM understanding
- [ ] Optional: structured project types (BUDGET, EVENT, TEAM, PERSONAL) with type-specific prompts

**Questions to resolve:**
- Free text or structured (type + description)?
- Should description influence schema/edge type suggestions?

---

## Priority: Medium

### 3. Smarter Search & Retrieval
- [ ] **Query rewriting** — LLM rewrites vague queries before search (already have search_query in classifier, expand this)
- [ ] **Multi-hop reasoning** — for complex questions, chain multiple searches
- [ ] **Source attribution** — show which facts contributed to the answer

### 4. Graph Quality & Maintenance
- [ ] **Duplicate entity detection** — merge "Boris", "Борис", "boris" into one entity
- [ ] **Entity resolution UI** — admin view to manually merge/split entities
- [ ] **Orphan cleanup** — remove entities with no edges after X days
- [ ] **Graph statistics endpoint** — entity count, edge count, most connected nodes

### 5. Performance & Scaling
- [ ] **Batch message processing** — process multiple messages in one Graphiti call
- [ ] **Caching layer** — cache frequent searches (e.g., "what's my budget?")
- [ ] **Async improvements** — move more processing to background tasks

---

## Priority: Low (Nice to Have)

### 6. Mobile/UX Improvements
- [ ] **Typing indicators** — show when AI is processing
- [ ] **Message reactions** — thumbs up/down for feedback
- [ ] **Voice input** — speech-to-text for messages
- [ ] **Rich message types** — show tables, charts for budget summaries

### 7. Multi-Project Features
- [ ] **Cross-project search** — find info across all user's projects
- [ ] **Project templates** — pre-configured schemas for common use cases
- [ ] **Project archiving** — soft delete with graph preservation

### 8. Analytics & Insights
- [ ] **Automatic summaries** — daily/weekly digest of changes
- [ ] **Trend detection** — "spending increased 20% this month"
- [ ] **Reminders** — proactive notifications based on tasks/deadlines

---

## Technical Debt

- [ ] Add comprehensive error handling in `graphiti_client.py`
- [ ] Add retry logic for LLM API calls
- [ ] Improve test coverage for edge cases
- [ ] Add OpenTelemetry tracing for debugging

---

## Notes

*Last updated: 2025-01-07*

### Discussion Points for Tomorrow:
1. MetaEdgeType vs normalization — which approach fits better?
2. Project description — structured types or free text?
3. Priority order — what to build first?
