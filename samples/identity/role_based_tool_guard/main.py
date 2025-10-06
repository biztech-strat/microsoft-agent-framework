import asyncio
import argparse
from pathlib import Path
import sys
from typing import Annotated, Callable, Iterable

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


def require_roles(allowed: Iterable[str]) -> Callable[[Callable[..., str]], Callable[..., str]]:
    allowed_set = set(r.lower() for r in allowed)

    def decorator(func: Callable[..., str]) -> Callable[..., str]:
        def wrapper(*args, **kwargs) -> str:
            roles = set(str(kwargs.pop("_roles", "")).lower().split(",")) if "_roles" in kwargs else set()
            roles = set(r for r in roles if r)
            if not roles & allowed_set:
                raise PermissionError(f"forbidden: required roles {sorted(allowed_set)}, actual {sorted(roles)}")
            return func(*args, **kwargs)

        return wrapper

    return decorator


@require_roles(["admin", "analyst"])  # admin/analyst 以外は拒否
def get_sales_report(
    period: Annotated[str, Field(description="Target period like '2025-09' or 'Q3'")],
    *,
    _roles: str = "",
) -> str:
    # 実際にはDB/BIツール等を叩く
    return f"Sales report for {period}: total=1,234,567"


def parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Role-based tool guard demo")
    p.add_argument("--roles", default="reader", help="comma-separated roles (e.g., admin,finance)")
    p.add_argument("--query", default="売上データを集計して")
    p.add_argument("--period", default="2025-09")
    return p.parse_args(argv)


async def main(argv: list[str]) -> None:
    setup_logging("INFO")
    args = parse_args(argv)

    def guarded_tool(period: str) -> str:
        # ランタイムでロールを注入
        return get_sales_report(period, _roles=args.roles)

    agent = AzureOpenAIResponsesClient(credential=AzureCliCredential()).create_agent(
        name="RBACAgent",
        instructions=("If the user asks for sales data, call the tool. If the tool errors, explain that it's forbidden."),
        tools=guarded_tool,
    )

    print("User:", args.query)
    print("Agent: ", end="")
    try:
        async for upd in agent.run_stream(f"{args.query} 対象期間: {args.period}"):
            if upd.text:
                print(upd.text, end="", flush=True)
    except PermissionError as e:
        print(str(e))
    print()


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1:]))

