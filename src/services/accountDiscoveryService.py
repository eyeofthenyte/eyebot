"""Resolve OAuth identities and verify configured guild account ownership."""

from __future__ import annotations


async def _get_json(session, url, *, token, params=None):
    headers = {"Authorization": f"Bearer {token}"}
    async with session.get(url, headers=headers, params=params or {}) as response:
        body = await response.json(content_type=None)
        if not 200 <= response.status < 300:
            raise ValueError(
                f"Account discovery failed: {body.get('error') if isinstance(body, dict) else response.status}"
            )
        return body


async def discover_oauth_account(
    platform,
    guild_id,
    token_response,
    platform_service,
    session,
):
    """Verify the authorized identity and return possibly-updated tokens."""
    token = token_response.get("access_token")
    settings = platform_service.effective_guild_platform(guild_id, platform)
    if platform == "youtube":
        body = await _get_json(
            session,
            "https://www.googleapis.com/youtube/v3/channels",
            token=token,
            params={"part": "id,snippet", "mine": "true"},
        )
        rows = body.get("items", [])
        if not rows:
            raise ValueError("Authorized Google account does not own a YouTube channel")
        row = rows[0]
        configured = settings.get("channel_id")
        if configured and configured != row.get("id"):
            raise ValueError("Authorized YouTube channel does not match configured channel_id")
        platform_service.set_guild_platform_override(guild_id, platform, "channel_id", row["id"])
        platform_service.set_guild_platform_override(
            guild_id, platform, "account_name", row.get("snippet", {}).get("title", "")
        )
    elif platform in {"facebook", "instagram"}:
        body = await _get_json(
            session,
            "https://graph.facebook.com/v26.0/me/accounts",
            token=token,
            params={"fields": "id,name,access_token,instagram_business_account"},
        )
        selected = None
        if platform == "facebook":
            expected = str(settings.get("page_id") or "")
            selected = next((row for row in body.get("data", []) if str(row.get("id")) == expected), None)
        else:
            expected = str(settings.get("account_id") or "")
            selected = next(
                (
                    row
                    for row in body.get("data", [])
                    if str((row.get("instagram_business_account") or {}).get("id")) == expected
                ),
                None,
            )
        if not selected:
            raise ValueError(
                f"Authorized Meta account does not contain configured {platform} account"
            )
        token_response["access_token"] = selected.get("access_token") or token
        platform_service.set_guild_platform_override(
            guild_id, platform, "account_name", selected.get("name", "")
        )
    elif platform == "twitter":
        body = await _get_json(
            session,
            "https://api.x.com/2/users/me",
            token=token,
            params={"user.fields": "id,name,username"},
        )
        account = body.get("data", {})
        expected = str(settings.get("user_id") or "")
        if expected and expected != str(account.get("id") or ""):
            raise ValueError("Authorized X account does not match configured user_id")
        platform_service.set_guild_platform_override(
            guild_id, platform, "user_id", str(account["id"])
        )
        platform_service.set_guild_platform_override(
            guild_id, platform, "account_name", account.get("username", "")
        )
    elif platform == "tiktok":
        body = await _get_json(
            session,
            "https://open.tiktokapis.com/v2/user/info/",
            token=token,
            params={"fields": "open_id,display_name,username"},
        )
        account = body.get("data", {}).get("user", {})
        if not account.get("open_id"):
            raise ValueError("TikTok did not return the authorized account identity")
        platform_service.set_guild_platform_override(
            guild_id, platform, "open_id", str(account["open_id"])
        )
        platform_service.set_guild_platform_override(
            guild_id,
            platform,
            "account_name",
            account.get("username") or account.get("display_name") or "",
        )
    return token_response
