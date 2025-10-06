import asyncio
import argparse
import os
from dataclasses import dataclass
from pathlib import Path
import random
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


# ---------- Demo (mock) backend ----------
class InProcBus:
    def __init__(self) -> None:
        self.main: asyncio.Queue[str] = asyncio.Queue()
        self.dead: asyncio.Queue[str] = asyncio.Queue()

    async def send(self, text: str) -> None:
        await self.main.put(text)

    async def receive(self) -> str:
        return await self.main.get()

    async def deadletter(self, text: str) -> None:
        await self.dead.put(text)


# ---------- Real backend (optional) ----------
class ServiceBusReal:
    def __init__(self, conn: str, queue: str) -> None:
        self.conn = conn
        self.queue = queue

    async def send(self, text: str) -> None:  # pragma: no cover
        from azure.servicebus.aio import ServiceBusClient
        async with ServiceBusClient.from_connection_string(self.conn) as sb:
            sender = sb.get_queue_sender(self.queue)
            async with sender:
                from azure.servicebus import ServiceBusMessage
                await sender.send_messages(ServiceBusMessage(text))

    async def receive(self) -> str:  # pragma: no cover
        from azure.servicebus.aio import ServiceBusClient
        async with ServiceBusClient.from_connection_string(self.conn) as sb:
            receiver = sb.get_queue_receiver(self.queue, max_wait_time=5)
            async with receiver:
                async for msg in receiver:
                    body = str(b"".join([b for b in msg.body]))
                    await receiver.complete_message(msg)
                    return body
        raise TimeoutError("No message received")

    async def deadletter(self, text: str) -> None:  # pragma: no cover
        # No direct dead-letter send; typically move/abandon to exceed delivery count.
        # For demo purposes we emit a log.
        print(f"[real] dead-letter simulated: {text}")


@dataclass
class WorkerConfig:
    concurrency: int = 2
    max_attempts: int = 3
    fail_ratio: float = 0.0  # for demo: random failure injection


async def process_message(text: str, cfg: WorkerConfig) -> bool:
    # Inject failures
    if random.random() < cfg.fail_ratio:
        raise RuntimeError("injected failure")
    await asyncio.sleep(0.05)
    print(f"[ok] {text}")
    return True


async def run_worker(bus: Any, cfg: WorkerConfig) -> None:
    sem = asyncio.Semaphore(cfg.concurrency)

    async def handle_one(text: str) -> None:
        attempt = 0
        while True:
            try:
                await process_message(text, cfg)
                return
            except Exception as e:
                attempt += 1
                print(f"[err] attempt={attempt} text='{text}' err={e}")
                if attempt >= cfg.max_attempts:
                    await bus.deadletter(text)
                    print(f"[dead] {text}")
                    return
                await asyncio.sleep(0.2 * attempt)

    async def worker_loop() -> None:
        while True:
            text = await bus.receive()
            await sem.acquire()
            asyncio.create_task(
                (async def():
                    try:
                        await handle_one(text)
                    finally:
                        sem.release()
                )()
            )

    await worker_loop()


def parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Azure Service Bus integration demo")
    sub = p.add_subparsers(dest="cmd", required=True)

    d = sub.add_parser("demo")
    d.add_argument("--count", type=int, default=10)
    d.add_argument("--concurrency", type=int, default=2)
    d.add_argument("--fail-ratio", type=float, default=0.1)

    s = sub.add_parser("send")
    s.add_argument("--text", default="hello")
    s.add_argument("--real", type=int, default=0)

    w = sub.add_parser("worker")
    w.add_argument("--real", type=int, default=0)
    w.add_argument("--concurrency", type=int, default=2)

    return p.parse_args(argv)


async def main(argv: list[str]) -> None:
    setup_logging("INFO")
    args = parse_args(argv)

    if args.cmd == "demo":
        bus = InProcBus()
        # produce
        for i in range(args.count):
            await bus.send(f"msg-{i}")
        # consume
        cfg = WorkerConfig(concurrency=args.concurrency, fail_ratio=args.fail_ratio)
        await asyncio.wait_for(run_worker(bus, cfg), timeout=5.0)
        return

    # real or mock single action
    if getattr(args, "real", 0):  # real path
        conn = os.environ.get("AZ_SERVICEBUS_CONNECTION")
        queue = os.environ.get("AZ_SERVICEBUS_QUEUE")
        if not (conn and queue):
            raise RuntimeError("AZ_SERVICEBUS_CONNECTION/AZ_SERVICEBUS_QUEUE not set")
        bus = ServiceBusReal(conn, queue)
    else:
        bus = InProcBus()

    if args.cmd == "send":
        await bus.send(args.text)
        print("sent")
        return

    if args.cmd == "worker":
        cfg = WorkerConfig(concurrency=args.concurrency)
        await run_worker(bus, cfg)


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1:]))

