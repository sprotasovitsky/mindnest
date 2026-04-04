"""Prometheus metrics for LLM observability (Layer 3).

Exposes metrics at /metrics via prometheus-fastapi-instrumentator.
Custom LLM metrics: latency, token counts, cost, errors, message types.
"""

from prometheus_client import Counter, Histogram

# LLM call latency histogram (labels: model, step)
llm_latency = Histogram(
    "llm_request_duration_seconds",
    "LLM call latency in seconds",
    ["model", "step"],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0],
)

# Token counts (labels: model, token_type = input|output|thinking)
llm_tokens = Counter(
    "llm_tokens_total",
    "Total LLM token counts",
    ["model", "token_type"],
)

# Cost in USD (labels: model, step)
llm_cost = Counter(
    "llm_cost_usd_total",
    "Cumulative LLM cost in USD",
    ["model", "step"],
)

# Error counter (labels: model, step)
llm_errors = Counter(
    "llm_error_total",
    "Total LLM call errors",
    ["model", "step"],
)

# Chat message type distribution (labels: message_type = DATA|QUESTION|BOTH)
message_type_counter = Counter(
    "chat_message_type_total",
    "Chat message classification distribution",
    ["message_type"],
)
