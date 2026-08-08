"""Kick live-event detector and Discord notification child."""

import asyncio

from services.liveNotificationService import LiveEvent, LiveNotificationService, load_platform_runtime
from services.logService import LogService


async def detect_kick_live(settings, session):
    channel = str(settings.get("channel") or "").strip().casefold()
    token = str(settings.get("access_token") or "")
    if not channel or not token:
        return None
    async with session.get(
        "https://api.kick.com/public/v1/channels",
        params={"slug": channel},
        headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
    ) as response:
        response.raise_for_status()
        rows = (await response.json()).get("data", [])
    if not rows:
        return None
    channel_data = rows[0]
    stream = channel_data.get("stream") or channel_data.get("livestream") or {}
    if not stream or stream.get("is_live") is False:
        return None
    event_id = str(stream.get("id") or stream.get("created_at") or channel)
    thumbnail = stream.get("thumbnail") or stream.get("thumbnail_url") or ""
    if isinstance(thumbnail, dict):
        thumbnail = thumbnail.get("url", "")
    return LiveEvent(event_id, str(stream.get("title") or f"{channel} is live"), f"https://kick.com/{channel}", str(channel_data.get("name") or channel), str(stream.get("category", {}).get("name", "") if isinstance(stream.get("category"), dict) else ""), str(thumbnail))


async def run():
    config, service = load_platform_runtime("kick")
    logger = LogService("kick", config["logging"])
    await LiveNotificationService("kick", config, service, detect_kick_live, logger).run_forever()


def main():
    asyncio.run(run())


if __name__ == "__main__":
    main()
