# LLM Observability Plan for MindNest

## Stack Context
- 3 Gemini models: classifier (gemini-2.5-flash-lite), responder (gemini-3-flash-preview), graphiti (gemini-2.5-flash)
- Vertex AI (not OpenAI API) — limits compatibility with some tools
- FastAPI + Neo4j + PostgreSQL + GCP

---

## Layer 1 — Structured Logging (foundation)

**What:** Every LLM call logged as machine-readable JSON with full context.

**Implementation options:**

| Option | Description | Complexity |
|---|---|---|
| A. `structlog` | Python structured logging library, JSON output | Low |
| B. Custom middleware | FastAPI middleware intercepts all requests | Low |
| C. Decorator on `generate_text()` | Wrap one function, everything logs automatically | Low |

**What to log:**
```json
{
  "trace_id": "uuid",
  "model": "gemini-3-flash-preview",
  "latency_ms": 1240,
  "input_tokens": 842,
  "output_tokens": 312,
  "cost_usd": 0.0018,
  "step": "chat_response",
  "project_id": "...",
  "user_id": "...",
  "message_type": "QUESTION"
}
```

---

## Layer 2 — Distributed Tracing

**What:** One user request = one trace. Full path visible: auth → classify → search → LLM → response.

**Implementation options:**

| Option | Description | Complexity |
|---|---|---|
| A. **OpenTelemetry** (standard) | OTLP protocol, export to any backend | Medium |
| B. **Google Cloud Trace** | Native GCP, zero config on GCP | Low |
| C. **Jaeger** (self-hosted) | Open source, Docker, full control | Medium |

**Spans for MindNest:**
```
trace: user_chat_request
  ├── span: authenticate_user
  ├── span: verify_project_membership
  ├── span: classify_message        ← Gemini flash-lite
  ├── span: graphiti_search         ← Neo4j
  ├── span: pending_cache_lookup
  ├── span: llm_generate_response   ← Gemini pro
  └── span: save_chat_history
```

---

## Layer 3 — Metrics (Prometheus)

**What:** Real-time numeric metrics, alerts, Grafana dashboards.

**Implementation options:**

| Option | Description | Complexity |
|---|---|---|
| A. `prometheus-fastapi-instrumentator` | Automatic HTTP metrics | Low |
| B. `prometheus_client` custom metrics | Full control over metrics | Medium |
| C. **Google Cloud Monitoring** | Native GCP, no own Prometheus | Low |

**Key metrics:**
```
# Latency
llm_request_duration_seconds{model, step}
graphiti_search_duration_seconds

# Tokens / Cost
llm_tokens_total{model, type}  # input/output
llm_cost_usd_total{model, user_id, project_id}

# Quality
chat_message_type_total{type}  # DATA/QUESTION/BOTH
classifier_confidence_histogram

# Errors
llm_error_total{model, error_type}
graphiti_error_total
```

---

## Layer 4 — AI-Specific Observability

**What:** Specialized tools for LLM chain visualization, replay, prompt comparison.

**Implementation options:**

| Tool | Vertex AI support | Self-hosted | Cost |
|---|---|---|---|
| **Arize Phoenix** | ✅ via OpenTelemetry | ✅ Docker | Free |
| **LangSmith** | ✅ (LangChain-agnostic) | ❌ cloud only | $$ |
| **Helicone** | ⚠️ proxy-based, Vertex harder | ❌ | $$ |
| **Weights & Biases** | ✅ | ❌ | $$ |
| **Langfuse** | ✅ | ✅ Docker | Free / $$ |

**Recommendation:** Arize Phoenix or Langfuse — both self-hosted, both support Vertex AI via OpenTelemetry.

**What they provide:**
- Chain visualization: classifier → search → response
- Replay any request
- Prompt comparison v1 vs v2
- Token/cost breakdown per step

---

## Layer 5 — Cost Tracking

**What:** Real cost in USD: per request, per user, per project, per day.

**Implementation options:**

| Option | Description | Complexity |
|---|---|---|
| A. **PostgreSQL table** | `llm_usage` table, SQL aggregations | Medium |
| B. **Prometheus + Grafana** | cost_usd metrics, dashboard | Medium |
| C. **Google Cloud Billing API** | Native Vertex AI cost per GCP project | Low (but coarse) |

**Gemini pricing (for calculation):**
```python
GEMINI_PRICING = {
    "gemini-2.5-flash-lite":  {"input": 0.000_000_075, "output": 0.000_000_3},
    "gemini-2.5-flash":       {"input": 0.000_000_15,  "output": 0.000_000_6},
    "gemini-3-flash-preview": {"input": 0.000_000_075, "output": 0.000_000_3},
}
```

---

## Layer 6 — Prompt Versioning

**What:** Prompt versioning, A/B testing, rollback.

**Implementation options:**

| Option | Description | Complexity |
|---|---|---|
| A. **Git-based** (already in place) | Prompts in `/prompts/*.txt`, history in git | Zero |
| B. **Version in logs** | Add `prompt_version` to every log entry | Low |
| C. **Langfuse Prompt Management** | UI for prompts, A/B, rollback | Medium |
| D. **DB + API** | Store prompts in PostgreSQL, hot-reload | High |

---

## Layer 7 — Evaluation Pipeline

**What:** Automated quality assessment — not "seems fine" but measurable.

**Implementation options:**

| Tool | Description | Complexity |
|---|---|---|
| **Ragas** | Metrics: faithfulness, answer relevance, context recall | Medium |
| **DeepEval** | LLM-as-a-judge, golden datasets | Medium |
| **LLM-as-judge** | Gemini evaluates Gemini responses | Low (DIY) |
| **Human feedback** | Thumbs up/down in UI → stored in DB | Medium |

**Key quality metrics for MindNest:**
- **Faithfulness**: answer grounded in graph data, not hallucinated
- **Context recall**: graph retrieved relevant data for the query
- **Answer relevance**: response actually answers the user's question
- **Classification accuracy**: DATA/QUESTION/BOTH classified correctly

---

## Layer 8 — Alerting

**What:** Notifications when something goes wrong.

**Implementation options:**

| Option | Complexity |
|---|---|
| Grafana Alerting → Slack/email | Medium |
| Google Cloud Monitoring Alerts | Low (native GCP) |
| PagerDuty / OpsGenie | High |

**Alerts for MindNest:**
- LLM latency > 10s
- Error rate > 5%
- Cost per day > $X threshold
- Graphiti search failure rate > 10%

---

## Prioritized Roadmap

```
MVP (1-2 days)
  ├── Layer 1: Structured logging — decorator on generate_text()
  └── Layer 5: Cost tracking in logs (simple calculation)

v1 (1 week)
  ├── Layer 3: Prometheus metrics + Grafana dashboard
  └── Layer 2: OpenTelemetry / Google Cloud Trace

v2 (2-3 weeks)
  ├── Layer 4: Langfuse self-hosted (AI observability UI)
  ├── Layer 6: prompt_version in logs
  └── Layer 8: Alerting

v3 (as needed)
  ├── Layer 7: Evaluation pipeline (Ragas)
  └── Layer 6: Langfuse Prompt Management (full)
```
