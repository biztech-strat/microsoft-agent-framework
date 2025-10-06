import asyncio
import argparse
import os
from pathlib import Path
import sys
from typing import Annotated

# Ensure repo root is on sys.path so `samples` is importable
_here = Path(__file__).resolve()
for _p in (_here.parent, *_here.parents):
    if (_p / "samples").is_dir() and (_p / "python").is_dir():
        if str(_p) not in sys.path:
            sys.path.insert(0, str(_p))
        break

from samples._shared import ensure_repo_on_sys_path, setup_logging

ensure_repo_on_sys_path()

from pydantic import Field
from agent_framework.azure import AzureOpenAIResponsesClient
from azure.identity import AzureCliCredential


async def invoke_function_real(name: str) -> str:
    import httpx  # type: ignore

    url = os.environ.get("AZ_FUNCTION_URL")
    if not url:
        raise RuntimeError("AZ_FUNCTION_URL is not set")
    code = os.environ.get("AZ_FUNCTION_CODE")

    params = {"name": name}
    if code:
        params["code"] = code

    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.get(url, params=params, headers={"x-functions-key": code} if code else None)
        r.raise_for_status()
        try:
            data = r.json()
        except Exception:
            data = {"text": r.text}
        return data.get("text") or data.get("message") or str(data)


async def invoke_function_mock(name: str) -> str:
    await asyncio.sleep(0.05)
    return f"Hello, {name}! (mock)"


def create_tool(use_real: bool):
    async def call_function(
        name: Annotated[str, Field(description="Name to greet via Azure Function")]
    ) -> str:
        try:
            return await (invoke_function_real(name) if use_real else invoke_function_mock(name))
        except Exception as e:
            return f"Function call failed: {e}"

    return call_function


def parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Azure Functions HTTP tool demo")
    p.add_argument("--name", default="Taro")
    p.add_argument("--real", type=int, default=0, help="1 for real HTTP call, 0 for mock")
    return p.parse_args(argv)


async def main(argv: list[str]) -> None:
    setup_logging("INFO")
    args = parse_args(argv)
    tool = create_tool(use_real=bool(args.real))

    agent = AzureOpenAIResponsesClient(credential=AzureCliCredential()).create_agent(
        name="FuncAgent",
        instructions=("You can call a tool to invoke an Azure Function and present the greeting."),
        tools=tool,
    )

    prompt = f"関数を呼び出して {args.name} に挨拶してください。"
    print("User:", prompt)
    print("Agent: ", end="")
    async for upd in agent.run_stream(prompt):
        if upd.text:
            print(upd.text, end="", flush=True)
    print()


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1:]))

