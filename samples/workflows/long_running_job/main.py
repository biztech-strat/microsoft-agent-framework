import asyncio
import argparse
import json
from dataclasses import dataclass
from pathlib import Path
import sys
from typing import Any

# Ensure repo root is on sys.path so `samples` is importable
_here = Path(__file__).resolve()
for _p in (_here.parent, *_here.parents):
    if (_p / "samples").is_dir() and (_p / "python").is_dir():
        if str(_p) not in sys.path:
            sys.path.insert(0, str(_p))
        break

from samples._shared import ensure_repo_on_sys_path, setup_logging

# Ensure in-repo core packages take precedence over site-packages
ensure_repo_on_sys_path()

from agent_framework import (
    WorkflowBuilder,
    RequestInfoExecutor,
    RequestInfoMessage,
    RequestResponse,
    WorkflowEvent,
    WorkflowOutputEvent,
    AgentRunEvent,
    WorkflowStatusEvent,
    RequestInfoEvent,
)
from agent_framework._workflows import WorkflowRunState
from agent_framework._workflows._executor import handler, Executor
from agent_framework._workflows import FileCheckpointStorage, WorkflowContext


CHECKPOINT_DIR = _here.parent / ".checkpoints"


@dataclass
class LongJobRequest(RequestInfoMessage):
    """外部に委譲する長時間ジョブの依頼。"""

    details: str = ""


class StartJob(Executor):
    def __init__(self, result_target_id: str) -> None:
        super().__init__(id="starter")
        self._result_target_id = result_target_id

    @handler
    async def submit(self, text: str, ctx: WorkflowContext) -> None:  # type: ignore[name-defined]
        # 外部処理への依頼を作成。結果の送り先（result handler）を明示
        req = LongJobRequest(details=text, source_executor_id=self._result_target_id)
        # RequestInfoExecutor に依頼を送る
        await ctx.send_message(req, target_id="requests")


class ResultHandler(Executor):
    def __init__(self) -> None:
        super().__init__(id="result")

    @handler
    async def on_result(self, msg: RequestResponse[LongJobRequest, Any], ctx: WorkflowContext[str]) -> None:  # type: ignore[name-defined]
        # 受け取った結果を最終出力としてワークフロー出力に流す
        req = msg.original_request
        await ctx.yield_output(f"request_id={msg.request_id} details='{req.details}' result={json.dumps(msg.data)}")


def build_workflow():
    requests = RequestInfoExecutor(id="requests")
    result = ResultHandler()
    starter = StartJob(result_target_id=result.id)

    storage = FileCheckpointStorage(CHECKPOINT_DIR)

    wb = WorkflowBuilder(name="long_job_demo")
    wb.set_start_executor(starter)
    wb.add_edge(starter, requests)  # start -> RequestInfoExecutor
    wb.add_edge(requests, result)   # RequestInfoExecutor -> ResultHandler（応答メッセージ用）
    wf = wb.with_checkpointing(storage).build()
    return wf, storage


async def cmd_start(args: argparse.Namespace) -> None:
    wf, storage = build_workflow()
    text = args.text or "バッチ処理を実行"
    events = await wf.run(text)

    req_id: str | None = None
    # ステータスとリクエストイベントを表示
    for ev in events:
        if isinstance(ev, WorkflowStatusEvent):
            print(f"[status] {ev.state.name}")
        if isinstance(ev, RequestInfoEvent):
            req_id = ev.request_id
            print(f"[request] id={ev.request_id} type={ev.request_type.__name__}")

    # 直近のチェックポイントIDを取得
    cps = await storage.list_checkpoints(workflow_id=wf.id)
    cps.sort(key=lambda c: c.timestamp)
    cp_id = cps[-1].checkpoint_id if cps else ""
    print(f"[checkpoint] id={cp_id}")

    if req_id is None:
        print("No request was created (unexpected).")
        return
    print("-- 次のコマンドで再開できます --")
    print(f"python main.py resume --checkpoint {cp_id} --request {req_id} --result '" + '{"status":"ok"}' + "'")


async def cmd_resume(args: argparse.Namespace) -> None:
    wf, storage = build_workflow()
    responses = {args.request: args.result}
    events = await wf.run_from_checkpoint(args.checkpoint, checkpoint_storage=storage, responses=responses)
    for ev in events:
        if isinstance(ev, WorkflowOutputEvent):
            print(f"[output] {ev.data}")
        if isinstance(ev, AgentRunEvent):
            # not used in this sample; present for completeness
            pass
        if isinstance(ev, WorkflowStatusEvent):
            print(f"[status] {ev.state.name}")


async def cmd_demo_poll(args: argparse.Namespace) -> None:
    # 1) start
    wf, storage = build_workflow()
    events = await wf.run(args.text or "ログ集計")

    req_id: str | None = None
    for ev in events:
        if isinstance(ev, RequestInfoEvent):
            req_id = ev.request_id
    cps = await storage.list_checkpoints(workflow_id=wf.id)
    cps.sort(key=lambda c: c.timestamp)
    cp_id = cps[-1].checkpoint_id if cps else ""

    print(f"[poll] waiting external completion for request={req_id} ...")
    await asyncio.sleep(args.delay)
    fake_result = {"status": "done", "took_sec": args.delay}

    # 2) resume
    events2 = await wf.run_from_checkpoint(cp_id, checkpoint_storage=storage, responses={req_id: fake_result})  # type: ignore[arg-type]
    for ev in events2:
        if isinstance(ev, WorkflowOutputEvent):
            print(f"[output] {ev.data}")
        if isinstance(ev, WorkflowStatusEvent):
            print(f"[status] {ev.state.name}")


def parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Long-running job workflow demo")
    sub = p.add_subparsers(dest="cmd", required=True)

    s1 = sub.add_parser("start", help="Start a long-running job and persist checkpoint")
    s1.add_argument("--text", default=None)
    s1.set_defaults(func=cmd_start)

    s2 = sub.add_parser("resume", help="Resume from checkpoint with response (callback)")
    s2.add_argument("--checkpoint", required=True)
    s2.add_argument("--request", required=True)
    s2.add_argument("--result", required=True)
    s2.set_defaults(func=cmd_resume)

    s3 = sub.add_parser("demo_poll", help="Simulate polling then resume automatically")
    s3.add_argument("--text", default=None)
    s3.add_argument("--delay", type=int, default=3)
    s3.set_defaults(func=cmd_demo_poll)

    return p.parse_args(argv)


async def main(argv: list[str]) -> None:
    setup_logging("INFO")
    args = parse_args(argv)
    await args.func(args)


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1:]))
