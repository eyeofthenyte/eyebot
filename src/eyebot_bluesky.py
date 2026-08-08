"""Bluesky outbound-job child."""

import asyncio

from services.liveNotificationService import load_platform_runtime
from services.logService import LogService
from services.platformWorkerService import PlatformWorkerService


async def run():
    config, service = load_platform_runtime("bluesky")
    await PlatformWorkerService(
        "bluesky", service, LogService("bluesky", config["logging"])
    ).run_forever()


def main():
    asyncio.run(run())


if __name__ == "__main__":
    main()
