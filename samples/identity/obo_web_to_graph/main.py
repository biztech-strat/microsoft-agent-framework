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

from samples._shared import ensure_repo_on_sys_path, setup_logging, load_env

ensure_repo_on_sys_path()


async def obo_exchange_and_call_graph(user_assertion: str) -> Dict[str, Any]:  # pragma: no cover
    import httpx  # type: ignore
    from azure.identity.aio import OnBehalfOfCredential  # type: ignore

    tenant = os.environ["AZURE_TENANT_ID"]
    client_id = os.environ["AZURE_CLIENT_ID"]
    client_secret = os.environ["AZURE_CLIENT_SECRET"]
    scope = os.environ.get("GRAPH_SCOPE", "https://graph.microsoft.com/.default")
    base = os.environ.get("GRAPH_BASE", "https://graph.microsoft.com/v1.0")

    cred = OnBehalfOfCredential(tenant_id=tenant, client_id=client_id, client_secret=client_secret, user_assertion=user_assertion)
    token = await cred.get_token(scope)

    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.get(f"{base}/me", headers={"Authorization": f"Bearer {token.token}"})
        r.raise_for_status()
        return r.json()


def parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="OBO -> Graph /me demo")
    p.add_argument("--mock", type=int, default=0)
    p.add_argument("--user-assertion", default=None, help="User access token from upstream app (Bearer JWT)")
    return p.parse_args(argv)


async def main(argv: list[str]) -> None:
    setup_logging("INFO")
    load_env((".env",))
    args = parse_args(argv)

    if args.mock or not args.user_assertion:
        print({
            "flow": "mock",
            "steps": [
                "receive user JWT (Authorization: Bearer <token>)",
                "exchange via OBO to Graph token",
                "call Graph /me",
            ],
            "me": {
                "displayName": "Contoso User",
                "userPrincipalName": "user@contoso.com",
            },
        })
        return

    try:
        data = await obo_exchange_and_call_graph(args.user_assertion)
        print({k: data.get(k) for k in ["displayName", "userPrincipalName", "id", "mail"]})
    except Exception as e:
        print(f"OBO flow failed: {e}")


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1:]))

