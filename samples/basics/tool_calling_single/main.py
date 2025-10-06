import asyncio
import logging
from random import randint
from typing import Annotated
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
from pydantic import Field

from samples._shared import load_env, setup_logging


def get_weather(
    location: Annotated[str, Field(description="The location to get the weather for.")],
) -> str:
    """Return a simple weather sentence for the location.

    入力: `location`（都市名など）
    出力: `str`（説明文）
    """
    logging.getLogger("sample.tools").info("Executing tool: get_weather(%s)", location)
    conditions = ["sunny", "cloudy", "rainy", "stormy"]
    return f"The weather in {location} is {conditions[randint(0, 3)]} with a high of {randint(10, 30)}°C."


async def main() -> None:
    setup_logging("INFO")
    load_env((".env",))

    agent = AzureOpenAIResponsesClient(credential=AzureCliCredential()).create_agent(
        name="ToolAgent",
        instructions=(
            "You are a helpful assistant. If the user asks about weather, use the get_weather tool."
        ),
        tools=get_weather,
    )

    user = "今日の東京の天気は？"
    print(f"User: {user}")
    print("Agent: ", end="", flush=True)
    async for chunk in agent.run_stream(user):
        if chunk.text:
            print(chunk.text, end="", flush=True)
    print()


if __name__ == "__main__":
    asyncio.run(main())
