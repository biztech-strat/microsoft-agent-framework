import asyncio
import argparse
import dataclasses
import random
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path
import sys
from typing import Any, List

# Ensure repo root on sys.path
_here = Path(__file__).resolve()
for _p in (_here.parent, *_here.parents):
    if (_p / "samples").is_dir() and (_p / "python").is_dir():
        if str(_p) not in sys.path:
            sys.path.insert(0, str(_p))
        break

from samples._shared import ensure_repo_on_sys_path, setup_logging

ensure_repo_on_sys_path()

from agent_framework import (
    WorkflowBuilder,
    WorkflowOutputEvent,
    AgentRunEvent,
    Case,
    Default,
)
from agent_framework._workflows import WorkflowContext
from agent_framework._workflows._executor import Executor, handler
from agent_framework.azure import AzureOpenAIResponsesClient
from azure.identity import AzureCliCredential


@dataclass
class ReceiptItem:
    category: str
    amount_yen: int
    day: str | None = None
    note: str | None = None


@dataclass
class ParsedReceipts:
    items: List[ReceiptItem]


@dataclass
class PolicyDecision:
    ok: bool
    total_yen: int
    violations: List[str]
    items: List[ReceiptItem]


class Parser(Executor):
    def __init__(self) -> None:
        super().__init__(id="parser")

    @handler
    async def parse(self, text: str, ctx: WorkflowContext[ParsedReceipts]) -> None:
        items: List[ReceiptItem] = []
        # very simple heuristics: カテゴリー語 + (YYYY-MM-DD)? + 金額(数字+円)
        for chunk in re.split(r"[,、]\s*", text):
            cat = "その他"
            if "タクシー" in chunk:
                cat = "taxi"
            elif "昼食" in chunk or "ランチ" in chunk:
                cat = "meal"
            m_amount = re.search(r"(\d{1,3}(?:,\d{3})*|\d+)\s*円", chunk)
            m_day = re.search(r"(20\d{2}-\d{2}-\d{2})", chunk)
            if m_amount:
                amt = int(m_amount.group(1).replace(",", ""))
                items.append(ReceiptItem(category=cat, amount_yen=amt, day=(m_day.group(1) if m_day else None), note=chunk))
        await ctx.send_message(ParsedReceipts(items))


class PolicyCheck(Executor):
    def __init__(self) -> None:
        super().__init__(id="policy")

    @handler
    async def check(self, parsed: ParsedReceipts, ctx: WorkflowContext[PolicyDecision]) -> None:
        violations: List[str] = []
        total = sum(i.amount_yen for i in parsed.items)
        # Rules: meal <= 1500 each, total <= 20000
        for it in parsed.items:
            if it.category == "meal" and it.amount_yen > 1500:
                violations.append(f"MEAL_LIMIT:{it.amount_yen}")
        if total > 20000:
            violations.append(f"TOTAL_LIMIT:{total}")
        ok = len(violations) == 0
        await ctx.send_message(PolicyDecision(ok=ok, total_yen=total, violations=violations, items=parsed.items))


class Submit(Executor):
    def __init__(self, graph_real: bool = False) -> None:
        super().__init__(id="submit")
        self.graph_real = graph_real

    async def _get_user_display_name(self) -> str:
        if not self.graph_real:
            return "Contoso User"
        # Real call (optional)
        import os
        import httpx  # type: ignore
        from azure.identity.aio import AzureCliCredential  # type: ignore

        scope = os.environ.get("GRAPH_SCOPE", "https://graph.microsoft.com/.default")
        base = os.environ.get("GRAPH_BASE", "https://graph.microsoft.com/v1.0")
        cred = AzureCliCredential()
        token = await cred.get_token(scope)
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(f"{base}/me", headers={"Authorization": f"Bearer {token.token}"})
            r.raise_for_status()
            data = r.json()
            return data.get("displayName") or data.get("userPrincipalName") or "User"

    @handler
    async def create(self, decision: PolicyDecision, ctx: WorkflowContext[str]) -> None:
        user = await self._get_user_display_name()
        report_id = f"R{random.randint(10000,99999)}"
        lines = [f"- {it.category}: {it.amount_yen}円 ({it.day or ''})" for it in decision.items]
        summary = "\n".join(lines)
        await ctx.yield_output(
            f"submitted: id={report_id} user={user} total={decision.total_yen}円\n明細:\n{summary}"
        )


class Explain(Executor):
    def __init__(self) -> None:
        super().__init__(id="explain")
        # Use an agent to phrase explanation
        self._agent = AzureOpenAIResponsesClient(credential=AzureCliCredential()).create_agent(
            name="PolicyExplainer",
            instructions="ユーザーに丁寧に、簡潔に日本語でポリシー違反の理由を説明してください。",
        )

    @handler
    async def explain(self, decision: PolicyDecision, ctx: WorkflowContext[str]) -> None:
        reasons = ", ".join(decision.violations) or "不明"
        prompt = f"違反: {reasons}. 合計 {decision.total_yen} 円。どのように修正すればよいか提案してください。"
        res = await self._agent.run(prompt)
        await ctx.yield_output(f"policy_violation: {reasons}\n{res.text}")


def parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Expense assistant E2E demo")
    p.add_argument("--text", default="タクシー 2025-09-15 3200円, 昼食 1200円")
    p.add_argument("--graph-real", type=int, default=0)
    return p.parse_args(argv)


async def main(argv: list[str]) -> None:
    setup_logging("INFO")
    args = parse_args(argv)

    parser = Parser()
    policy = PolicyCheck()
    submit = Submit(graph_real=bool(args.graph_real))
    explain = Explain()

    wb = WorkflowBuilder(name="expense_assistant")
    wb.set_start_executor(parser)
    wb.add_edge(parser, policy)
    # Branch by policy.ok
    def is_ok(dec: PolicyDecision) -> bool:
        return isinstance(dec, PolicyDecision) and dec.ok

    wb.add_switch_case_edge_group(
        policy,
        [
            Case(condition=is_ok, target=submit),
            Default(target=explain),
        ],
    )

    wf = wb.build()

    events = await wf.run(args.text)
    for ev in events:
        if isinstance(ev, AgentRunEvent):
            # Show agent text outputs (Explain path)
            text = getattr(ev.data, "text", None)
            if text:
                print(f"[{ev.executor_id}] {text}")
        if isinstance(ev, WorkflowOutputEvent):
            print("--- RESULT ---")
            print(ev.data)


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1:]))

