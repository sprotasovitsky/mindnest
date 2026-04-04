"""LongMemEval evaluation with Gemini as LLM judge.

Reimplements the upstream evaluate_qa.py logic using google-genai (Gemini)
instead of OpenAI, and maps our JSONL format (id/answer) to the expected
format (question_id/hypothesis) automatically.

Usage:
    # Requires VERTEX_AI env vars (same as backend .env)
    source .env
    python -m benchmarks.longmemeval.evaluate \
        --hypothesis results/chat_hypothesis.jsonl \
        --reference data/longmemeval_s_cleaned.json

    python -m benchmarks.longmemeval.evaluate \
        --hypothesis results/mcp_hypothesis.jsonl \
        --reference data/longmemeval_s_cleaned.json \
        --label "MCP test"
"""

import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path

import numpy as np
from google import genai
from google.genai import types
from google.oauth2 import service_account

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s — %(message)s")
logger = logging.getLogger(__name__)

DEFAULT_REFERENCE = Path(__file__).parent / "data" / "longmemeval_s_cleaned.json"
DEFAULT_MODEL = "gemini-3.1-flash-lite-preview"


# ---------------------------------------------------------------------------
# Gemini client
# ---------------------------------------------------------------------------

_client = None


def _get_client() -> genai.Client:
    global _client
    if _client is not None:
        return _client

    project = os.environ.get("VERTEX_AI_PROJECT_ID", "")
    location = "global"  # gemini-3.1 models require global endpoint
    sa_email = os.environ.get("GCP_SERVICE_ACCOUNT_EMAIL", "")
    private_key = os.environ.get("GCP_PRIVATE_KEY", "").replace("\\n", "\n")

    if not project or not sa_email or not private_key:
        raise RuntimeError(
            "Vertex AI credentials not set. Export: "
            "VERTEX_AI_PROJECT_ID, GCP_SERVICE_ACCOUNT_EMAIL, GCP_PRIVATE_KEY"
        )

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


def _judge(prompt: str, model: str) -> str:
    """Call Gemini and return the response text."""
    client = _get_client()
    for attempt in range(3):
        try:
            config = types.GenerateContentConfig(
                thinking_config=types.ThinkingConfig(thinking_level="MEDIUM"),
            )
            resp = client.models.generate_content(model=model, contents=prompt, config=config)
            return resp.text.strip()
        except Exception as e:
            if attempt < 2:
                logger.warning(f"Judge call failed, retrying: {e}")
                time.sleep(2 ** attempt)
            else:
                raise


# ---------------------------------------------------------------------------
# Prompts (same as upstream evaluate_qa.py)
# ---------------------------------------------------------------------------

def _get_prompt(task: str, question: str, answer: str, response: str, abstention: bool = False) -> str:
    if abstention:
        return (
            "I will give you an unanswerable question, an explanation, and a response from a model. "
            "Please answer yes if the model correctly identifies the question as unanswerable. "
            "The model could say that the information is incomplete, or some other information is "
            "given but the asked information is not.\n\n"
            f"Question: {question}\n\nExplanation: {answer}\n\nModel Response: {response}\n\n"
            "Does the model correctly identify the question as unanswerable? Answer yes or no only."
        )

    base = (
        "I will give you a question, a correct answer, and a response from a model. "
        "Please answer yes if the response contains the correct answer. Otherwise, answer no. "
        "If the response is equivalent to the correct answer or contains all the intermediate "
        "steps to get the correct answer, you should also answer yes. "
        "If the response only contains a subset of the information required by the answer, answer no."
    )

    if task == "temporal-reasoning":
        base += (
            " In addition, do not penalize off-by-one errors for the number of days. "
            "If the question asks for the number of days/weeks/months, etc., and the model "
            "makes off-by-one errors (e.g., predicting 19 days when the answer is 18), "
            "the model's response is still correct."
        )
    elif task == "knowledge-update":
        base = (
            "I will give you a question, a correct answer, and a response from a model. "
            "Please answer yes if the response contains the correct answer. Otherwise, answer no. "
            "If the response contains some previous information along with an updated answer, "
            "the response should be considered as correct as long as the updated answer is the required answer."
        )
    elif task == "single-session-preference":
        return (
            "I will give you a question, a rubric for desired personalized response, and a response "
            "from a model. Please answer yes if the response satisfies the desired response. "
            "Otherwise, answer no. The model does not need to reflect all the points in the rubric. "
            "The response is correct as long as it recalls and utilizes the user's personal information correctly.\n\n"
            f"Question: {question}\n\nRubric: {answer}\n\nModel Response: {response}\n\n"
            "Is the model response correct? Answer yes or no only."
        )

    return (
        f"{base}\n\n"
        f"Question: {question}\n\nCorrect Answer: {answer}\n\nModel Response: {response}\n\n"
        "Is the model response correct? Answer yes or no only."
    )


# ---------------------------------------------------------------------------
# Main evaluation
# ---------------------------------------------------------------------------

def load_hypotheses(path: Path) -> list[dict]:
    """Load JSONL hypothesis file, mapping our format to upstream format."""
    entries = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            entries.append({
                "question_id": obj.get("question_id") or obj.get("id"),
                "hypothesis": obj.get("hypothesis") or obj.get("answer"),
            })
    return entries


def load_references(path: Path) -> list[dict]:
    with open(path) as f:
        return json.load(f)


def evaluate(
    hypothesis_path: Path,
    reference_path: Path,
    model: str = DEFAULT_MODEL,
    label: str = "",
) -> None:
    hypotheses = load_hypotheses(hypothesis_path)
    references = load_references(reference_path)

    qid2data = {r["question_id"]: r for r in references}
    qid2type = {r["question_id"]: r["question_type"] for r in references}
    qtypes = set(qid2type.values())
    qtype2acc: dict[str, list[int]] = {t: [] for t in qtypes}

    result_path = Path(str(hypothesis_path) + f".eval-results-gemini")
    tag = f"[{label}] " if label else ""
    logger.info(f"{tag}Evaluating {len(hypotheses)} hypotheses with {model}")

    results = []
    with open(result_path, "w") as out_f:
        for i, entry in enumerate(hypotheses):
            qid = entry["question_id"]
            if qid not in qid2data:
                logger.warning(f"Skipping {qid}: not in reference data")
                continue

            ref = qid2data[qid]
            qtype = qid2type[qid]
            question = ref["question"]
            answer = ref["answer"]
            hypothesis = entry["hypothesis"]
            abstention = "_abs" in qid

            prompt = _get_prompt(qtype, question, answer, hypothesis, abstention)
            eval_response = _judge(prompt, model)
            label_correct = "yes" in eval_response.lower()

            entry["autoeval_label"] = {"model": model, "label": label_correct}
            results.append(entry)
            qtype2acc[qtype].append(1 if label_correct else 0)

            out_f.write(json.dumps(entry) + "\n")

            status = "CORRECT" if label_correct else "WRONG"
            logger.info(
                f"  [{i+1}/{len(hypotheses)}] {status} | {qtype} | "
                f"Q: {question[:60]} | A: {answer[:40]} | H: {hypothesis[:40]}"
            )

    # Print results
    overall = np.mean([1 if r["autoeval_label"]["label"] else 0 for r in results]).item()
    print(f"\n{tag}Overall accuracy: {overall:.4f} ({len(results)} questions)")
    for qtype in sorted(qtype2acc.keys()):
        scores = qtype2acc[qtype]
        if scores:
            print(f"  {qtype}: {np.mean(scores):.4f} ({len(scores)})")

    print(f"\nResults saved to {result_path}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="LongMemEval Evaluation (Gemini judge)")
    parser.add_argument("--hypothesis", required=True, help="Path to hypothesis JSONL")
    parser.add_argument("--reference", default=str(DEFAULT_REFERENCE), help="Path to reference JSON")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Gemini model for judging")
    parser.add_argument("--label", default="", help="Label for logging")
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    evaluate(
        hypothesis_path=Path(args.hypothesis),
        reference_path=Path(args.reference),
        model=args.model,
        label=args.label,
    )
