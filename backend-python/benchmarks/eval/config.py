"""Configuration for evaluation pipeline (Layer 7).

Uses Gemini as the LLM judge for both DeepEval and Ragas evaluations.
Dataset: 5 questions from the existing LongMemEval test set.
"""

import os

# LLM judge model — use fast model for evaluation to keep costs down
JUDGE_MODEL = "gemini-2.5-flash"

# Fixed set of 5 question IDs from test_5_new.json for regression testing.
# These IDs are stable and used as the baseline for comparison.
REGRESSION_QUESTION_IDS = [
    "e47becba",
    "51a45a95",
    "1e043500",
    "a3f9c12d",
    "b2c3d4e5",
]

# API endpoint for the running backend
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

# Path to the LongMemEval dataset
DATASET_PATH = "benchmarks/longmemeval/data/test_5_new.json"

# Results directory
RESULTS_DIR = "benchmarks/eval/results"

# Minimum acceptable scores for regression (fail if below these)
MIN_ANSWER_RELEVANCY = 0.6
MIN_FAITHFULNESS = 0.5
MIN_CONTEXT_RECALL = 0.5
