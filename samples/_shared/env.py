import os
from pathlib import Path
from typing import Iterable


def load_env(paths: Iterable[str] | None = None) -> None:
    """Minimal .env loader for samples.

    - Supports `KEY=VALUE` lines
    - Ignores blanks and lines starting with `#`
    - Keeps existing environment values (does not overwrite)
    """
    if not paths:
        paths = (".env",)

    for p in paths:
        path = Path(p)
        if not path.exists():
            continue
        for raw in path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            os.environ.setdefault(key, value)

