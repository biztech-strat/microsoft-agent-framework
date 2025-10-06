import asyncio
import argparse
import random
import time
from dataclasses import dataclass
from pathlib import Path
import sys
from typing import Any

# Ensure repo root is on sys.path so `samples` is importable
_here = Path(__file__).resolve()
for _p in (_here.parent, *_here.parents):
    if (_p / "samples").is_dir() and (_p / "python").is_dir():
        if str(_p) not in sys.path:
            sys.path.insert(0, str(_p))
        break

from samples._shared import ensure_repo_on_sys_path, setup_logging

ensure_repo_on_sys_path()

from agent_framework import WorkflowBuilder
from agent_framework._workflows import WorkflowContext
from agent_framework._workflows._executor import Executor, handler


@dataclass
class RetryPolicy:
    max_retries: int = 3
    base_delay: float = 0.5  # seconds
    jitter: float = 0.1      # +/- jitter seconds
    timeout: float = 2.0     # per-attempt timeout seconds


@dataclass
class CircuitBreakerConfig:
    threshold: int = 3           # consecutive failures to open
    reset_timeout_sec: float = 5 # open -> half-open after cooldown


class CircuitBreaker:
    def __init__(self, cfg: CircuitBreakerConfig) -> None:
        self.cfg = cfg
        self._state = "closed"  # closed | open | half-open
        self._fail_count = 0
        self._opened_at: float | None = None

    def _update_state(self) -> None:
        if self._state == "open" and self._opened_at is not None:
            if time.time() - self._opened_at >= self.cfg.reset_timeout_sec:
                self._state = "half-open"

    def before_call(self) -> str:
        self._update_state()
        return self._state

    def record_success(self) -> None:
        self._state = "closed"
        self._fail_count = 0
        self._opened_at = None

    def record_failure(self) -> None:
        self._fail_count += 1
        if self._fail_count >= self.cfg.threshold:
            self._state = "open"
            self._opened_at = time.time()


class ResilientExecutor(Executor):
    def __init__(self, *, policy: RetryPolicy, breaker: CircuitBreaker, fail_first: int) -> None:
        super().__init__(id="resilient")
        self.policy = policy
        self.breaker = breaker
        self._fail_budget = fail_first

    async def _unstable_operation(self, text: str) -> str:
        # 失敗注入: 最初の _fail_budget 回は例外
        if self._fail_budget > 0:
            self._fail_budget -= 1
            raise RuntimeError("Injected failure")
        # 疑似処理: 少し待って成功
        await asyncio.sleep(0.1)
        return f"OK:{text}"

    def _compute_backoff(self, attempt: int) -> float:
        # attempt: 0-based
        delay = self.policy.base_delay * (2 ** attempt)
        if self.policy.jitter:
            delay += random.uniform(-self.policy.jitter, self.policy.jitter)
        return max(0.0, delay)

    @handler
    async def run(self, text: str, ctx: WorkflowContext[Any, str]) -> None:
        state = self.breaker.before_call()
        if state == "open":
            await ctx.yield_output("circuit_open: skip")
            return

        attempts = 0
        last_err: Exception | None = None
        max_attempts = self.policy.max_retries + 1
        while attempts < max_attempts:
            try:
                # half-open allows single probe
                result = await asyncio.wait_for(self._unstable_operation(text), timeout=self.policy.timeout)
                self.breaker.record_success()
                await ctx.yield_output(f"success attempt={attempts+1} result={result}")
                return
            except Exception as e:
                last_err = e
                self.breaker.record_failure()
                attempts += 1
                if attempts >= max_attempts:
                    break
                delay = self._compute_backoff(attempts - 1)
                await asyncio.sleep(delay)

        await ctx.yield_output(f"failed after {attempts} attempt(s): {last_err}")


def parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Retry/Backoff/CircuitBreaker demo")
    p.add_argument("--text", default="ジョブ実行")
    p.add_argument("--fail-first", type=int, default=2)
    p.add_argument("--max-retries", type=int, default=3)
    p.add_argument("--base-delay", type=float, default=0.5)
    p.add_argument("--jitter", type=float, default=0.1)
    p.add_argument("--timeout", type=float, default=1.0)
    p.add_argument("--circuit-threshold", type=int, default=3)
    p.add_argument("--circuit-reset-sec", type=float, default=5.0)
    return p.parse_args(argv)


async def main(argv: list[str]) -> None:
    setup_logging("INFO")
    args = parse_args(argv)

    policy = RetryPolicy(
        max_retries=args.max_retries,
        base_delay=args.base_delay,
        jitter=args.jitter,
        timeout=args.timeout,
    )
    breaker = CircuitBreaker(CircuitBreakerConfig(threshold=args.circuit_threshold, reset_timeout_sec=args.circuit_reset_sec))

    resilient = ResilientExecutor(policy=policy, breaker=breaker, fail_first=args.fail_first)

    wb = WorkflowBuilder(name="retry_backoff_circuit")
    wb.set_start_executor(resilient)
    wf = wb.build()

    events = await wf.run(args.text, include_status_events=True)
    for ev in events:
        # Print final output or status for clarity
        if ev.__class__.__name__ == "WorkflowOutputEvent":
            print(f"[output] {ev.data}")
        if ev.__class__.__name__ == "WorkflowStatusEvent":
            print(f"[status] {ev.state.name}")


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1:]))

