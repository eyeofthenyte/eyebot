"""Substack RSS notification child."""

import asyncio

from services.feedNotificationService import FeedNotificationService
from services.liveNotificationService import load_platform_runtime
from services.logService import LogService


async def run():
    config, service = load_platform_runtime("substack")
    await FeedNotificationService(
        config, service, LogService("substack", config["logging"])
    ).run_forever()


def main():
    asyncio.run(run())


if __name__ == "__main__":
    main()
