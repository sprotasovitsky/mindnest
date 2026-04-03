"""Classifier benchmark: compare gemini-2.5-flash-lite vs 3.1-flash-lite (NONE/MINIMAL).

Runs all user messages from one instance through 3 classifier variants and reports:
- Speed (avg time per message)
- Tokens (input/output)
- Classification agreement (TYPE matches between models)

Usage:
    python3 -m benchmarks.longmemeval.test_classifier \
        --dataset benchmarks/longmemeval/data/test_5_new.json \
        --instance e47becba \
        --limit 50
"""

import argparse
import asyncio
import json
import time
from dataclasses import dataclass, field

from google import genai
from google.genai import types

from app.llm import _get_vertex_credentials
from app.config import get_settings
from app.prompts import load_prompt

CONCURRENCY = 10  # parallel requests per variant

CLASSIFIER_PROMPT_TEMPLATE = None  # loaded once

COT_SUFFIX = (
    "\n\nBefore answering, briefly explain your reasoning:\n"
    "1. What facts/data are present in the message?\n"
    "2. What questions are asked?\n"
    "Then give the final output in the required format."
)


def get_prompt(message: str, chat_history: str = "(no history)") -> str:
    global CLASSIFIER_PROMPT_TEMPLATE
    if CLASSIFIER_PROMPT_TEMPLATE is None:
        CLASSIFIER_PROMPT_TEMPLATE = load_prompt("classifier")
    return CLASSIFIER_PROMPT_TEMPLATE.format(
        message=message,
        user_name="Benchmark User",
        chat_history=chat_history,
    ) + COT_SUFFIX


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
    input_tokens: list[int] = field(default_factory=list)
    output_tokens: list[int] = field(default_factory=list)
    think_tokens: list[int] = field(default_factory=list)
    types: list[str] = field(default_factory=list)


async def classify_one(client, model, prompt, thinking_cfg, sem):
    async with sem:
        cfg_kwargs = {}
        if thinking_cfg:
            cfg_kwargs["thinking_config"] = thinking_cfg
        config = types.GenerateContentConfig(**cfg_kwargs) if cfg_kwargs else None
        for attempt in range(4):
            try:
                t0 = time.monotonic()
                resp = await client.aio.models.generate_content(
                    model=model, contents=prompt, config=config
                )
                elapsed = time.monotonic() - t0
                u = resp.usage_metadata
                think = getattr(u, "thoughts_token_count", 0) or 0
                msg_type = parse_type(resp.text or "")
                return elapsed, u.prompt_token_count, u.candidates_token_count, think, msg_type
            except Exception as e:
                if "429" in str(e) and attempt < 3:
                    await asyncio.sleep(5 * (attempt + 1))
                else:
                    raise


async def run_variant(client, model, thinking_cfg, messages, label) -> VariantResult:
    result = VariantResult(name=label)
    sem = asyncio.Semaphore(CONCURRENCY)
    print(f"  Running {label} ({len(messages)} messages)...")
    t_start = time.monotonic()
    tasks = [classify_one(client, model, msg, thinking_cfg, sem) for msg in messages]
    results = await asyncio.gather(*tasks)
    total = time.monotonic() - t_start
    for elapsed, inp, out, think, mtype in results:
        result.times.append(elapsed)
        result.input_tokens.append(inp)
        result.output_tokens.append(out)
        result.think_tokens.append(think)
        result.types.append(mtype)
    print(f"    Done in {total:.1f}s")
    return result


def print_report(variants: list[VariantResult]):
    baseline_types = variants[0].types

    print("\n" + "=" * 70)
    print(f"{'Metric':<30} " + "  ".join(f"{v.name:>12}" for v in variants))
    print("=" * 70)

    def row(label, values):
        print(f"{label:<30} " + "  ".join(f"{v:>12}" for v in values))

    n = len(variants[0].times)
    row("Messages", [f"{n}" for _ in variants])
    row(
        "Total time (s)",
        [f"{sum(v.times):.1f}" for v in variants],
    )
    row(
        "Avg time/msg (s)",
        [f"{sum(v.times)/len(v.times):.2f}" for v in variants],
    )
    row(
        "Avg input tokens",
        [f"{sum(v.input_tokens)/n:.0f}" for v in variants],
    )
    row(
        "Avg output tokens",
        [f"{sum(v.output_tokens)/n:.0f}" for v in variants],
    )
    row(
        "Avg think tokens",
        [f"{sum(v.think_tokens)/n:.0f}" for v in variants],
    )
    row(
        "Total input tokens",
        [f"{sum(v.input_tokens):,}" for v in variants],
    )
    row(
        "Total output tokens",
        [f"{sum(v.output_tokens):,}" for v in variants],
    )

    print("-" * 70)
    print("Classification types distribution:")
    for t in ("DATA", "QUESTION", "BOTH", "UNKNOWN"):
        counts = [v.types.count(t) for v in variants]
        row(f"  {t}", [f"{c} ({100*c/n:.0f}%)" for c in counts])

    print("-" * 70)
    print("Agreement with baseline (2.5-flash-lite):")
    for v in variants[1:]:
        matches = sum(1 for a, b in zip(baseline_types, v.types) if a == b)
        print(f"  {v.name}: {matches}/{n} ({100*matches/n:.0f}%)")

    print("=" * 70)

    # Per-type disagreements
    print("\nDisagreements (baseline vs 3.1):")
    for i, (base_type, msg_preview) in enumerate(
        zip(baseline_types, [""] * n)
    ):
        disagreed = [v for v in variants[1:] if v.types[i] != base_type]
        if disagreed:
            print(
                f"  msg#{i+1}: baseline={base_type} "
                + " ".join(f"{v.name}={v.types[i]}" for v in disagreed)
            )


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", default="benchmarks/longmemeval/data/test_5_new.json")
    parser.add_argument("--instance", default="e47becba")
    parser.add_argument("--limit", type=int, default=0, help="0=all messages")
    args = parser.parse_args()

    with open(args.dataset) as f:
        data = json.load(f)

    inst = next((d for d in data if d["question_id"] == args.instance), None)
    if not inst:
        print(f"Instance {args.instance} not found")
        return

    # Extract all user messages
    messages_raw = []
    for sess in inst["haystack_sessions"]:
        for turn in sess:
            if turn["role"] == "user":
                messages_raw.append(turn["content"])

    if args.limit:
        messages_raw = messages_raw[: args.limit]

    prompts = [get_prompt(m) for m in messages_raw]
    print(f"Instance: {args.instance} | Messages: {len(prompts)}")

    settings = get_settings()
    creds = _get_vertex_credentials()

    client_r = genai.Client(
        vertexai=True,
        project=settings.vertex_ai_project_id,
        location=settings.vertex_ai_location,
        credentials=creds,
    )
    client_g = genai.Client(
        vertexai=True,
        project=settings.vertex_ai_project_id,
        location="global",
        credentials=creds,
    )

    variants_cfg = [
        (client_r, "gemini-2.5-flash-lite", None, "2.5-flash-lite"),
        (client_g, "gemini-3.1-flash-lite-preview", None, "3.1-NONE"),
        (
            client_g,
            "gemini-3.1-flash-lite-preview",
            types.ThinkingConfig(thinking_level="MINIMAL"),
            "3.1-MINIMAL",
        ),
    ]

    results = []
    for client, model, thinking_cfg, label in variants_cfg:
        r = await run_variant(client, model, thinking_cfg, prompts, label)
        results.append(r)

    print_report(results)

    # Save raw results
    out_path = f"benchmarks/longmemeval/results/classifier_benchmark_{args.instance}.json"
    import os
    os.makedirs("benchmarks/longmemeval/results", exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(
            {
                "instance": args.instance,
                "n_messages": len(prompts),
                "variants": [
                    {
                        "name": r.name,
                        "times": r.times,
                        "input_tokens": r.input_tokens,
                        "output_tokens": r.output_tokens,
                        "think_tokens": r.think_tokens,
                        "types": r.types,
                    }
                    for r in results
                ],
            },
            f,
            indent=2,
        )
    print(f"\nRaw results saved to {out_path}")


if __name__ == "__main__":
    asyncio.run(main())
