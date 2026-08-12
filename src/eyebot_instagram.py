"""Instagram live-event detector and Discord notification child."""

import asyncio

from services.liveNotificationService import LiveEvent, LiveNotificationService, load_platform_runtime
from services.logService import LogService
from services.platformWorkerService import PlatformWorkerService
from services.instagramAccountService import InstagramAccountMonitorService


async def detect_instagram_live(settings, session):
    account_id = str(settings.get("account_id") or "")
    token = str(settings.get("access_token") or "")
    if not account_id or not token:
        return None
    async with session.get(
        f"https://graph.facebook.com/v26.0/{account_id}/live_media",
        params={"fields": "id,caption,permalink,timestamp,username,media_url,thumbnail_url", "access_token": token},
    ) as response:
        response.raise_for_status()
        rows = (await response.json()).get("data", [])
    if not rows:
        return None
    media = rows[0]
    event_id = str(media["id"])
    username = str(media.get("username") or account_id)
    return LiveEvent(event_id, str(media.get("caption") or f"{username} is live"), str(media.get("permalink") or f"https://www.instagram.com/{username}/"), username, "Instagram Live", str(media.get("thumbnail_url") or media.get("media_url") or ""))


async def run():
    config, service = load_platform_runtime("instagram")
    logger = LogService("instagram", config["logging"])
    account_monitor = InstagramAccountMonitorService(
        config,
        service,
        logger,
        poll_seconds=config.get("instagram", {}).get("posts_poll_seconds", 60),
    )
    await asyncio.gather(
        LiveNotificationService("instagram", config, service, detect_instagram_live, logger).run_forever(),
        PlatformWorkerService("instagram", service, logger).run_forever(),
        account_monitor.run_forever(),
    )


def main():
    asyncio.run(run())


if __name__ == "__main__":
    main()
