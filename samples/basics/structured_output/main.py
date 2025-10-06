import asyncio
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

from agent_framework.azure import AzureOpenAIResponsesClient
from azure.identity import AzureCliCredential
from pydantic import BaseModel, Field

from samples._shared import load_env, setup_logging


class Summary(BaseModel):
    topic: str = Field(description="対象テーマ")
    bullets: List[str] = Field(description="3点の要約", min_items=3, max_items=3)


async def ask_with_retry(prompt: str, max_retries: int = 2) -> Summary:
    agent = AzureOpenAIResponsesClient(credential=AzureCliCredential()).create_agent(
        name="StructAgent",
        instructions=(
            "Respond strictly in JSON that matches the provided schema."
        ),
    )

    last_error: Exception | None = None
    for attempt in range(1, max_retries + 2):
        try:
            res = await agent.run(prompt, response_format=Summary)
            assert isinstance(res.value, Summary)
            return res.value
        except Exception as e:  # ValidationError などを包含
            last_error = e
            prompt = (
                prompt
                + "\n出力は必ずJSONのみ。不要な文章やマークダウンは禁止。スキーマに厳密準拠。"
            )
    raise RuntimeError(f"Failed to get structured output: {last_error}")


async def main() -> None:
    setup_logging("INFO")
    load_env((".env",))

    prompt = "Microsoft Agent Framework の強みを3点で要約してください。"
    result = await ask_with_retry(prompt)
    print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    asyncio.run(main())
