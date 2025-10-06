import asyncio
import os
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

from agent_framework import AgentRunEvent, ConcurrentBuilder
from agent_framework.azure import AzureOpenAIResponsesClient
from azure.identity import AzureCliCredential

from samples._shared import load_env, setup_logging


async def main() -> None:
    setup_logging("INFO")
    load_env((".env",))

    credential = AzureCliCredential()

    paraphraser = AzureOpenAIResponsesClient(credential=credential).create_agent(
        name="Paraphraser",
        instructions="Rephrase the input in different words (Japanese).",
    )
    summarizer = AzureOpenAIResponsesClient(credential=credential).create_agent(
        name="Summarizer",
        instructions="Summarize the input in 1 sentence (Japanese).",
    )
    qagenerator = AzureOpenAIResponsesClient(credential=credential).create_agent(
        name="QAGenerator",
        instructions="Generate 3 short Q&A-style hints about the input (Japanese).",
    )

    max_branches = int(os.environ.get("MAX_BRANCHES", "2"))
    agents: List = [paraphraser, summarizer, qagenerator][:max(1, min(3, max_branches))]

    # Aggregate final outputs as plain text
    async def aggregate(results):
        parts = []
        for r in results:
            text = getattr(r.agent_run_response, "text", None)
            if not text and getattr(r.agent_run_response, "messages", None):
                msgs = r.agent_run_response.messages
                text = msgs[-1].text if msgs and getattr(msgs[-1], "text", None) else None
            if text:
                parts.append(text)
        return "\n---\n".join(parts)

    wf = ConcurrentBuilder().participants(agents).with_aggregator(aggregate).build()

    prompt = os.environ.get("PROMPT", "Microsoft Agent Framework の要点を説明してください")
    events = await wf.run(prompt)
    for ev in events:
        if isinstance(ev, AgentRunEvent):
            text = ev.data.text if hasattr(ev.data, "text") else None
            if text:
                print(f"[{ev.executor_id}] {text}")


if __name__ == "__main__":
    asyncio.run(main())
