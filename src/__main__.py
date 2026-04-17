"""
Satoshi Pulse v2 — entry point.

Usage:
    python -m src                        # Run API server (default)
    python -m src scheduler              # Run data collector scheduler only
    python -m src api                    # Run API server only
    python -m src full                   # Run API + scheduler together
"""

import asyncio
import sys


def main() -> None:
    mode = sys.argv[1] if len(sys.argv) > 1 else "api"

    if mode == "scheduler":
        from src.scheduler.scheduler import main as scheduler_main

        asyncio.run(scheduler_main())

    elif mode == "api":
        import uvicorn

        uvicorn.run(
            "src.api.main:app",
            host="0.0.0.0",
            port=8000,
            reload=False,
            log_level="info",
        )

    elif mode == "full":
        asyncio.run(_run_full())

    else:
        print(f"Unknown mode: {mode}")
        print("Usage: python -m src [api|scheduler|full]")
        sys.exit(1)


async def _run_full() -> None:
    """Run both the API server and the scheduler concurrently."""
    import uvicorn

    from src.scheduler.scheduler import Scheduler

    scheduler = Scheduler()

    config = uvicorn.Config(
        "src.api.main:app",
        host="0.0.0.0",
        port=8000,
        log_level="info",
    )
    server = uvicorn.Server(config)

    await asyncio.gather(
        server.serve(),
        scheduler.start(),
    )


if __name__ == "__main__":
    main()
