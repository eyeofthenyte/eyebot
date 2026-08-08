"""Bounded Discord REST delivery for non-Discord child processes."""

from __future__ import annotations

from collections.abc import Mapping


class DiscordPostingService:
    API_ROOT = "https://discord.com/api/v10"

    def __init__(self, config):
        discord = config.get("discord", {})
        self.token = discord.get("bot_token", "") if isinstance(discord, Mapping) else ""

    async def send(self, session, channel_id, content, *, title=None, url=None):
        if not self.token:
            raise RuntimeError("discord.bot_token is unavailable")
        payload = {
            "content": str(content)[:2000],
            "allowed_mentions": {"parse": []},
        }
        if title:
            embed = {"title": str(title)[:256], "color": 0x5865F2}
            if isinstance(url, str) and url.startswith("https://"):
                embed["url"] = url
            payload["embeds"] = [embed]
        async with session.post(
            f"{self.API_ROOT}/channels/{int(channel_id)}/messages",
            headers={"Authorization": f"Bot {self.token}"},
            json=payload,
        ) as response:
            if response.status not in {200, 201}:
                detail = (await response.text())[:500]
                raise RuntimeError(
                    f"Discord delivery failed: HTTP {response.status} {detail}"
                )
