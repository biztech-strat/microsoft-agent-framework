from __future__ import annotations

import os
from pathlib import Path
import sys

# Ensure repo root is on sys.path so `samples` is importable when DevUI imports this package
_here = Path(__file__).resolve()
for _p in (_here.parent, *_here.parents):
    if (_p / "samples").is_dir() and (_p / "python").is_dir():
        if str(_p) not in sys.path:
            sys.path.insert(0, str(_p))
        break

from samples._shared import ensure_repo_on_sys_path, load_env

# Ensure in-repo core packages take precedence over site-packages
ensure_repo_on_sys_path()

from agent_framework.azure import AzureOpenAIResponsesClient
from azure.identity import AzureCliCredential


def get_weather(location: str) -> str:
    """Get weather for a location.

    A deterministic demo tool that returns a stubbed condition string.
    """
    location = location.strip() or "Unknown"
    return f"Weather in {location}: 72°F and sunny"


def create_agent():
    """Create the WeatherAgent used by DevUI.

    Notes:
    - Discovery mode: DevUI imports `agent` from this package.
    - Programmatic mode: `samples/devui/main.py` calls this function.
    - Auth: Azure CLI (`az login`) or `AZURE_OPENAI_API_KEY` in .env
    - Model config is read from .env (endpoint, deployment name)
    """
    # Allow running standalone imports to pick up .env if present
    load_env(
        (
            str(_here.parent.parent / ".env"),  # samples/devui/agents/.env (parent of weather_agent)
            str(_here.parent / ".env"),         # samples/devui/agents/weather_agent/.env
            str(_here.parents[3] / "samples" / ".env"),  # repo/samples/.env
        )
    )

    # Prefer CLI credential; fall back to API key if provided
    # AzureOpenAIResponsesClient will use env vars for endpoint/deployment
    client = AzureOpenAIResponsesClient(
        credential=AzureCliCredential() if not os.environ.get("AZURE_OPENAI_API_KEY") else None,
        api_key=os.environ.get("AZURE_OPENAI_API_KEY"),
    )

    agent = client.create_agent(
        name="WeatherAgent",
        instructions=(
            "You are a concise weather assistant."
            " Reply in Japanese if the user writes in Japanese."
            " Use the get_weather tool when users ask for weather."
        ),
        tools=[get_weather],
    )
    return agent

