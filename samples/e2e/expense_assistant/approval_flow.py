import asyncio
import argparse
import random
import re
from dataclasses import dataclass
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
    RequestInfoExecutor,
    RequestInfoMessage,
    RequestResponse,
)
from agent_framework._workflows import WorkflowContext, FileCheckpointStorage
from agent_framework._workflows._events import RequestInfoEvent, WorkflowStatusEvent
from agent_framework._workflows._executor import Executor, handler
from agent_framework.azure import AzureOpenAIResponsesClient
from azure.identity import AzureCliCredential


# Reuse simple parsing/decision model
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
        for it in parsed.items:
            if it.category == "meal" and it.amount_yen > 1500:
                violations.append(f"MEAL_LIMIT:{it.amount_yen}")
        if total > 20000:
            violations.append(f"TOTAL_LIMIT:{total}")
        ok = len(violations) == 0
        await ctx.send_message(PolicyDecision(ok=ok, total_yen=total, violations=violations, items=parsed.items))


class Submit(Executor):
    def __init__(self) -> None:
        super().__init__(id="submit")

    @handler
    async def create(self, decision: PolicyDecision, ctx: WorkflowContext[str]) -> None:
        report_id = f"R{random.randint(10000,99999)}"
        lines = [f"- {it.category}: {it.amount_yen}円 ({it.day or ''})" for it in decision.items]
        await ctx.yield_output(f"submitted: id={report_id} total={decision.total_yen}円\n明細:\n" + "\n".join(lines))


class Explain(Executor):
    def __init__(self) -> None:
        super().__init__(id="explain")
        self._agent = AzureOpenAIResponsesClient(credential=AzureCliCredential()).create_agent(
            name="PolicyExplainer",
            instructions="ユーザーに丁寧に、簡潔に日本語でポリシー違反の理由を説明してください。",
        )

    @handler
    async def explain(self, decision: PolicyDecision, ctx: WorkflowContext[str]) -> None:
        reasons = ", ".join(decision.violations) or "不明"
        # RAG: ポリシーから根拠を抽出
        excerpts = retrieve_policy_evidence(f"{reasons} 合計 {decision.total_yen}円")
        prompt = (
            "以下の社内ポリシー抜粋を根拠として、なぜ申請が承認されないのかを日本語で簡潔に説明し、"
            "どのように修正すべきかを提案してください。\n"
            f"[VIOLATIONS] {reasons}\n[AMOUNT] {decision.total_yen}\n"
            f"[POLICY]\n{excerpts}\n---\n説明:"
        )
        res = await self._agent.run(prompt)
        await ctx.yield_output(f"policy_violation: {reasons}\n根拠:\n{excerpts}\n---\n{res.text}")


# Approval
@dataclass
class ApprovalRequest(RequestInfoMessage):
    total_yen: int = 0
    summary: str = ""
    stage: str = "manager"


class ApprovalGate(Executor):
    def __init__(self, result_target_id: str) -> None:
        super().__init__(id="approval_gate")
        self._result_id = result_target_id

    @handler
    async def request(self, dec: PolicyDecision, ctx: WorkflowContext[RequestInfoMessage]) -> None:
        if not dec.ok:
            await ctx.send_message(dec, target_id="explain")
            return
        lines = [f"- {it.category}: {it.amount_yen}円 ({it.day or ''})" for it in dec.items]
        stage = "manager" if dec.total_yen <= 15000 else "finance"
        req = ApprovalRequest(total_yen=dec.total_yen, summary="\n".join(lines), source_executor_id=self._result_id)
        req.stage = stage
        await ctx.send_message(req, target_id="approvals")


class AfterApproval(Executor):
    def __init__(self, submit_target_id: str, explain_target_id: str) -> None:
        super().__init__(id="after_approval")
        self._submit_id = submit_target_id
        self._explain_id = explain_target_id

    @handler
    async def handle(self, resp: RequestResponse[ApprovalRequest, dict], ctx: WorkflowContext[PolicyDecision]) -> None:  # type: ignore[name-defined]
        approved = bool((resp.data or {}).get("approved", False))
        stage = getattr(resp.original_request, "stage", "manager")
        if approved and stage == "manager" and resp.original_request.total_yen > 15000:
            # 2段階目（経理）へ再申請
            req2 = ApprovalRequest(
                total_yen=resp.original_request.total_yen,
                summary=resp.original_request.summary,
                source_executor_id=self.id,
            )
            req2.stage = "finance"
            await ctx.send_message(req2, target_id="approvals")
            return
        if approved:
            await ctx.send_message(PolicyDecision(ok=True, total_yen=resp.original_request.total_yen, violations=[], items=[]), target_id=self._submit_id)
        else:
            await ctx.send_message(PolicyDecision(ok=False, total_yen=resp.original_request.total_yen, violations=["REJECTED_BY_APPROVER"], items=[]), target_id=self._explain_id)


# ----- Simple policy retrieval (RAG-lite) -----
def retrieve_policy_evidence(query: str, k: int = 3) -> str:
    """Very small keyword-overlap retriever for policy.md.

    Splits by headings and returns top-k sections by token overlap.
    """
    policy_path = _here.parent / "policy.md"
    try:
        text = policy_path.read_text(encoding="utf-8")
    except Exception:
        return "(policy not available)"
    sections: list[tuple[str, str]] = []  # (title, body)
    current_title = ""
    current_lines: list[str] = []
    for line in text.splitlines():
        if line.startswith("## "):
            if current_title or current_lines:
                sections.append((current_title, "\n".join(current_lines).strip()))
                current_lines = []
            current_title = line[3:].strip()
        else:
            current_lines.append(line)
    if current_title or current_lines:
        sections.append((current_title, "\n".join(current_lines).strip()))

    q_tokens = set(re.findall(r"\w+", query.lower()))
    scored = []
    for title, body in sections:
        t = (title + "\n" + body).lower()
        s_tokens = set(re.findall(r"\w+", t))
        score = len(q_tokens & s_tokens)
        if score > 0:
            scored.append((score, title, body))
    scored.sort(reverse=True)
    out = []
    for _, title, body in scored[:k]:
        out.append(f"### {title}\n{body}")
    return "\n\n".join(out) or "(no relevant policy found)"


def build_workflow() -> tuple[Any, FileCheckpointStorage]:
    parser = Parser()
    policy = PolicyCheck()
    submit = Submit()
    explain = Explain()
    approvals = RequestInfoExecutor(id="approvals")
    after = AfterApproval(submit_target_id=submit.id, explain_target_id=explain.id)
    gate = ApprovalGate(result_target_id=after.id)

    wb = WorkflowBuilder(name="expense_assistant_approval")
    wb.set_start_executor(parser)
    wb.add_edge(parser, policy)

    need_approval = lambda d: isinstance(d, PolicyDecision) and d.ok and d.total_yen > 10000
    is_ng = lambda d: isinstance(d, PolicyDecision) and not d.ok

    wb.add_switch_case_edge_group(
        policy,
        [
            Case(condition=is_ng, target=explain),
            Case(condition=need_approval, target=gate),
            Default(target=submit),
        ],
    )
    wb.add_edge(gate, approvals)
    wb.add_edge(approvals, after)
    wb.add_edge(after, submit)
    wb.add_edge(after, explain)

    storage = FileCheckpointStorage(_here.parent / ".checkpoints")
    wf = wb.with_checkpointing(storage).build()
    return wf, storage


def parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Expense assistant with approval flow")
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("start")
    s.add_argument("--text", default="タクシー 12000円, 昼食 1200円")
    a = sub.add_parser("approve")
    a.add_argument("--checkpoint", required=True)
    a.add_argument("--request", required=True)
    a.add_argument("--approved", type=int, default=1)
    a.add_argument("--comment", default="")
    return p.parse_args(argv)


async def main(argv: list[str]) -> None:
    setup_logging("INFO")
    args = parse_args(argv)
    wf, storage = build_workflow()

    if args.cmd == "start":
        events = await wf.run(args.text)
        req_id = None
        for ev in events:
            if isinstance(ev, RequestInfoEvent):
                req_id = ev.request_id
                print(f"[request] id={req_id} total_yen={getattr(ev.data, 'total_yen', '')}")
            if isinstance(ev, WorkflowStatusEvent):
                print(f"[status] {ev.state.name}")
            if isinstance(ev, WorkflowOutputEvent):
                print("--- RESULT ---")
                print(ev.data)
        if req_id:
            cps = await storage.list_checkpoints(workflow_id=wf.id)
            cps.sort(key=lambda c: c.timestamp)
            cp_id = cps[-1].checkpoint_id if cps else ""
            print(f"[checkpoint] id={cp_id}")
            print(f"承認コマンド例: python approval_flow.py approve --checkpoint {cp_id} --request {req_id} --approved 1 --comment ok")
        return

    if args.cmd == "approve":
        responses = {args.request: {"approved": bool(args.approved), "comment": args.comment}}
        events = await wf.run_from_checkpoint(args.checkpoint, checkpoint_storage=storage, responses=responses)
        for ev in events:
            if isinstance(ev, WorkflowOutputEvent):
                print("--- RESULT ---")
                print(ev.data)
            if isinstance(ev, WorkflowStatusEvent):
                print(f"[status] {ev.state.name}")


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1:]))
