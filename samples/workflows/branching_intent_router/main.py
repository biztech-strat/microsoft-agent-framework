import asyncio
import logging
import os
import re
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

from agent_framework import Case, Default, WorkflowBuilder, AgentRunEvent
from agent_framework.azure import AzureOpenAIResponsesClient
from azure.identity import AzureCliCredential

from samples._shared import load_env, setup_logging


def is_translate_intent(text: str) -> bool:
    pattern = re.compile(r"(翻訳|英訳|translate)", re.IGNORECASE)
    return bool(pattern.search(text))


async def main() -> None:
    setup_logging("INFO")
    load_env((".env",))
    logger = logging.getLogger("router")

    # Router: identity pass-through (str -> str)
    from agent_framework import executor, WorkflowContext

    @executor(id="Router")
    async def router(text: str, ctx: WorkflowContext[str]) -> None:
        route = "translator" if is_translate_intent(text) else "summarizer"
        logger.info("Routed to %s based on input: %s", route, text)
        await ctx.send_message(text)

    translator = AzureOpenAIResponsesClient(credential=AzureCliCredential()).create_agent(
        name="Translator",
        instructions=(
            "If the input is Japanese, translate to English."
            "If the input is English, translate to Japanese."
        ),
    )

    summarizer = AzureOpenAIResponsesClient(credential=AzureCliCredential()).create_agent(
        name="Summarizer",
        instructions=("Summarize the input in Japanese in one concise sentence."),
    )

    wb = WorkflowBuilder()
    wb.set_start_executor(router)
    wb.add_switch_case_edge_group(
        router,
        [
            Case(condition=is_translate_intent, target=translator),
            Default(target=summarizer),
        ],
    )
    wf = wb.build()

    prompt = os.environ.get("PROMPT", "次の文を英訳して: Microsoft Agent Framework は何ができる？")
    events = await wf.run(prompt)
    for ev in events:
        if isinstance(ev, AgentRunEvent):
            text = ev.data.text if hasattr(ev.data, "text") else None
            if text:
                print(f"[{ev.executor_id}] {text}")


if __name__ == "__main__":
    asyncio.run(main())
