import asyncio
import os
import time
from pathlib import Path
import sys

# Ensure repo root on sys.path
_here = Path(__file__).resolve()
for _p in (_here.parent, *_here.parents):
    if (_p / "samples").is_dir() and (_p / "python").is_dir():
        if str(_p) not in sys.path:
            sys.path.insert(0, str(_p))
        break

from samples._shared import ensure_repo_on_sys_path, setup_logging

ensure_repo_on_sys_path()

from agent_framework.azure import AzureOpenAIResponsesClient
from azure.identity import AzureCliCredential


def _cost(tokens: int, per_1k: float) -> float:
    return (tokens / 1000.0) * per_1k


async def main() -> None:
    setup_logging("INFO")
    prompt = os.environ.get("PROMPT", "Microsoft Agent Framework の要点を一文で")

    agent = AzureOpenAIResponsesClient(credential=AzureCliCredential()).create_agent(
        name="MetricsAgent",
        instructions="Answer concisely in Japanese.",
    )

    t0 = time.perf_counter()
    res = await agent.run(prompt)
    t1 = time.perf_counter()

    latency_ms = (t1 - t0) * 1000
    usage = res.usage_details
    input_tokens = getattr(usage, "input_token_count", 0) or 0
    output_tokens = getattr(usage, "output_token_count", 0) or 0

    in_cost = _cost(input_tokens, float(os.environ.get("INPUT_COST_PER_1K", "0") or 0))
    out_cost = _cost(output_tokens, float(os.environ.get("OUTPUT_COST_PER_1K", "0") or 0))

    print("--- Result ---")
    print(res.text)
    print("\n--- Metrics ---")
    print(f"latency_ms={latency_ms:.1f}")
    print(f"input_tokens={input_tokens} output_tokens={output_tokens}")
    print(f"est_cost_usd={in_cost + out_cost:.6f} (in={in_cost:.6f}, out={out_cost:.6f})")


if __name__ == "__main__":
    asyncio.run(main())

