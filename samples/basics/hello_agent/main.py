import asyncio
import os
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

from agent_framework.azure import AzureOpenAIResponsesClient
from azure.identity import AzureCliCredential

from samples._shared import load_env, setup_logging


async def run_non_streaming() -> None:
    print("=== Non-Streaming ===")
    agent = AzureOpenAIResponsesClient(credential=AzureCliCredential()).create_agent(
        name="HelloAgent",
        instructions=(
            "You are a concise and friendly assistant. Reply in Japanese if the user speaks Japanese."
        ),
    )
    user = os.environ.get("PROMPT", "Microsoft Agent Framework について一言で紹介してください。")
    print(f"User: {user}")
    result = await agent.run(user)
    print(f"Agent: {result}")


async def run_streaming() -> None:
    print("=== Streaming ===")
    agent = AzureOpenAIResponsesClient(credential=AzureCliCredential()).create_agent(
        name="HelloAgent",
        instructions=(
            "You are a concise and friendly assistant. Reply in Japanese if the user speaks Japanese."
        ),
    )
    user = os.environ.get("PROMPT", "このサンプルの概要を一文で説明してください。")
    print(f"User: {user}")
    print("Agent: ", end="", flush=True)
    async for chunk in agent.run_stream(user):
        if chunk.text:
            print(chunk.text, end="", flush=True)
    print()


async def main() -> None:
    setup_logging("INFO")
    load_env((".env",))

    if os.environ.get("STREAM"):
        await run_streaming()
    else:
        await run_non_streaming()
        print()
        await run_streaming()


if __name__ == "__main__":
    asyncio.run(main())
