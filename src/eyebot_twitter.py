"""X Spaces live-event detector and Discord notification child."""

import asyncio

from services.liveNotificationService import LiveEvent, LiveNotificationService, load_platform_runtime
from services.logService import LogService
from services.platformWorkerService import PlatformWorkerService
from services.twitterAccountService import TwitterAccountMonitorService


async def detect_twitter_live(settings, session):
    user_id = str(settings.get("user_id") or "")
    token = str(settings.get("bearer_token") or "")
    if not user_id or not token:
        return None
    async with session.get(
        "https://api.x.com/2/spaces/by/creator_ids",
        params={"user_ids": user_id, "space.fields": "id,state,title,started_at,creator_id"},
        headers={"Authorization": f"Bearer {token}"},
    ) as response:
        response.raise_for_status()
        rows = (await response.json()).get("data", [])
    live = next((space for space in rows if space.get("state") == "live"), None)
    if not live:
        return None
    event_id = str(live["id"])
    return LiveEvent(event_id, str(live.get("title") or "Live Space on X"), f"https://x.com/i/spaces/{event_id}", str(settings.get("handle") or user_id), "Live audio Space on X")


async def run():
    config, service = load_platform_runtime("twitter")
    logger = LogService("twitter", config["logging"])
    account_monitor = TwitterAccountMonitorService(
        config,
        service,
        logger,
        poll_seconds=config.get("twitter", {}).get("posts_poll_seconds", 300),
    )
    await asyncio.gather(
        LiveNotificationService("twitter", config, service, detect_twitter_live, logger).run_forever(),
        PlatformWorkerService("twitter", service, logger).run_forever(),
        account_monitor.run_forever(),
    )


def main():
    asyncio.run(run())


if __name__ == "__main__":
    main()
