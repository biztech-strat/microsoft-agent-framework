import asyncio
import re
from typing import List
from pathlib import Path
import sys

# Ensure repo root is on sys.path so `samples` is importable
_here = Path(__file__).resolve()
for _p in (_here.parent, *_here.parents):
    if (_p / "samples").is_dir() and (_p / "python").is_dir():
        if str(_p) not in sys.path:
            sys.path.insert(0, str(_p))
        break

from samples._shared import ensure_repo_on_sys_path

# Ensure in-repo core packages take precedence over site-packages
ensure_repo_on_sys_path()

from agent_framework import (
    AgentRunEvent,
    ChatMessage,
    Role,
    SequentialBuilder,
)
from agent_framework.azure import AzureOpenAIResponsesClient
from azure.identity import AzureCliCredential

from samples._shared import load_env, setup_logging


def extract_steps_from_text(text: str) -> List[str]:
    lines = [l.strip("- ") for l in text.splitlines() if l.strip()]
    # Heuristics: pick lines that look like steps
    steps = []
    for line in lines:
        if re.match(r"^(Step|ステップ|[0-9]+\.|・|- )", line, re.IGNORECASE):
            steps.append(re.sub(r"^(Step\s*\d+[:\.]?|[0-9]+\.|・|- )\s*", "", line, flags=re.IGNORECASE))
    if not steps:
        # Fallback: first 3 lines
        steps = lines[:3]
    return steps[:3]


async def main() -> None:
    setup_logging("INFO")
    load_env((".env",))

    # Agents
    planner = AzureOpenAIResponsesClient(credential=AzureCliCredential()).create_agent(
        name="Planner",
        instructions=(
            "Break the user's goal into exactly 3 concise steps."
            "Reply as bullet list starting with '- '."
        ),
    )

    actor = AzureOpenAIResponsesClient(credential=AzureCliCredential()).create_agent(
        name="Actor",
        instructions=(
            "You receive research notes and must produce the final answer in Japanese."
            "Be concise."
        ),
    )

    # Function executor operating on conversation
    from agent_framework import executor, WorkflowContext

    @executor(id="Retriever")
    async def retrieve(conv: List[ChatMessage], ctx: WorkflowContext[str]) -> None:
        # Last assistant message is planner output
        last = next((m for m in reversed(conv) if m.role == Role.ASSISTANT and m.text), None)
        plan_text = last.text if last else ""
        steps = extract_steps_from_text(plan_text)
        notes = "\n".join(f"[R{i+1}] 情報要約: {s}" for i, s in enumerate(steps))
        await ctx.send_message(f"研究ノート:\n{notes}")

    # Build sequential workflow
    workflow = SequentialBuilder().participants([planner, retrieve, actor]).build()

    user_goal = "Microsoft Agent Framework の概要を社内向けに3点で説明して"
    events = await workflow.run(user_goal)

    # Print agent outputs in order
    for ev in events:
        if isinstance(ev, AgentRunEvent):
            text = ev.data.text if hasattr(ev.data, "text") else None
            if text:
                print(f"[{ev.executor_id}] {text}")


if __name__ == "__main__":
    asyncio.run(main())
