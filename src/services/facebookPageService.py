"""Resolve and poll guild-owned Facebook Page feed subscriptions."""

from __future__ import annotations

import asyncio
import json
import os
import tempfile
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from services.discordPostingService import DiscordPostingService


GRAPH_ROOT = "https://graph.facebook.com/v26.0"
FACEBOOK_HOSTS = frozenset(
    {"facebook.com", "www.facebook.com", "m.facebook.com", "web.facebook.com"}
)


def facebook_page_reference(value: str) -> str:
    """Return a numeric Page ID or URL username suitable for Graph lookup."""
    supplied = str(value or "").strip()
    if supplied.isdigit():
        return supplied
    parsed = urlparse(supplied)
    if parsed.scheme != "https" or parsed.hostname not in FACEBOOK_HOSTS:
        raise ValueError("must be an HTTPS facebook.com Page URL")
    if parsed.path.rstrip("/") == "/profile.php":
        identifier = parse_qs(parsed.query).get("id", [""])[0]
        if identifier.isdigit():
            return identifier
        raise ValueError("profile.php URL does not contain a numeric id")
    parts = [part for part in parsed.path.split("/") if part]
    if len(parts) != 1 or parts[0].casefold() in {
        "groups", "events", "marketplace", "people", "posts", "reel", "watch"
    }:
        raise ValueError("URL must identify a Facebook Page, not Page content")
    return parts[0]


async def _graph_get(session, path, token, params=None):
    selected = dict(params or {})
    selected["access_token"] = token
    async with session.get(f"{GRAPH_ROOT}/{path}", params=selected) as response:
        body = await response.json(content_type=None)
        if not 200 <= response.status < 300:
            detail = body.get("error", {}).get("message") if isinstance(body, dict) else None
            raise ValueError(detail or f"Meta Graph API returned HTTP {response.status}")
        return body


async def resolve_facebook_page(page_url, token, session):
    """Resolve a URL only when the connected Meta token can access the Page."""
    reference = facebook_page_reference(page_url)
    accounts = await _graph_get(
        session, "me/accounts", token, {"fields": "id,name,link", "limit": 100}
    )
    supplied_url = str(page_url).rstrip("/").casefold()
    body = None
    for row in accounts.get("data", ()):
        if not isinstance(row, dict):
            continue
        link = str(row.get("link") or "")
        try:
            link_reference = facebook_page_reference(link)
        except ValueError:
            link_reference = ""
        if (
            str(row.get("id") or "") == reference
            or link.rstrip("/").casefold() == supplied_url
            or link_reference.casefold() == reference.casefold()
        ):
            body = row
            break
    if body is None:
        resolved = await _graph_get(
            session,
            reference,
            token,
            {"fields": "id,name,link"},
        )
        resolved_id = str(resolved.get("id") or "")
        body = next(
            (
                row
                for row in accounts.get("data", ())
                if isinstance(row, dict) and str(row.get("id") or "") == resolved_id
            ),
            None,
        )
    if body is None:
        raise ValueError("Page is not managed by the connected Meta account")
    page_id = str(body.get("id") or "")
    name = str(body.get("name") or "")
    if not page_id or not name:
        raise ValueError("Meta did not return an accessible Facebook Page")
    await _graph_get(session, f"{page_id}/feed", token, {"fields": "id", "limit": 1})
    link = str(body.get("link") or page_url)
    if not link.startswith("https://"):
        link = page_url
    return {"page_id": page_id, "name": name, "url": link}


class FacebookPageMonitorService:
    """Poll monitored Page feeds and deliver newly observed posts once."""

    def __init__(self, config, platform_service, logger, *, poll_seconds=60):
        from services.tokenRefreshService import TokenRefreshService

        self.config = config
        self.platforms = platform_service
        self.logger = logger
        self.discord = DiscordPostingService(config)
        self.tokens = TokenRefreshService(platform_service, logger)
        self.poll_seconds = min(3600, max(30, int(poll_seconds)))
        root = Path(platform_service.guild_config_dir) / ".facebook_posts"
        self.state_path = root / "state.json"
        try:
            value = json.loads(self.state_path.read_text(encoding="utf-8"))
            self.state = value if isinstance(value, dict) else {}
        except (OSError, UnicodeError, json.JSONDecodeError):
            self.state = {}

    def _save(self):
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        descriptor, name = tempfile.mkstemp(dir=self.state_path.parent, suffix=".tmp")
        temporary = Path(name)
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as output:
                json.dump(self.state, output, sort_keys=True)
                output.flush()
                os.fsync(output.fileno())
            os.replace(temporary, self.state_path)
        finally:
            if temporary.exists():
                temporary.unlink()

    async def poll_once(self, session):
        changed = False
        active = set()
        for guild_id in sorted(self.platforms.discord_guilds()):
            settings = self.platforms.effective_guild_platform(guild_id, "facebook")
            if settings.get("available", True) is not True or settings.get("enabled") is not True:
                continue
            try:
                await self.tokens.refresh_guild(guild_id, "facebook", session)
            except (OSError, RuntimeError, ValueError) as error:
                self.logger.error(
                    f"Skipping Facebook Pages for guild {guild_id}: {error}",
                    guild_id=guild_id,
                )
                continue
            settings = self.platforms.effective_guild_platform(guild_id, "facebook")
            token = str(
                settings.get("user_access_token")
                or settings.get("access_token")
                or ""
            )
            pages = settings.get("monitored_pages", ())
            if not token or not isinstance(pages, (list, tuple)):
                continue
            for page in pages:
                if not isinstance(page, dict):
                    continue
                page_id = str(page.get("page_id") or "")
                destination = str(page.get("destination_channel") or settings.get("destination_channel") or "")
                if not page_id or not destination.isdigit():
                    continue
                key = f"{guild_id}:{page_id}"
                active.add(key)
                try:
                    body = await _graph_get(
                        session,
                        f"{page_id}/feed",
                        token,
                        {"fields": "id,message,permalink_url,created_time,full_picture", "limit": 10},
                    )
                except ValueError as error:
                    self.logger.error(
                        f"Facebook Page {page_id} poll failed: {error}",
                        guild_id=guild_id,
                    )
                    continue
                rows = [row for row in body.get("data", ()) if isinstance(row, dict) and row.get("id")]
                if key not in self.state:
                    self.state[key] = str(rows[0]["id"]) if rows else ""
                    changed = True
                    continue
                previous = self.state[key]
                pending = []
                for row in rows:
                    if str(row["id"]) == previous:
                        break
                    pending.append(row)
                for row in reversed(pending):
                    message = str(row.get("message") or "New Facebook Page post")
                    url = str(row.get("permalink_url") or page.get("url") or "")
                    content = f"{message}\n{url}".strip()
                    await self.discord.send(
                        session,
                        destination,
                        content[:2000],
                        title=f"New post from {page.get('name') or page_id}",
                    )
                if rows and self.state.get(key) != str(rows[0]["id"]):
                    self.state[key] = str(rows[0]["id"])
                    changed = True
        for stale in set(self.state) - active:
            self.state.pop(stale, None)
            changed = True
        if changed:
            self._save()

    async def run_forever(self):
        import aiohttp

        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
            while True:
                try:
                    await self.poll_once(session)
                except asyncio.CancelledError:
                    raise
                except Exception as error:
                    self.logger.error(f"Facebook Page monitoring failed: {error}")
                await asyncio.sleep(self.poll_seconds)
