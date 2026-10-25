"""Check how often the LLM judge agrees with hand-labelled cases.

Usage (inside the API container):

    python -m evaluation.judge_check
"""

import argparse
import json
from pathlib import Path

from config import JUDGE_MODEL, JUDGE_PROVIDER
from evaluation.judge import AnswerJudge
from providers.factory import build_chat_client

DEFAULT_CASES = Path(__file__).parent / "datasets" / "judge_cases.jsonl"


def load_cases(path: str | Path) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def decide(judge: AnswerJudge, case: dict) -> bool | None:
    """Ask the judge the one criterion a case is labelled for."""

    if case["criterion"] == "correct":
        return judge.is_correct(case["question"], case["answer"], case["reference"])

    if case["criterion"] == "grounded":
        return judge.is_grounded(case["answer"], case["passages"])

    if case["criterion"] == "citations":
        return judge.citations_supported(case["answer"], case["passages"])

    raise ValueError(f"Unknown criterion in case {case['id']}: {case['criterion']}")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="python -m evaluation.judge_check",
        description="Check the LLM judge against labelled cases.",
    )
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES)
    args = parser.parse_args()

    judge = AnswerJudge(
        client=build_chat_client(provider=JUDGE_PROVIDER, model=JUDGE_MODEL)
    )
    cases = load_cases(args.cases)

    print(f"Judge: {JUDGE_PROVIDER}/{JUDGE_MODEL}\n")
    print("| Case | Criterion | Expected | Judge | Agrees |")
    print("|---|---|---|---|---|")

    agreed = 0

    for case in cases:
        decision = decide(judge, case)
        agrees = decision == case["expected"]
        agreed += agrees

        print(
            f"| {case['id']} | {case['criterion']} | "
            f"{_label(case['expected'])} | {_label(decision)} | "
            f"{'yes' if agrees else 'NO'} |"
        )

    print(f"\nAgreement: {agreed}/{len(cases)}")


def _label(decision: bool | None) -> str:
    return "no decision" if decision is None else ("YES" if decision else "NO")


if __name__ == "__main__":
    main()
