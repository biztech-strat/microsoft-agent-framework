import sys
from pathlib import Path
from typing import Sequence


def ensure_repo_on_sys_path() -> Sequence[str]:
    """Prepend this repo's `python/packages/*` paths to sys.path if missing.

    This lets samples import the in-repo `agent_framework` and
    `agent_framework_azure_ai` even when an older site-packages version exists.
    Returns the list of paths that were added (in order).
    """
    here = Path(__file__).resolve()
    added: list[str] = []

    # Walk upwards until we find a folder containing python/packages/*
    for root in (here, *here.parents):
        core = root / "python" / "packages" / "core"
        azure_ai = root / "python" / "packages" / "azure-ai"
        if core.exists() and azure_ai.exists():
            for p in (str(core), str(azure_ai)):
                if p not in sys.path:
                    sys.path.insert(0, p)
                    added.append(p)
            break

    return added

