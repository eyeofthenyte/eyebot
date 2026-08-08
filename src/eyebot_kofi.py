"""Ko-fi lifecycle child; signed delivery is handled by EyeBot gateway."""

import asyncio

from services.liveNotificationService import load_platform_runtime
from services.logService import LogService


async def run():
    config, _service = load_platform_runtime("kofi")
    logger = LogService("kofi", config["logging"])
    if config.get("gateway", {}).get("enabled") is not True:
        raise RuntimeError("Ko-fi requires gateway.enabled: true")
    logger.info("Ko-fi webhook routing is active through the EyeBot gateway")
    await asyncio.Event().wait()


def main():
    asyncio.run(run())


if __name__ == "__main__":
    main()
