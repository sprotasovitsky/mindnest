# LongMemEval Benchmark

Benchmarks for testing MindNest retrieval quality against the
[LongMemEval](https://github.com/xiaowu0162/LongMemEval) dataset.

Two test paths exist: **Chat** (full production pipeline via `/api/chat`) and
**MCP Agent** (simulated LLM client calling MCP tools). The Chat path is the
primary benchmark — it tests the real user experience end-to-end.

---

## Python modules

| File | Role |
|------|------|
| `config.py` | `BenchmarkConfig` dataclass — timing, credentials, paths, model names. Single source of truth for all harness settings. |
| `auth.py` | Two auth helpers: `login_jwt` (Chat test) and `login_oauth_pkce` (MCP Agent test, full PKCE flow). |
| `projects.py` | `create_project` and `get_project` — thin wrappers over `/api/projects`. |
| `run_chat_test.py` | **Primary benchmark.** Full production pipeline: create project → onboarding → ingest sessions → ask question → write `chat_hypothesis.jsonl`. Supports `--fill-only` / `--ask-only` for two-phase runs. |
| `run_mcp_agent_test.py` | MCP Agent benchmark. Gives Gemini the MCP tool descriptions and lets it decide how many searches to make. Tests the real MCP client experience (what Claude/Cursor sees). |
| `preprocess.py` | Preprocesses raw LongMemEval sessions into atomic facts via LLM before MCP ingestion. Produces `longmemeval_s_mcp_*.json` files. Run once per dataset variant — output is committed separately. |
| `test_single.py` | Debug utility. Clears chat history for a project, sends one question, prints reply + backend logs, saves timestamped log. Use to iterate on a single question without running the full benchmark. |
| `evaluate.py` | Gemini-as-judge evaluator. Reads a `*_hypothesis.jsonl`, compares to ground truth, prints per-type accuracy. |

Do **not** add new Python files without justification. Shared helpers go into
existing modules (`auth.py`, `projects.py`, `config.py`). New test paths need
a clear reason to exist alongside the two current ones.

---

## Data files (`data/`)

All `.json` files except `longmemeval_s.json` are gitignored (too large).

| File | Size | Description |
|------|------|-------------|
| `longmemeval_s.json` | 3 KB | 3-instance sample from the original dataset. Committed. Used for quick smoke tests and early development. |
| `longmemeval_s_cleaned.json` | 277 MB | Full LongMemEval-S (500 instances), cleaned. Primary reference for Chat benchmark evaluation. |
| `longmemeval_m_cleaned.json` | 2.7 GB | LongMemEval-M (500 instances, longer sessions). For extended runs. |
| `longmemeval_oracle.json` | 15 MB | Ground truth answers for all instances. Used by `evaluate.py`. |
| `longmemeval_s_mcp_30.json` | 2 MB | 30 instances preprocessed for MCP: raw turns replaced with LLM-extracted atomic facts. Input for `run_mcp_agent_test.py`. |
| `test_5_new.json` | 2.5 MB | 5-instance subset for iterating on the Chat path: degrees, commute, coupon, theater, Spotify playlist. Current active dev dataset. |

Do **not** add new data files without reason. New subsets of existing datasets
should be created with `--limit` on the runner, not as separate files.
New preprocessed MCP variants are created by `preprocess.py` when the
preprocessing strategy changes.

---

## Results (`results/`)

Gitignored entirely. Structure created at runtime.

| Path | Created by | Contents |
|------|-----------|----------|
| `results/<run>/chat_hypothesis.jsonl` | `run_chat_test.py` | One JSON line per instance: `{id, answer, question}` |
| `results/<run>/projects_map.json` | `run_chat_test.py --fill-only` | Maps `instance_id → project_id` for two-phase runs |
| `results/<run>/mcp_agent_hypothesis.jsonl` | `run_mcp_agent_test.py` | Same format as chat hypothesis |
| `results/*.eval-results-gemini` | `evaluate.py` | Per-instance eval labels written next to the hypothesis file |
| `results/prompt_optimization_history.json` | Manual | History of MCP search prompt variants and scores |
| `results/optimization_120_results.json` | Manual | Parsed results of the 6×4×5=120 prompt optimization run |
| `results/exploratory_questions.json` | Manual | Reference questions used during exploratory testing |

---

## Logs (`logs/`)

Gitignored. Named by type + timestamp or run name.

| Pattern | Source | Keep? |
|---------|--------|-------|
| `backend_<run>.log` | uvicorn stdout redirected manually | Keep latest per run; delete after analysis |
| `fill_<run>.log` | `run_chat_test.py --fill-only` stdout | Keep until ask phase completes |
| `single_<timestamp>.log` | `test_single.py` | Keep last 5–10; delete older |
| `final_*.log` | Historical MCP prompt optimization (60-run batches) | Keep as benchmark history |
| `optimization_120.log` | 120-run C1–C6 × P1–P4 grid search | Keep as benchmark history |
| `preprocess_*.log` | `preprocess.py` stdout | Keep until MCP data file is verified |

---

## Typical workflows

### Chat benchmark — two-phase run (see CLAUDE.md for full commands)

Always use `/api/chat` — never MCP endpoints.

```
Phase 1 — Fill (fast settings):
  ITERATIVE_SEARCH_MAX=0 LLM_THINKING_LEVEL=NONE LLM_MAX_OUTPUT_TOKENS=200 uvicorn ...
  run_chat_test.py --fill-only
  → creates projects, ingests sessions, writes projects_map.json
  → no iterative search, no thinking, capped responses (200 tokens)

Phase 2 — Ask (normal settings):
  normal uvicorn (no env overrides)
  run_chat_test.py --ask-only
  → reads projects_map.json, asks benchmark questions, writes chat_hypothesis.jsonl
```

### Debug a single question

```bash
python -m benchmarks.longmemeval.test_single \
    --project-id <id> \
    --question "Where did I redeem a $5 coupon on coffee creamer?"
```

### MCP Agent benchmark

```bash
# Preprocess dataset (if strategy changed)
python -m benchmarks.longmemeval.preprocess \
    --input data/longmemeval_s_cleaned.json \
    --output data/longmemeval_s_mcp_30.json \
    --limit 30

# Run agent test
python -m benchmarks.longmemeval.run_mcp_agent_test \
    --email benchmark2@mindnest.one --password BenchmarkPass123! \
    --dataset data/longmemeval_s_mcp_30.json
```

### Evaluate results

```bash
python -m benchmarks.longmemeval.evaluate \
    --hypothesis results/chat5_new/chat_hypothesis.jsonl \
    --reference data/longmemeval_s_cleaned.json
```
