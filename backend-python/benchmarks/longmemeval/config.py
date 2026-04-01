"""Configuration for LongMemEval benchmark harness."""

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class BenchmarkConfig:
    # API base URL
    api_url: str = "http://localhost:8000"

    # Benchmark user credentials (create a dedicated account before running)
    email: str = ""
    password: str = ""

    # MCP OAuth client ID (registered in the system)
    mcp_client_id: str = "mcp-benchmark-client"
    # Redirect URI used during PKCE flow (must be registered or accepted by server)
    mcp_redirect_uri: str = "http://localhost:9999/callback"

    # Timing
    graphiti_wait_base_seconds: int = 30
    graphiti_wait_per_message: float = 0.5
    graphiti_wait_max_seconds: int = 120
    inter_message_delay_seconds: float = 1.0
    inter_session_delay_seconds: float = 2.0

    # Rate limit handling
    rate_limit_backoff_seconds: int = 60
    rate_limit_max_retries: int = 3

    # Onboarding seed sent as first message to every new project in the chat test.
    # Must be descriptive enough to trigger description confirmation.
    onboarding_seed_message: str = (
        "This is my personal memory assistant. "
        "Please use it to remember information about my life, work, and tasks."
    )

    # Gemini model used for answer synthesis in the MCP test
    gemini_model_for_synthesis: str = "gemini-2.5-flash"

    # Dataset path (relative to this file's directory or absolute)
    dataset_path: str = str(
        Path(__file__).parent / "data" / "longmemeval_s.json"
    )

    # Output directory
    output_dir: str = str(Path(__file__).parent / "results")

    # How many instances to process (None = all)
    limit: int | None = None

    # Short-turn context prepend threshold (chars)
    short_turn_threshold: int = 30

    # Vertex AI project/location for Gemini synthesis (reads from env if empty)
    vertex_project: str = ""
    vertex_location: str = "us-central1"

    # Extra fields can be added per-run via CLI arguments
    extra: dict = field(default_factory=dict)


# Singleton config — override fields in CLI scripts before use
DEFAULT_CONFIG = BenchmarkConfig()
