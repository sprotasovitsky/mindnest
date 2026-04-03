"""MCP Agent test — simulates a real LLM client connected via MCP.

Instead of hardcoded search→synthesis, gives Gemini our MCP tool
descriptions and lets it decide which tools to call, how many times,
and how to interpret results. Tests the full MCP experience as a
real client (Claude, Cursor) would use it.

Usage:
    source .env
    python -m benchmarks.longmemeval.run_mcp_agent_test \
        --email benchmark@example.com \
        --password secret \
        --limit 3

Output:
    results/mcp_agent_hypothesis.jsonl
"""

import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path

import httpx
from google import genai
from google.genai import types
from google.oauth2 import service_account

from .auth import login_oauth_pkce, login_jwt
from .config import BenchmarkConfig
from .projects import create_project

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)

MCP_PROJECT_DESCRIPTION = "Benchmark project for LongMemEval MCP agent test"
MAX_AGENT_TURNS = 5

# Tool descriptions — same as MCP endpoint docstrings
SEARCH_TOOL_DESC = """Search project knowledge using natural language.
Searches for facts and entities related to the query in the specified project.

Use this to find any stored information:
- Facts, events, tasks, preferences, relationships, states
- People and contacts, purchases and expenses
- Any information previously stored via send_message or chat

Returns facts (relationships between entities) and entities (people, items,
places, concepts with aggregated summaries).

Before each search call, reason about:
1. What do I already know from previous results?
2. What is still missing to answer the question?
3. Which entity name from the results could lead me closer to the answer?

Then search for that entity name. Short entity-name queries (1-2 words)
find more connected facts than long natural language questions."""

GET_USER_TOOL_DESC = """Get the current user's name and ID.
Call this before searching if the question uses first-person pronouns
like "my", "I", "me" — then include the user name in your search query."""


# ---------------------------------------------------------------------------
# Gemini client with function calling
# ---------------------------------------------------------------------------

_client = None


def _get_client() -> genai.Client:
    global _client
    if _client is not None:
        return _client

    project = os.environ.get("VERTEX_AI_PROJECT_ID", "")
    location = "global"
    sa_email = os.environ.get("GCP_SERVICE_ACCOUNT_EMAIL", "")
    private_key = os.environ.get("GCP_PRIVATE_KEY", "").replace("\\n", "\n")

    if not project or not sa_email or not private_key:
        raise RuntimeError("Vertex AI credentials not set")

    credentials = service_account.Credentials.from_service_account_info(
        {
            "type": "service_account",
            "project_id": project,
            "private_key": private_key,
            "client_email": sa_email,
            "token_uri": "https://oauth2.googleapis.com/token",
        },
        scopes=["https://www.googleapis.com/auth/cloud-platform"],
    )
    _client = genai.Client(vertexai=True, project=project, location=location, credentials=credentials)
    return _client


# ---------------------------------------------------------------------------
# MCP tool execution
# ---------------------------------------------------------------------------

def _headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def execute_search(api_url: str, token: str, project_id: str, query: str) -> dict:
    """Execute search_knowledge MCP call."""
    resp = httpx.post(
        f"{api_url}/api/mcp/search",
        json={"query": query, "project_id": project_id},
        headers=_headers(token),
        timeout=120,
    )
    resp.raise_for_status()
    data = resp.json()
    # Format for LLM consumption
    facts = [f.get("fact", "") for f in data.get("facts", [])]
    entities = [
        f"{e.get('name', '')}: {e.get('summary', '')[:100]}"
        for e in data.get("entities", [])
    ]
    return {
        "facts": facts[:20],
        "entities": entities[:15],
        "total_facts": len(data.get("facts", [])),
        "total_entities": len(data.get("entities", [])),
    }


def execute_get_user(api_url: str, token: str) -> dict:
    """Execute get_current_user MCP call."""
    # MCP auth token contains user info
    resp = httpx.get(
        f"{api_url}/api/mcp/user",
        headers=_headers(token),
        timeout=30,
    )
    if resp.status_code == 200:
        return resp.json()
    # Fallback — extract from token
    return {"name": "Benchmark User", "note": "user endpoint not available"}


# ---------------------------------------------------------------------------
# Agent loop
# ---------------------------------------------------------------------------

def ask_question_as_agent(
    api_url: str,
    mcp_token: str,
    project_id: str,
    question: str,
    model: str = "gemini-3.1-flash-lite-preview",
) -> tuple[str, list[str]]:
    """Run agent loop: give Gemini MCP tools, let it answer the question."""
    client = _get_client()

    tools = types.Tool(function_declarations=[
        types.FunctionDeclaration(
            name="search_knowledge",
            description=SEARCH_TOOL_DESC,
            parameters=types.Schema(
                type="OBJECT",
                properties={
                    "query": types.Schema(type="STRING", description="Natural language search query"),
                },
                required=["query"],
            ),
        ),
        types.FunctionDeclaration(
            name="get_current_user",
            description=GET_USER_TOOL_DESC,
            parameters=types.Schema(type="OBJECT", properties={}),
        ),
    ])

    system_prompt = (
        "You are a helpful assistant answering questions about the user's personal knowledge. "
        "Use the available tools to search the knowledge graph. "
        "The graph stores entities connected by relationships. "
        "If your search returns facts that mention an entity you haven't explored yet, "
        "search for that entity name to discover connected information. "
        "Answer concisely based on the facts you find."
    )

    config = types.GenerateContentConfig(
        tools=[tools],
        thinking_config=types.ThinkingConfig(thinking_budget=1024),
        system_instruction=system_prompt,
    )

    contents = [
        types.Content(role="user", parts=[types.Part(text=question)]),
    ]

    queries_used = []

    for turn in range(MAX_AGENT_TURNS):
        response = client.models.generate_content(
            model=model,
            contents=contents,
            config=config,
        )

        candidate = response.candidates[0]

        # Check if model wants to call a function
        function_calls = [
            p.function_call for p in candidate.content.parts
            if p.function_call is not None
        ]

        if not function_calls:
            # Model produced a text answer
            text_parts = [p.text for p in candidate.content.parts if p.text]
            answer = " ".join(text_parts).strip()
            logger.info(f"  Agent answered after {turn} tool calls, queries: {queries_used}")
            return answer, queries_used

        # Execute function calls
        contents.append(candidate.content)

        function_responses = []
        for fc in function_calls:
            if fc.name == "search_knowledge":
                query = fc.args.get("query", question)
                queries_used.append(query)
                logger.info(f"  Agent calls search_knowledge({query!r})")
                result = execute_search(api_url, mcp_token, project_id, query)
                function_responses.append(
                    types.Part(function_response=types.FunctionResponse(
                        name="search_knowledge",
                        response=result,
                    ))
                )
            elif fc.name == "get_current_user":
                logger.info("  Agent calls get_current_user()")
                result = execute_get_user(api_url, mcp_token)
                function_responses.append(
                    types.Part(function_response=types.FunctionResponse(
                        name="get_current_user",
                        response=result,
                    ))
                )

        contents.append(types.Content(role="user", parts=function_responses))

    # Max turns reached — force text response with mode=NONE
    logger.info(f"  Agent hit max turns — forcing text response")
    final_config = types.GenerateContentConfig(
        tools=[tools],
        tool_config=types.ToolConfig(
            function_calling_config=types.FunctionCallingConfig(mode="NONE"),
        ),
        system_instruction=system_prompt,
    )
    if model.startswith("gemini-3"):
        final_config = types.GenerateContentConfig(
            tools=[tools],
            tool_config=types.ToolConfig(
                function_calling_config=types.FunctionCallingConfig(mode="NONE"),
            ),
            thinking_config=types.ThinkingConfig(thinking_budget=1024) if "lite" in model else None,
            system_instruction=system_prompt,
        )
    try:
        response = client.models.generate_content(
            model=model, contents=contents, config=final_config,
        )
        text_parts = [p.text for p in response.candidates[0].content.parts if p.text]
        answer = " ".join(text_parts).strip()
        logger.info(f"  Forced answer: {answer[:100]}")
        return answer, queries_used
    except Exception as e:
        logger.error(f"  Forced answer failed: {e}")
        return f"Could not determine answer after {MAX_AGENT_TURNS} tool calls.", queries_used


# ---------------------------------------------------------------------------
# Dataset & ingestion (reuse from run_mcp_test)
# ---------------------------------------------------------------------------

def load_dataset(path: str) -> list[dict]:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Dataset not found at {p}")
    with open(p) as f:
        data = json.load(f)
    logger.info(f"Loaded {len(data)} instances from {p}")
    return data


def _normalize_sessions(raw_sessions: list) -> list[list[dict]]:
    out = []
    for s in raw_sessions:
        if isinstance(s, dict) and "turns" in s:
            out.append(s["turns"])
        elif isinstance(s, list):
            out.append(s)
        else:
            out.append([s])
    return out


def mcp_send_message(api_url, token, project_id, message, retries=3):
    url = f"{api_url}/api/mcp/message"
    payload = {"message": message, "project_id": project_id}
    backoff = 60
    for attempt in range(retries):
        try:
            resp = httpx.post(url, json=payload, headers=_headers(token), timeout=120)
            if resp.status_code == 429:
                time.sleep(backoff * (attempt + 1))
                continue
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPStatusError:
            if attempt < retries - 1:
                time.sleep(5)
            else:
                raise
    raise RuntimeError(f"Failed after {retries} attempts")


def ingest_sessions(api_url, token, project_id, sessions, delay=1.0, session_delay=2.0, threshold=30):
    normalized = _normalize_sessions(sessions)
    total = 0
    for s_idx, turns in enumerate(normalized):
        prev = ""
        for t_idx, turn in enumerate(turns):
            if turn.get("role") != "user":
                continue
            content = turn["content"]
            if prev and len(content.strip()) <= threshold:
                message = f"[Context: {prev[:80]}] {content}"
            else:
                message = content
            mcp_send_message(api_url, token, project_id, message)
            total += 1
            prev = content
            if t_idx < len(turns) - 1:
                time.sleep(delay)
        if s_idx < len(normalized) - 1:
            time.sleep(session_delay)
    return total


def _get_instance_id(instance: dict) -> str:
    return instance.get("question_id") or instance.get("id", "")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run(config: BenchmarkConfig) -> None:
    dataset = load_dataset(config.dataset_path)
    if config.limit:
        dataset = dataset[:config.limit]

    output_dir = Path(config.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "mcp_agent_hypothesis.jsonl"

    done_ids: set[str] = set()
    if output_path.exists():
        with open(output_path) as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        done_ids.add(json.loads(line)["id"])
                    except (json.JSONDecodeError, KeyError):
                        pass
        logger.info(f"Resuming — {len(done_ids)} instances already done")

    with open(output_path, "a") as out_f:
        for idx, instance in enumerate(dataset):
            instance_id = _get_instance_id(instance) or str(idx)
            if instance_id in done_ids:
                logger.info(f"[{idx+1}/{len(dataset)}] Skipping {instance_id}")
                continue

            # Re-login before each instance
            jwt_token = login_jwt(config)
            mcp_token = login_oauth_pkce(config, scope="read write")

            question = instance.get("question", "")
            sessions = instance.get("haystack_sessions") or instance.get("sessions", [])

            logger.info(
                f"[{idx+1}/{len(dataset)}] Instance {instance_id} — "
                f"{len(sessions)} sessions, question: {question[:80]}"
            )

            project = create_project(
                api_url=config.api_url,
                token=jwt_token,
                name=f"bench-mcp-agent-{instance_id}",
                description=MCP_PROJECT_DESCRIPTION,
            )
            project_id = project["id"]

            total_msgs = ingest_sessions(
                api_url=config.api_url,
                token=mcp_token,
                project_id=project_id,
                sessions=sessions,
                delay=config.inter_message_delay_seconds,
                session_delay=config.inter_session_delay_seconds,
                threshold=config.short_turn_threshold,
            )

            wait_secs = min(
                config.graphiti_wait_base_seconds + config.graphiti_wait_per_message * total_msgs,
                config.graphiti_wait_max_seconds,
            )
            logger.info(f"Waiting {wait_secs:.0f}s for Graphiti to process {total_msgs} messages")
            time.sleep(wait_secs)

            # Agent loop — Gemini decides how to search
            answer, queries = ask_question_as_agent(
                api_url=config.api_url,
                mcp_token=mcp_token,
                project_id=project_id,
                question=question,
                model=config.gemini_model_for_synthesis,
            )

            record = {
                "id": instance_id,
                "answer": answer,
                "question": question,
                "queries_used": queries,
            }
            out_f.write(json.dumps(record, ensure_ascii=False) + "\n")
            out_f.flush()

            logger.info(f"  → Answer: {answer[:120]}")

    logger.info(f"Done. Results written to {output_path}")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="LongMemEval MCP Agent Test")
    parser.add_argument("--api-url", default="http://localhost:8000")
    parser.add_argument("--email", required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument("--dataset", help="Path to dataset JSON")
    parser.add_argument("--output-dir", help="Output directory")
    parser.add_argument("--limit", type=int, default=None)
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    cfg = BenchmarkConfig(
        api_url=args.api_url,
        email=args.email,
        password=args.password,
        limit=args.limit,
    )
    if args.dataset:
        cfg.dataset_path = args.dataset
    if args.output_dir:
        cfg.output_dir = args.output_dir
    run(cfg)
