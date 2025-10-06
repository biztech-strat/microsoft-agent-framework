import asyncio
import argparse
from dataclasses import dataclass
from pathlib import Path
import sys
from typing import Any, Dict

# Ensure repo root is on sys.path so `samples` is importable
_here = Path(__file__).resolve()
for _p in (_here.parent, *_here.parents):
    if (_p / "samples").is_dir() and (_p / "python").is_dir():
        if str(_p) not in sys.path:
            sys.path.insert(0, str(_p))
        break

from samples._shared import ensure_repo_on_sys_path, setup_logging

ensure_repo_on_sys_path()

from typing import Annotated
from pydantic import Field
from agent_framework.azure import AzureOpenAIResponsesClient
from azure.identity import AzureCliCredential


class RateLimitError(Exception):
    def __init__(self, retry_after: float) -> None:
        self.retry_after = retry_after
        super().__init__(f"Rate limited. Retry after {retry_after}s")


@dataclass
class RestClient:
    mode: str = "success"  # success | fail | rate_limit
    real_url: str | None = None

    async def get_weather(self, city: str) -> Dict[str, Any]:
        if self.real_url:
            try:
                import httpx  # type: ignore
            except Exception as e:  # pragma: no cover
                raise RuntimeError("httpx not available; install to use --real mode") from e
            async with httpx.AsyncClient(timeout=5.0) as client:
                r = await client.get(self.real_url, params={"city": city})
                r.raise_for_status()
                return r.json()

        # Mocked branches
        if self.mode == "success":
            return {"city": city, "temp_c": 24, "condition": "sunny"}
        if self.mode == "rate_limit":
            raise RateLimitError(retry_after=2.0)
        # default to failure
        raise RuntimeError("Upstream error: service unavailable")


def create_tool(client: RestClient):
    async def fetch_weather(
        city: Annotated[str, Field(description="The city to query weather for.")]
    ) -> str:
        try:
            data = await client.get_weather(city)
            return f"{data['city']}: {data['condition']}, {data['temp_c']}°C"
        except RateLimitError as e:
            return f"Rate limited. Please retry after {e.retry_after} seconds."
        except Exception as e:
            return f"Failed to get weather: {e}"

    return fetch_weather


def parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="REST basic integration demo")
    p.add_argument("--city", default="東京")
    p.add_argument("--mode", choices=["success", "fail", "rate_limit"], default="success")
    p.add_argument("--real", action="store_true", help="Use real HTTP call")
    p.add_argument("--url", default=None, help="Real URL returning {temp_c, condition} JSON")
    return p.parse_args(argv)


async def main(argv: list[str]) -> None:
    setup_logging("INFO")
    args = parse_args(argv)

    client = RestClient(mode=args.mode, real_url=args.url if args.real else None)
    tool = create_tool(client)

    agent = AzureOpenAIResponsesClient(credential=AzureCliCredential()).create_agent(
        name="RestAgent",
        instructions=(
            "You can call tools to fetch external data. If the tool indicates a rate limit, explain briefly."
        ),
        tools=tool,
    )

    prompt = f"{args.city} の天気を教えてください。"
    print(f"User: {prompt}")
    print("Agent: ", end="", flush=True)
    async for upd in agent.run_stream(prompt):
        if upd.text:
            print(upd.text, end="", flush=True)
    print()


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1:]))

