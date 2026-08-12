"""Bluesky outbound-job child."""

import asyncio

from services.liveNotificationService import load_platform_runtime
from services.logService import LogService
from services.platformWorkerService import PlatformWorkerService
from services.blueskyAccountService import BlueskyAccountMonitorService


async def run():
    config, service = load_platform_runtime("bluesky")
    logger = LogService("bluesky", config["logging"])
    monitor = BlueskyAccountMonitorService(
        config,
        service,
        logger,
        poll_seconds=config.get("bluesky", {}).get("posts_poll_seconds", 120),
    )
    await asyncio.gather(
        PlatformWorkerService("bluesky", service, logger).run_forever(),
        monitor.run_forever(),
    )


def main():
    asyncio.run(run())


if __name__ == "__main__":
    main()
