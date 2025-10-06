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

from samples._shared import ensure_repo_on_sys_path, load_env, setup_logging

# Ensure in-repo core packages take precedence over site-packages
ensure_repo_on_sys_path()

from agent_framework.devui import serve

from samples.devui.agents.weather_agent.agent import create_agent


async def main() -> None:
    setup_logging("INFO")
    # Load .env for model and auth. DevUI also loads .env when using CLI discovery,
    # but we load here for programmatic mode.
    repo_root = _here.parent.parent  # .../samples
    load_env(
        (
            str(_here.parent / "agents" / ".env"),  # samples/devui/agents/.env
            str(repo_root / ".env"),                 # samples/.env
            ".env",                                  # current dir fallback
        )
    )

    agent = create_agent()
    # Launch DevUI and auto open browser
    await serve(entities=[agent], auto_open=True)


if __name__ == "__main__":
    asyncio.run(main())

