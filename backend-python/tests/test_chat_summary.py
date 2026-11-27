"""Unit tests for GET /api/chat/summary.

The LLM, Langfuse, database session and auth are all mocked, so these tests
need no running server, Neo4j or PostgreSQL.
"""

from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.database import get_db
from app.dependencies import get_current_user
from app.prompts import clear_prompt_cache
from app.routers import chat

PROJECT_ID = "11111111-1111-1111-1111-111111111111"
USER_ID = "22222222-2222-2222-2222-222222222222"
OTHER_USER_ID = "33333333-3333-3333-3333-333333333333"


def _project(member_ids: list[str]) -> SimpleNamespace:
    return SimpleNamespace(
        id=PROJECT_ID,
        description="Test project",
        members=[SimpleNamespace(user_id=uid) for uid in member_ids],
    )


def _message(user_message: str, assistant_reply: str) -> SimpleNamespace:
    return SimpleNamespace(
        user_message=user_message,
        assistant_reply=assistant_reply,
        created_at=datetime(2026, 11, 25, 10, 30, tzinfo=timezone.utc),
    )


def _make_db(project) -> MagicMock:
    """Mock AsyncSession whose execute() resolves the project lookup."""
    db = MagicMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = project
    db.execute = AsyncMock(return_value=result)
    db.commit = AsyncMock()
    return db


@pytest.fixture(autouse=True)
def no_rate_limit():
    """Disable the shared chat rate limiter (30/min in prod config) for tests."""
    previous = chat.limiter.enabled
    chat.limiter.enabled = False
    yield
    chat.limiter.enabled = previous


@pytest.fixture
def user():
    return SimpleNamespace(
        id=USER_ID, name="Alice", email_verified=False, tokens_used=0,
    )


@pytest.fixture
def langfuse():
    """Mock Langfuse client; get_prompt fails so prompts load from .txt files."""
    lf = MagicMock()
    lf.get_prompt.side_effect = Exception("not in Langfuse")
    clear_prompt_cache()
    with patch("app.langfuse_client.get_langfuse", return_value=lf):
        yield lf
    clear_prompt_cache()


@pytest.fixture
def llm():
    with patch("app.routers.chat.generate_text", new_callable=AsyncMock) as mock:
        yield mock


def _client(user, db) -> TestClient:
    app = FastAPI()
    app.state.limiter = chat.limiter
    app.include_router(chat.router)
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_db] = lambda: db
    return TestClient(app)


def _patch_messages(messages):
    return patch(
        "app.routers.chat.get_messages_since",
        new_callable=AsyncMock,
        return_value=messages,
    )


class TestChatSummaryEndpoint:

    def test_empty_history_returns_empty_summary_without_llm(self, user, langfuse, llm):
        db = _make_db(_project([USER_ID]))
        with _patch_messages([]) as get_msgs:
            resp = _client(user, db).get(
                "/api/chat/summary", params={"project_id": PROJECT_ID},
            )

        assert resp.status_code == 200
        assert resp.json() == {
            "summary": "",
            "key_topics": [],
            "message_count": 0,
            "period_days": 7,
        }
        llm.assert_not_called()
        langfuse.trace.assert_not_called()
        assert user.tokens_used == 0
        # Only the current user's messages are requested
        args = get_msgs.await_args.args
        assert args[1] == PROJECT_ID
        assert args[2] == USER_ID

    def test_summary_happy_path(self, user, langfuse, llm):
        db = _make_db(_project([USER_ID]))
        llm.return_value = (
            '{"summary": "Alice planned a trip to Lisbon. She booked flights. '
            'She asked about hotels.", '
            '"key_topics": ["Lisbon trip", "flights", "hotels", "flights", '
            '"budget", "packing", "visa"]}'
        )
        messages = [
            _message("I'm going to Lisbon in May", "Got it!"),
            _message("Booked flights for May 3rd", "Noted."),
            _message("Which hotels did I consider?", "You haven't mentioned any yet."),
        ]

        with _patch_messages(messages):
            resp = _client(user, db).get(
                "/api/chat/summary",
                params={"project_id": PROJECT_ID, "days": 14},
            )

        assert resp.status_code == 200
        body = resp.json()
        assert body["summary"].startswith("Alice planned a trip to Lisbon.")
        # Deduplicated and capped at 5
        assert body["key_topics"] == ["Lisbon trip", "flights", "hotels", "budget", "packing"]
        assert body["message_count"] == 3
        assert body["period_days"] == 14

        # LLM call is traced like regular chat
        llm.assert_awaited_once()
        prompt = llm.await_args.args[0]
        assert "Booked flights for May 3rd" in prompt
        assert "last 14 day(s)" in prompt
        kwargs = llm.await_args.kwargs
        assert kwargs["step"] == "chat_summary"
        assert kwargs["prompt_name"] == "chat_summary"
        assert kwargs["project_id"] == PROJECT_ID
        assert kwargs["user_id"] == USER_ID
        trace_id = kwargs["trace_id"]
        assert trace_id

        # Langfuse trace is created with the same trace_id, then updated with output
        trace_calls = langfuse.trace.call_args_list
        assert trace_calls[0].kwargs["id"] == trace_id
        assert trace_calls[0].kwargs["name"] == "chat_summary"
        assert trace_calls[0].kwargs["user_id"] == USER_ID
        assert trace_calls[-1].kwargs["id"] == trace_id
        assert trace_calls[-1].kwargs["output"]["message_count"] == 3

        # Token usage recorded for unverified user
        assert user.tokens_used == (len(prompt) + len(llm.return_value)) // 4
        db.commit.assert_awaited()

    def test_summary_handles_fenced_json(self, user, langfuse, llm):
        db = _make_db(_project([USER_ID]))
        llm.return_value = '```json\n{"summary": "Short recap.", "key_topics": ["work"]}\n```'
        with _patch_messages([_message("hi", "hello")]):
            resp = _client(user, db).get(
                "/api/chat/summary", params={"project_id": PROJECT_ID},
            )
        assert resp.status_code == 200
        assert resp.json()["summary"] == "Short recap."
        assert resp.json()["key_topics"] == ["work"]

    def test_summary_falls_back_to_raw_text_on_invalid_json(self, user, langfuse, llm):
        db = _make_db(_project([USER_ID]))
        llm.return_value = "The user talked about work."
        with _patch_messages([_message("hi", "hello")]):
            resp = _client(user, db).get(
                "/api/chat/summary", params={"project_id": PROJECT_ID},
            )
        assert resp.status_code == 200
        assert resp.json()["summary"] == "The user talked about work."
        assert resp.json()["key_topics"] == []

    def test_llm_failure_returns_502_without_charging_tokens(self, user, langfuse, llm):
        db = _make_db(_project([USER_ID]))
        llm.side_effect = RuntimeError("vertex down")
        with _patch_messages([_message("hi", "hello")]):
            resp = _client(user, db).get(
                "/api/chat/summary", params={"project_id": PROJECT_ID},
            )
        assert resp.status_code == 502
        assert user.tokens_used == 0

    @pytest.mark.parametrize("days", [0, -1, 31, 100])
    def test_days_out_of_range_rejected(self, user, langfuse, llm, days):
        db = _make_db(_project([USER_ID]))
        with _patch_messages([_message("hi", "hello")]) as get_msgs:
            resp = _client(user, db).get(
                "/api/chat/summary",
                params={"project_id": PROJECT_ID, "days": days},
            )
        assert resp.status_code == 422
        get_msgs.assert_not_called()
        llm.assert_not_called()

    @pytest.mark.parametrize("days", [1, 30])
    def test_days_boundaries_accepted(self, user, langfuse, llm, days):
        db = _make_db(_project([USER_ID]))
        with _patch_messages([]):
            resp = _client(user, db).get(
                "/api/chat/summary",
                params={"project_id": PROJECT_ID, "days": days},
            )
        assert resp.status_code == 200
        assert resp.json()["period_days"] == days

    def test_foreign_project_forbidden(self, user, langfuse, llm):
        db = _make_db(_project([OTHER_USER_ID]))
        with _patch_messages([_message("secret", "ok")]) as get_msgs:
            resp = _client(user, db).get(
                "/api/chat/summary", params={"project_id": PROJECT_ID},
            )
        assert resp.status_code == 403
        get_msgs.assert_not_called()
        llm.assert_not_called()

    def test_unknown_project_not_found(self, user, langfuse, llm):
        db = _make_db(None)
        with _patch_messages([]):
            resp = _client(user, db).get(
                "/api/chat/summary", params={"project_id": PROJECT_ID},
            )
        assert resp.status_code == 404
        llm.assert_not_called()

    def test_token_limit_exceeded(self, user, langfuse, llm):
        user.tokens_used = 10**9
        db = _make_db(_project([USER_ID]))
        with _patch_messages([_message("hi", "hello")]):
            resp = _client(user, db).get(
                "/api/chat/summary", params={"project_id": PROJECT_ID},
            )
        assert resp.status_code == 403
        assert resp.json()["detail"]["error"] == "token_limit_exceeded"
        llm.assert_not_called()


class TestGetMessagesSince:

    @pytest.mark.asyncio
    async def test_query_filters_by_project_user_and_period(self):
        result = MagicMock()
        newest_first = [_message("second", "b"), _message("first", "a")]
        result.scalars.return_value.all.return_value = newest_first
        db = MagicMock()
        db.execute = AsyncMock(return_value=result)
        since = datetime(2026, 11, 20, tzinfo=timezone.utc)

        messages = await chat.get_messages_since(db, PROJECT_ID, USER_ID, since)

        # Returned oldest first
        assert [m.user_message for m in messages] == ["first", "second"]
        query = db.execute.await_args.args[0]
        sql = str(query)
        assert "chat_messages.project_id" in sql
        assert "chat_messages.user_id" in sql
        assert "chat_messages.created_at >=" in sql
        params = query.compile().params
        assert PROJECT_ID in params.values()
        assert USER_ID in params.values()
        assert since in params.values()
        assert chat.SUMMARY_MAX_MESSAGES in params.values()
