"""TikTok approved Content Posting job child."""

import asyncio

from services.liveNotificationService import load_platform_runtime
from services.logService import LogService
from services.platformWorkerService import PlatformWorkerService


async def run():
    config, service = load_platform_runtime("tiktok")
    await PlatformWorkerService(
        "tiktok", service, LogService("tiktok", config["logging"])
    ).run_forever()


def main():
    asyncio.run(run())


if __name__ == "__main__":
    main()
