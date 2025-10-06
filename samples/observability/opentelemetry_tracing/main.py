import asyncio
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

from agent_framework.observability import create_workflow_span, OtelAttr


def setup_otel_console() -> None:
    try:
        from opentelemetry import trace
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import (  # type: ignore
            ConsoleSpanExporter,
            SimpleSpanProcessor,
        )

        provider = TracerProvider(resource=Resource.create({"service.name": "maf-samples"}))
        provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
        trace.set_tracer_provider(provider)
    except Exception as e:  # pragma: no cover
        print(f"OTel console setup skipped: {e}")


async def main() -> None:
    setup_logging("INFO")
    setup_otel_console()

    # Minimal workflow-level span
    with create_workflow_span(OtelAttr.WORKFLOW_RUN_SPAN, attributes={"demo": True}) as span:
        span.add_event("custom-event", {"key": "value"})
        # Simulate nested work
        await asyncio.sleep(0.05)
        # Child span
        from agent_framework.observability import create_processing_span

        with create_processing_span("demo-executor", "DemoExecutor", "str"):
            await asyncio.sleep(0.05)
    print("Tracing complete (see console spans above)")


if __name__ == "__main__":
    asyncio.run(main())

