"""Request-scoped context variables for propagating trace IDs across async calls."""

from contextvars import ContextVar

# Set once per HTTP request in the chat router; read anywhere in the call stack
current_trace_id: ContextVar[str | None] = ContextVar("current_trace_id", default=None)
