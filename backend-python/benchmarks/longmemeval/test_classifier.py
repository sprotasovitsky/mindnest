"""Classifier benchmark: compare gemini-2.5-flash-lite vs 3.1-flash-lite (NONE/MINIMAL).

Uses the exact same code path as production classifier (generate_text from app.llm).
History: sliding window of last 4 user+assistant pairs from the dataset.

Usage:
    python3 -m benchmarks.longmemeval.test_classifier \
        --dataset benchmarks/longmemeval/data/test_5_new.json \
        --instance e47becba
"""

import argparse
import asyncio
import json
import time
from dataclasses import dataclass, field

from app.llm import generate_text
from app.config import get_settings
from app.prompts import load_prompt

CLASSIFIER_HISTORY_LIMIT = 4  # must match app/routers/chat.py

COT_SUFFIX = (
    "\n\nBefore answering, briefly explain your reasoning:\n"
    "1. What facts/data are present in the message?\n"
    "2. What questions are asked?\n"
    "Then give the final output in the required format."
)


def format_history(pairs: list[tuple[str, str]]) -> str:
    """Format last N user+assistant pairs exactly like production classifier."""
    recent = pairs[-CLASSIFIER_HISTORY_LIMIT:]
    lines = []
    for user_msg, assistant_msg in recent:
        lines.append(f"[User]: {user_msg}")
        lines.append(f"[Assistant]: {assistant_msg}")
        lines.append("")
    return "\n".join(lines)


def build_prompts(instance: dict) -> list[str]:
    """Build prompt strings from dataset instance.

    Iterates through all sessions and turns, maintaining a sliding window
    of the last 4 user+assistant pairs as chat_history — same as production.
    Returns list of full prompt strings for every user turn.
    """
    template = load_prompt("classifier")
    history_pairs: list[tuple[str, str]] = []  # (user_msg, assistant_reply)
    prompts = []

    for sess in instance["haystack_sessions"]:
        turns = sess  # list of {"role": ..., "content": ...}
        i = 0
        while i < len(turns):
            turn = turns[i]
            if turn["role"] != "user":
                i += 1
                continue

            message = turn["content"]
            chat_history = format_history(history_pairs) if history_pairs else "(no history)"

            prompt = template.format(
                message=message,
                user_name="Benchmark User",
                chat_history=chat_history,
            ) + COT_SUFFIX
            prompts.append(prompt)

            # Find paired assistant reply for history
            assistant_reply = ""
            if i + 1 < len(turns) and turns[i + 1]["role"] == "assistant":
                assistant_reply = turns[i + 1]["content"][:200]  # truncate for history
                i += 2
            else:
                i += 1

            history_pairs.append((message, assistant_reply))

    return prompts


def parse_type(response: str) -> str:
    for line in response.strip().split("\n"):
        line = line.strip()
        if line.startswith("TYPE:"):
            t = line.replace("TYPE:", "").strip().upper()
            if t in ("DATA", "QUESTION", "BOTH"):
                return t
    return "UNKNOWN"


@dataclass
class VariantResult:
    name: str
    times: list[float] = field(default_factory=list)
    types: list[str] = field(default_factory=list)


async def classify_one(model: str, thinking_level: str, prompt: str) -> tuple[float, str]:
    """Call generate_text exactly like production classifier does."""
    settings = get_settings()
    old_thinking = settings.llm_thinking_level
    settings.llm_thinking_level = thinking_level

    t0 = time.monotonic()
    try:
        response = await generate_text(prompt, model=model)
    finally:
        settings.llm_thinking_level = old_thinking

    elapsed = time.monotonic() - t0
    return elapsed, parse_type(response)


async def run_variant(model: str, thinking_level: str, prompts: list[str], label: str) -> VariantResult:
    result = VariantResult(name=label)
    print(f"  Running {label} ({len(prompts)} messages, sequential)...")
    t_start = time.monotonic()
    for i, prompt in enumerate(prompts):
        elapsed, mtype = await classify_one(model, thinking_level, prompt)
        result.times.append(elapsed)
        result.types.append(mtype)
        if (i + 1) % 50 == 0:
            print(f"    {i+1}/{len(prompts)} done...")
        await asyncio.sleep(3)
    print(f"    Done in {time.monotonic()-t_start:.1f}s")
    return result


def print_report(variants: list[VariantResult]):
    baseline = variants[0]
    n = len(baseline.times)

    print("\n" + "=" * 72)
    print(f"{'Metric':<32} " + "  ".join(f"{v.name:>12}" for v in variants))
    print("=" * 72)

    def row(label, values):
        print(f"{label:<32} " + "  ".join(f"{v:>12}" for v in values))

    row("Messages", [str(n)] * len(variants))
    row("Total time (s)", [f"{sum(v.times):.1f}" for v in variants])
    row("Avg time/msg (s)", [f"{sum(v.times)/n:.2f}" for v in variants])

    print("-" * 72)
    print("Type distribution:")
    for t in ("DATA", "QUESTION", "BOTH", "UNKNOWN"):
        counts = [v.types.count(t) for v in variants]
        row(f"  {t}", [f"{c} ({100*c/n:.0f}%)" for c in counts])

    print("-" * 72)
    print("Agreement with 2.5-flash-lite baseline:")
    for v in variants[1:]:
        matches = sum(1 for a, b in zip(baseline.types, v.types) if a == b)
        print(f"  {v.name}: {matches}/{n} ({100*matches/n:.0f}%)")

    print("=" * 72)


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", default="benchmarks/longmemeval/data/test_5_new.json")
    parser.add_argument("--instance", default="e47becba")
    args = parser.parse_args()

    with open(args.dataset) as f:
        data = json.load(f)

    inst = next((d for d in data if d["question_id"] == args.instance), None)
    if not inst:
        print(f"Instance {args.instance} not found")
        return

    prompts = build_prompts(inst)
    # Skip first 4 so history window is always full (4 pairs), then take 100
    prompts = prompts[4:104]

    print(f"Instance: {args.instance} | Messages: {len(prompts)}")

    # (model, thinking_level, label)
    # thinking_level is patched into settings before each call — same path as production
    variants = [
        ("gemini-2.5-flash-lite", "NONE", "2.5-flash-lite"),
        ("gemini-3.1-flash-lite-preview", "NONE", "3.1-NONE"),
        ("gemini-3.1-flash-lite-preview", "MINIMAL", "3.1-MINIMAL"),
    ]

    results = []
    for model, thinking_level, label in variants:
        r = await run_variant(model, thinking_level, prompts, label)
        results.append(r)

    print_report(results)

    out_path = f"benchmarks/longmemeval/results/classifier_benchmark_{args.instance}.json"
    with open(out_path, "w") as f:
        json.dump({
            "instance": args.instance,
            "n_messages": len(prompts),
            "variants": [{
                "name": r.name,
                "times": r.times,
                "types": r.types,
            } for r in results],
        }, f, indent=2)
    print(f"\nSaved to {out_path}")


if __name__ == "__main__":
    asyncio.run(main())
