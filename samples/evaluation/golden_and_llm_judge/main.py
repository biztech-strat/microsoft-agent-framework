import asyncio
import argparse
import json
import unicodedata
from pathlib import Path
import sys
from typing import Any, Dict, List

# Ensure repo root on sys.path
_here = Path(__file__).resolve()
for _p in (_here.parent, *_here.parents):
    if (_p / "samples").is_dir() and (_p / "python").is_dir():
        if str(_p) not in sys.path:
            sys.path.insert(0, str(_p))
        break

from samples._shared import ensure_repo_on_sys_path, setup_logging

ensure_repo_on_sys_path()

from agent_framework.azure import AzureOpenAIResponsesClient
from azure.identity import AzureCliCredential


def normalize(s: str) -> str:
    # 大文字小文字/全角半角/空白を正規化
    s = unicodedata.normalize("NFKC", s).lower()
    s = " ".join(s.split())
    return s


def load_golden(case: str) -> List[Dict[str, Any]]:
    data = json.loads((Path(__file__).parent / "golden.json").read_text(encoding="utf-8"))
    return data[case]


async def run_case(case: str) -> None:
    agent = AzureOpenAIResponsesClient(credential=AzureCliCredential()).create_agent(
        name="EvalAgent",
        instructions="Answer concisely in Japanese.",
    )
    tests = load_golden(case)
    passed = 0
    for t in tests:
        out = await agent.run(t["input"])
        text = out.text
        ok = all(normalize(k) in normalize(text) for k in t.get("expect_contains", []))
        print({"id": t["id"], "pass": ok})
        if ok:
            passed += 1
    print(f"summary: {passed}/{len(tests)} passed")


async def judge_case(case: str, threshold: float) -> None:
    # 採点用の別エージェント
    judge = AzureOpenAIResponsesClient(credential=AzureCliCredential()).create_agent(
        name="Judge",
        instructions=(
            "You are a strict grader. Given INPUT and OUTPUT, return only a floating score 0..1 where 1 is perfect."
            "No extra words."
        ),
    )
    agent = AzureOpenAIResponsesClient(credential=AzureCliCredential()).create_agent(
        name="EvalAgent",
        instructions="Answer concisely in Japanese.",
    )
    tests = load_golden(case)
    passed = 0
    for t in tests:
        out = await agent.run(t["input"])
        prompt = f"INPUT: {t['input']}\nOUTPUT: {out.text}\nSCORE:"
        s = await judge.run(prompt)
        try:
            score = float(s.text.strip().split()[0])
        except Exception:
            score = 0.0
        ok = score >= threshold
        print({"id": t["id"], "score": score, "pass": ok})
        if ok:
            passed += 1
    print(f"summary: {passed}/{len(tests)} passed (threshold={threshold})")


def parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Golden + LLM-as-judge")
    sub = p.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--case", default="basics")
    j = sub.add_parser("judge")
    j.add_argument("--case", default="basics")
    j.add_argument("--threshold", type=float, default=0.8)
    return p.parse_args(argv)


async def main(argv: list[str]) -> None:
    setup_logging("INFO")
    args = parse_args(argv)
    if args.cmd == "run":
        await run_case(args.case)
    else:
        await judge_case(args.case, args.threshold)


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1:]))

