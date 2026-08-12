"""TikTok approved Content Posting job child."""

import asyncio

from services.liveNotificationService import load_platform_runtime
from services.logService import LogService
from services.platformWorkerService import PlatformWorkerService
from services.tiktokVideoMonitorService import TikTokVideoMonitorService


async def run():
    config, service = load_platform_runtime("tiktok")
    logger = LogService("tiktok", config["logging"])
    await asyncio.gather(
        PlatformWorkerService("tiktok", service, logger).run_forever(),
        TikTokVideoMonitorService(
            config, service, logger,
            poll_seconds=config.get("tiktok", {}).get("videos_poll_seconds", 300),
        ).run_forever(),
    )


def main():
    asyncio.run(run())


if __name__ == "__main__":
    main()
