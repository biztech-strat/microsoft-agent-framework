import asyncio
import argparse
from pathlib import Path
import sys
from typing import List

# Ensure repo root on sys.path
_here = Path(__file__).resolve()
for _p in (_here.parent, *_here.parents):
    if (_p / "samples").is_dir() and (_p / "python").is_dir():
        if str(_p) not in sys.path:
            sys.path.insert(0, str(_p))
        break

from samples._shared import ensure_repo_on_sys_path, setup_logging

ensure_repo_on_sys_path()

from agent_framework import AgentMiddleware, AgentRunContext, ChatResponse, Role
from agent_framework.azure import AzureOpenAIResponsesClient
from azure.identity import AzureCliCredential


class SafetyMiddleware(AgentMiddleware):
    def __init__(self, banned_keywords: List[str]) -> None:
        self.banned = [w.lower() for w in banned_keywords]

    def _violates(self, text: str) -> bool:
        t = text.lower()
        return any(w in t for w in self.banned)

    async def process(self, context: AgentRunContext, next):
        # Combine user texts in this invocation (Role enum or str-safe)
        user_inputs = []
        for m in context.messages or []:
            role = getattr(m, "role", None)
            is_user = False
            if role == Role.USER:
                is_user = True
            elif isinstance(role, str) and role.lower() == "user":
                is_user = True
            elif hasattr(role, "value") and isinstance(getattr(role, "value"), str) and role.value.lower() == "user":
                is_user = True
            if is_user:
                user_inputs.append(getattr(m, "text", "") or "")
        combined = "\n".join(user_inputs)

        if combined and self._violates(combined):
            context.result = ChatResponse(text="申し訳ありません。その内容には対応できません。安全な観点から別の表現で質問してください。")
            return

        await next(context)


def parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Safety & filters demo")
    p.add_argument("--prompt", default="このサンプルの概要を教えて")
    return p.parse_args(argv)


async def main(argv: list[str]) -> None:
    setup_logging("INFO")
    args = parse_args(argv)

    banned = ["危険な作業手順", "違法行為", "爆薬の作り方"]
    mw = SafetyMiddleware(banned)

    agent = AzureOpenAIResponsesClient(credential=AzureCliCredential()).create_agent(
        name="SafetyAgent",
        instructions="Answer briefly in Japanese.",
        middleware=[mw],
    )

    res = await agent.run(args.prompt)
    print(res.text)


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1:]))
