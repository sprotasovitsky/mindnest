"""Test different classifier prompt variants for list preservation.

Run from backend-python/:
    python -m benchmarks.classifier_variants_test
"""
import asyncio
import re
from pathlib import Path
from app.llm import generate_text
from app.config import get_settings

settings = get_settings()

# ── Test messages ──────────────────────────────────────────────────────────────

VIKA_MSG = """Done with shopping! Expenses:
- Duck - 1500 rubles
- Potatoes 3kg - 150 rubles
- Tomatoes 1kg - 300 rubles
- Cucumbers 0.5kg - 150 rubles
- Herring 500g - 350 rubles
- Olivier ingredients - 800 rubles
- Mandarin oranges 3kg - 450 rubles
- Cheese platter - 900 rubles
- Crackers - 200 rubles
- Olives - 300 rubles
Total: 5100 rubles
My task is done!"""

DEPS_MSG = """Project dependencies:
1. Feature A DEPENDS_ON Task X
2. Feature A DEPENDS_ON Task Y
3. Feature B DEPENDS_ON Task Z
4. Task Y DEPENDS_ON Design D
5. Decision E RELATES_TO Feature B
6. Bug F RELATES_TO Decision E
Save all these links."""

# Realistic Vika chat history (only her own messages, last 3 pairs)
VIKA_HISTORY = """[User]: For hot dishes, let's add: duck for roasting - 1 piece (about 2.5 kg), potatoes - 3 kg for baking, vegetables for salad - tomatoes 1 kg, cucumbers 0.5 kg. Also herring for shuba salad - 500g.
[Assistant]: Got it, Vika. I have updated the shopping list with your additions.

[User]: 6 bottles of champagne is not enough for 4 people. Change it to 10 bottles. Also add sparkling water - 6 bottles and regular water - 4 bottles.
[Assistant]: Understood, Vika. Updated the shopping list accordingly.

[User]: How many items do I need to buy in total? List them please.
[Assistant]: Based on the updated list, here are all 30 categories: Champagne (10), Sparkling water (6), Regular water (4), Vodka (2), Red wine (3), White wine (2), Duck, Potatoes, Olivier ingredients, Herring, Tomatoes, Cucumbers, Mandarin oranges, Cheese platter, Crackers, Olives, Napoleon cake, Ice cream, Chocolate candies, Balloons, Garland lights, Napkins, Fireworks, Cups, Plates, Garbage bags, Ornaments, Monopoly, Uno cards, Karaoke."""

EMPTY_HISTORY = ""

# ── Prompt variants ────────────────────────────────────────────────────────────

BASE_PROMPT = Path("app/prompts/classifier.txt").read_text()

VARIANT_A = BASE_PROMPT  # current

VARIANT_B = BASE_PROMPT.replace(
    "- PRESERVE ALL ITEMS in structured lists — numbered lists, task lists, relationship declarations, expense lists. Never summarize a list to just its header. Every item must appear in DATA_TO_SAVE.",
    "- For messages that contain a list (numbered or bulleted), COPY THE ENTIRE LIST VERBATIM into DATA_TO_SAVE. Do not rephrase, do not skip any line, do not summarize. Every single line of the original list must appear in DATA_TO_SAVE."
)

# V3: instruct to use original message as-is for pure data lists
VARIANT_C = BASE_PROMPT.replace(
    "- PRESERVE ALL ITEMS in structured lists — numbered lists, task lists, relationship declarations, expense lists. Never summarize a list to just its header. Every item must appear in DATA_TO_SAVE.",
    "- For messages consisting primarily of a list (expenses, tasks, relationships, purchases): set DATA_TO_SAVE to the COMPLETE original message text unchanged. Do not reformat, do not condense, do not drop any item."
)

# V4: count items before writing
VARIANT_D = BASE_PROMPT.replace(
    "- PRESERVE ALL ITEMS in structured lists — numbered lists, task lists, relationship declarations, expense lists. Never summarize a list to just its header. Every item must appear in DATA_TO_SAVE.",
    "- PRESERVE ALL ITEMS in structured lists — numbered lists, task lists, relationship declarations, expense lists. Never summarize a list to just its header. Every item must appear in DATA_TO_SAVE.\n- Before writing DATA_TO_SAVE for a list: count the items in the original list, then verify your DATA_TO_SAVE contains exactly that many items."
)

# V7: self-check after writing
VARIANT_G = BASE_PROMPT.replace(
    "- PRESERVE ALL ITEMS in structured lists — numbered lists, task lists, relationship declarations, expense lists. Never summarize a list to just its header. Every item must appear in DATA_TO_SAVE.",
    "- PRESERVE ALL ITEMS in structured lists — numbered lists, task lists, relationship declarations, expense lists. Never summarize a list to just its header. Every item must appear in DATA_TO_SAVE.\n- After writing DATA_TO_SAVE, verify: if the original message contained a list, does DATA_TO_SAVE contain every item? If any item is missing, rewrite DATA_TO_SAVE with all items included."
)

VARIANTS = {
    "V1_current": VARIANT_A,
    "V2_verbatim": VARIANT_B,
    "V3_original": VARIANT_C,
    "V4_count": VARIANT_D,
    "V7_selfcheck": VARIANT_G,
}

# ── Runner ─────────────────────────────────────────────────────────────────────

def build_prompt(template: str, message: str, user_name: str, chat_history: str) -> str:
    return (template
            .replace("{message}", message)
            .replace("{user_name}", user_name)
            .replace("{chat_history}", chat_history or "none"))


def parse_data_to_save(response: str) -> str:
    for line in response.strip().splitlines():
        if line.strip().startswith("DATA_TO_SAVE:"):
            val = line.split(":", 1)[1].strip()
            return "" if val.lower() == "none" else val
    return ""


async def run_variant(name: str, template: str, message: str, history: str,
                      checks: list[str], n: int = 8):
    prompt = build_prompt(template, message, "Vika", history)
    passes = 0
    results = []
    for i in range(n):
        raw = await generate_text(prompt, model=settings.llm_model)
        saved = parse_data_to_save(raw)
        ok = all(c.lower() in saved.lower() for c in checks)
        passes += ok
        results.append(("✓" if ok else "✗", len(saved), saved[-60:]))

    print(f"\n  {name}: {passes}/{n} passed")
    for i, (sym, ln, tail) in enumerate(results):
        print(f"    [{sym}] run{i+1} len={ln} …{repr(tail)}")
    return passes


async def main():
    tests = [
        ("Vika expenses (olives check)", VIKA_MSG, VIKA_HISTORY, ["olives"]),
        ("Vika expenses no history",     VIKA_MSG, EMPTY_HISTORY, ["olives"]),
        ("Dependencies list",            DEPS_MSG, EMPTY_HISTORY,
         ["Feature A", "Decision E", "Bug F"]),
    ]

    for test_name, msg, history, checks in tests:
        print(f"\n{'='*60}")
        print(f"TEST: {test_name}")
        print(f"Checks: {checks}")
        totals = {}
        for vname, template in VARIANTS.items():
            score = await run_variant(vname, template, msg, history, checks)
            totals[vname] = score

        print(f"\n  SUMMARY: {totals}")

    print("\nDone.")


if __name__ == "__main__":
    asyncio.run(main())
