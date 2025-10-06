import asyncio
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


async def main() -> None:
    setup_logging("INFO")
    load_env((".env",))

    agent = AzureOpenAIResponsesClient(credential=AzureCliCredential()).create_agent(
        name="MemoryAgent",
        instructions=(
            "You are a helpful assistant with short-term memory within the current session."
        ),
    )
    # Keep a single thread across turns to preserve in-memory history
    # If you want to reset memory, call `agent.get_new_thread()`
    # If you want to have multiple independent sessions, create multiple threads
    # If you don't care about memory, don't pass `thread` to `agent.run` or `agent.run_stream`
    thread = agent.get_new_thread()

    print("=== Turn 1 ===")
    msg1 = "私の好きな色は青です。覚えておいてください。"
    print(f"User: {msg1}")
    print("Agent: ", end="", flush=True)
    async for chunk in agent.run_stream(msg1, thread=thread):
        if chunk.text:
            print(chunk.text, end="", flush=True)
    print("\n")

    print("=== Turn 2 ===")
    msg2 = "私の好きな色は？"
    print(f"User: {msg2}")
    result = await agent.run(msg2, thread=thread)
    print(f"Agent: {result}")


if __name__ == "__main__":
    asyncio.run(main())
