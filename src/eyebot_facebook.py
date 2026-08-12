"""Facebook live-event detector and Discord notification child."""

import asyncio

from services.liveNotificationService import LiveEvent, LiveNotificationService, load_platform_runtime
from services.logService import LogService
from services.platformWorkerService import PlatformWorkerService
from services.facebookPageService import FacebookPageMonitorService


async def detect_facebook_live(settings, session):
    page_id = str(settings.get("page_id") or "")
    token = str(settings.get("access_token") or "")
    if not page_id or not token:
        return None
    async with session.get(
        f"https://graph.facebook.com/v26.0/{page_id}/live_videos",
        params={"broadcast_status": "LIVE", "fields": "id,title,status,permalink_url,description", "access_token": token},
    ) as response:
        response.raise_for_status()
        rows = (await response.json()).get("data", [])
    live = next((row for row in rows if row.get("status") in {"LIVE", "LIVE_NOW"}), None)
    if not live:
        return None
    event_id = str(live["id"])
    url = str(live.get("permalink_url") or f"https://www.facebook.com/{event_id}")
    if url.startswith("/"):
        url = "https://www.facebook.com" + url
    return LiveEvent(event_id, str(live.get("title") or "Facebook Live"), url, str(settings.get("page_name") or page_id), str(live.get("description") or ""))


async def run():
    config, service = load_platform_runtime("facebook")
    logger = LogService("facebook", config["logging"])
    page_monitor = FacebookPageMonitorService(
        config,
        service,
        logger,
        poll_seconds=config.get("facebook", {}).get("posts_poll_seconds", 60),
    )
    await asyncio.gather(
        LiveNotificationService("facebook", config, service, detect_facebook_live, logger).run_forever(),
        PlatformWorkerService("facebook", service, logger).run_forever(),
        page_monitor.run_forever(),
    )


def main():
    asyncio.run(run())


if __name__ == "__main__":
    main()
