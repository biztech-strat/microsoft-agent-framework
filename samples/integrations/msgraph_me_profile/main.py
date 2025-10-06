import asyncio
import argparse
import os
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


async def fetch_me_real() -> Dict[str, Any]:
    import httpx  # type: ignore
    from azure.identity.aio import AzureCliCredential  # type: ignore

    scope = os.environ.get("GRAPH_SCOPE", "https://graph.microsoft.com/.default")
    base = os.environ.get("GRAPH_BASE", "https://graph.microsoft.com/v1.0")

    cred = AzureCliCredential()
    token = await cred.get_token(scope)
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.get(f"{base}/me", headers={"Authorization": f"Bearer {token.token}"})
        r.raise_for_status()
        return r.json()


async def fetch_me_mock() -> Dict[str, Any]:
    return {
        "displayName": "Contoso User",
        "userPrincipalName": "user@contoso.com",
        "mail": "user@contoso.com",
        "id": "00000000-0000-0000-0000-000000000000",
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Microsoft Graph /me demo")
    p.add_argument("--mock", type=int, default=0, help="1でモック、0で実リクエスト")
    return p.parse_args(argv)


async def main(argv: list[str]) -> None:
    setup_logging("INFO")
    args = parse_args(argv)
    try:
        data = await (fetch_me_mock() if args.mock else fetch_me_real())
        print({k: data.get(k) for k in ["displayName", "userPrincipalName", "mail", "id"]})
    except Exception as e:
        print(f"Graph call failed: {e}")


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1:]))

