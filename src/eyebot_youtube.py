"""YouTube live-event detector and Discord notification child."""

import asyncio

from services.liveNotificationService import LiveEvent, LiveNotificationService, load_platform_runtime
from services.logService import LogService


async def detect_youtube_live(settings, session):
    channel_id = str(settings.get("channel_id") or "")
    api_key = str(settings.get("api_key") or "")
    if not channel_id or not api_key:
        return None
    async with session.get(
        "https://www.googleapis.com/youtube/v3/search",
        params={"part": "snippet", "channelId": channel_id, "eventType": "live", "type": "video", "maxResults": 1, "key": api_key},
    ) as response:
        response.raise_for_status()
        rows = (await response.json()).get("items", [])
    if not rows:
        return None
    item = rows[0]
    snippet = item.get("snippet", {})
    video_id = str(item.get("id", {}).get("videoId") or "")
    thumbnails = snippet.get("thumbnails", {})
    thumbnail = (thumbnails.get("high") or thumbnails.get("medium") or thumbnails.get("default") or {}).get("url", "")
    return LiveEvent(video_id, str(snippet.get("title") or "YouTube livestream"), f"https://www.youtube.com/watch?v={video_id}", str(snippet.get("channelTitle") or channel_id), str(snippet.get("description") or ""), str(thumbnail))


async def run():
    config, service = load_platform_runtime("youtube")
    logger = LogService("youtube", config["logging"])
    await LiveNotificationService("youtube", config, service, detect_youtube_live, logger).run_forever()


def main():
    asyncio.run(run())


if __name__ == "__main__":
    main()
