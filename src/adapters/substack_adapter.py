"""Public Substack RSS newsletter and podcast retrieval adapter."""

import asyncio

from adapters.platform_api_adapter import PlatformApiAdapter
from core.command_model import CommandPlatform


class SubstackAdapter(PlatformApiAdapter):
    def __init__(self):
        super().__init__(CommandPlatform.SUBSTACK, ("newsletters", "podcasts"))

    async def fetch_feed(self, settings):
        publication = str(settings.get("publication_url") or "").rstrip("/")
        if not publication.startswith("https://"):
            raise ValueError("Substack publication_url must use HTTPS")

        def parse():
            import feedparser

            return feedparser.parse(publication + "/feed")

        result = await asyncio.to_thread(parse)
        if getattr(result, "bozo", False) and not result.entries:
            raise RuntimeError(f"Unable to read Substack feed: {result.bozo_exception}")
        return result.entries


SUBSTACK_ADAPTER = SubstackAdapter()
