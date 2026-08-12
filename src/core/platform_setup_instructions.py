"""Markdown setup guides for EyeBot platform connectors."""

from __future__ import annotations


PLATFORM_ORDER = (
    "discord",
    "twitch",
    "youtube",
    "facebook",
    "kick",
    "twitter",
    "bluesky",
    "tiktok",
    "instagram",
    "substack",
    "kofi",
)


COMMON_WARNING = """## Security warning
- Never paste a token, password, client secret, authorization code, cookie, or callback URL into Discord.
- Run secret commands in the EyeBot host terminal. The prompt hides the value and asks for confirmation.
- Use `--guild {guild_id}` for this server. Omit it only when intentionally setting a global fallback.
- Rotate any credential that has appeared in chat, logs, screenshots, Git, YAML, or shell history.
"""


PLATFORM_GUIDES = {
    "discord": """# Discord setup
**Connector status:** Implemented.

1. Open the [Discord Developer Portal](https://discord.com/developers/applications) and create or select the EyeBot application.
2. On **Bot**, create/reset the bot token and enable **Message Content Intent** and **Server Members Intent**.
3. On **Installation**, generate a guild-install link with the `bot` scope and the permissions documented in EyeBot's README. Administrator is not required.
4. Store the token on the EyeBot host:
   `docker compose run --rm --no-deps eyebot python src/manage_secrets.py set discord bot_token --guild {guild_id}`
5. Keep `discord.bot_token` blank in `platforms.yaml`; set `discord.enabled: true` globally.
6. Recreate the container and confirm the bot becomes online.

References: [Discord applications](https://discord.com/developers/applications) · [Discord permissions](https://docs.discord.com/developers/topics/permissions) · [Gateway intents](https://docs.discord.com/developers/events/gateway)
""",
    "twitch": """# Twitch setup
**Connector status:** Implemented for chat commands through TwitchIO 2.10.

1. Open the [Twitch Developer Console](https://dev.twitch.tv/console/apps), register an application, enable 2FA, and configure an exact OAuth redirect URI.
2. Generate a **user access token** for the bot Twitch account with `chat:read` and `chat:edit`. Do not use an app access token, ID token, refresh token, or client secret as `tmi_token`.
3. Validate that the token's login matches the intended bot account and that its Client ID matches the application.
4. Store both values as global secrets on the EyeBot host. One Twitch process uses one bot identity for every joined channel:
   `docker compose run --rm --no-deps eyebot python src/manage_secrets.py set twitch tmi_token`
   `docker compose run --rm --no-deps eyebot python src/manage_secrets.py set twitch client_id`
5. For a private installation, set connector-wide `nick` and `channels` in `platforms.yaml`.
6. For a shared installation, the host must set `private_install: false` in `config.yaml`; then add this server's Twitch channels with `!platform twitch channel add <channel_login> [<#destination>]`. If destination is omitted, the guild's Twitch `destination_channel` is used for live alerts. Use `channel remove <channel_login>` or `channel list` to manage the guild-owned list. The legacy `set channel` command remains compatible.
7. Select the Discord channel for Twitch go-live posts with `!platform twitch set destination_channel <#channel>`. EyeBot polls the official Helix Get Streams endpoint and posts once when a new stream becomes live.
8. The host must also set connector-wide `twitch.enabled: true` in `platforms.yaml`. Enable this guild with `!platform twitch enable`, then restart the Twitch child so it joins the newly configured channel. The shared bot account must be permitted to join and speak in that Twitch channel.

References: [Register a Twitch app](https://dev.twitch.tv/docs/authentication/register-app) · [OAuth tokens](https://dev.twitch.tv/docs/authentication/getting-tokens-oauth/) · [Validate tokens](https://dev.twitch.tv/docs/authentication/validate-tokens)
""",
    "youtube": """# YouTube setup
**Connector status:** Live-event detection, Discord alerts, and YouTube live-chat API methods are implemented. Continuous live-chat command polling still requires an approved live broadcast and runtime activation.

1. Open [Google Cloud Console](https://console.cloud.google.com/), create/select a project, and enable the [YouTube Data API v3](https://console.cloud.google.com/marketplace/product/google/youtube.googleapis.com).
2. Configure the OAuth consent screen and create OAuth client credentials. YouTube user operations require OAuth; service accounts are not supported for YouTube channels.
3. Request only the scopes needed for livestream chat and selected features.
4. Store only the application values on the EyeBot host; the gateway obtains guild access/refresh tokens:
   `docker compose run --rm --no-deps eyebot python src/manage_secrets.py set youtube api_key --guild {guild_id}`
   `docker compose run --rm --no-deps eyebot python src/manage_secrets.py set youtube client_id --guild {guild_id}`
   `docker compose run --rm --no-deps eyebot python src/manage_secrets.py set youtube client_secret --guild {guild_id}`
5. Set the source and Discord destination with `!platform youtube set channel_id <UC...>` and `!platform youtube set destination_channel <#channel>`.
6. Enable the OAuth gateway, register its exact callback, then run `!platform youtube connect` from the mod channel. Enable the platform after authorization. EyeBot polls `search.list` for active broadcasts; the default 900-second interval limits quota consumption.

References: [YouTube authentication](https://developers.google.com/youtube/v3/guides/authentication) · [Live Streaming API](https://developers.google.com/youtube/v3/live/getting-started) · [Google credentials](https://console.cloud.google.com/apis/credentials)
""",
    "facebook": """# Facebook setup
**Connector status:** Live-event detection, Discord alerts, signed webhook intake, and queued Page posting are implemented. Live-comment command routing remains unavailable.

1. Open [Meta for Developers](https://developers.facebook.com/apps/), create an app, and add the required Facebook Login/Graph API products.
2. Configure valid OAuth redirect URIs, app domains, privacy policy, and requested permissions. Page features may require Meta App Review.
3. Obtain the App ID and App Secret. The gateway obtains the user token, resolves the configured Page, and stores its Page token.
4. Store the application values on the EyeBot host:
   `docker compose run --rm --no-deps eyebot python src/manage_secrets.py set facebook app_id --guild {guild_id}`
   `docker compose run --rm --no-deps eyebot python src/manage_secrets.py set facebook app_secret --guild {guild_id}`
5. Set `page_id` and `destination_channel` with `!platform facebook set ...`.
6. Enable the OAuth gateway, register the callback/webhook URLs, and run `!platform facebook connect`. Enable only after Meta grants the requested Page permissions.
7. When `!platform facebook enable` prompts, create or select the private social-media source channel. Attach one to four images there (or reply to an image message) and run `!socialmedia facebook [caption]`.
8. To monitor ordinary posts from another accessible Page, use `!platform facebook page add <page_url> [<#destination>]`. When destination is omitted, the configured Facebook `destination_channel` is used. Manage entries with `page list` and `page remove <url|page_id>`.

References: [Meta apps](https://developers.facebook.com/apps/) · [Facebook Login](https://developers.facebook.com/documentation/facebook-login) · [Access tokens](https://developers.facebook.com/documentation/facebook-login/guides/access-tokens) · [Graph API](https://developers.facebook.com/docs/graph-api/get-started/)
""",
    "kick": """# Kick setup
**Connector status:** Live-event detection and Discord go-live posting are implemented; chat transport remains a placeholder.

1. Sign in to [Kick](https://kick.com/), open account settings, and use the **Developer** tab to create an application.
2. Review [Kick Dev](https://dev.kick.com/) and the [Kick developer documentation](https://docs.kick.com/) for current OAuth endpoints, redirect URI rules, scopes, and app approval requirements.
3. Select only the permissions needed for the enabled capabilities.
4. Store the application values on the EyeBot host; the gateway obtains guild tokens:
   `docker compose run --rm --no-deps eyebot python src/manage_secrets.py set kick client_id --guild {guild_id}`
   `docker compose run --rm --no-deps eyebot python src/manage_secrets.py set kick client_secret --guild {guild_id}`
5. Set the source and destination with `!platform kick set channel <channel_name>` and `!platform kick set destination_channel <#channel>`.
6. Enable after the application has access to Kick's public channels endpoint.
7. Add multiple public Kick channels with `!platform kick channel add <channel_name> [<#destination>]`; manage them with `channel list` and `channel remove <channel_name>`. Each channel may route go-live alerts separately.

References: [Kick Dev](https://dev.kick.com/) · [Kick documentation](https://docs.kick.com/) · [Kick developer settings](https://kick.com/settings/developer)
""",
    "twitter": """# Twitter/X setup
**Connector status:** X Spaces live detection, Discord alerts, OAuth, and queued text posting are implemented.

1. Open the [X Developer Platform](https://developer.x.com/) and create a project/application in the Developer Console.
2. Select an access tier that permits the required posting operations and configure OAuth user authentication.
3. Create an OAuth 2 client for per-guild posting and obtain a Bearer Token for Spaces lookup when required by the selected tier.
4. Store `client_id`, `client_secret`, and applicable Bearer Token on the host. The gateway obtains the guild access/refresh tokens.
5. Set the creator's numeric X user ID and Discord destination with `!platform twitter set user_id <id>` and `!platform twitter set destination_channel <#channel>`.
6. Enable the OAuth gateway, run `!platform twitter connect`, then enable `posting_enabled` after the application tier permits posting and Spaces lookup.
7. When `!platform twitter enable` prompts, create or select the private social-media source channel. Attach one to four images there (or reply to an image message) and run `!socialmedia twitter [caption]`.
8. Monitor posts from another public X account with `!platform twitter account add <username|profile_url> [<#destination>]`. Use `account list` and `account remove <username|profile_url>` to manage sources. Replies and reposts are excluded. Timeline reads use X API credits and may incur charges.

References: [X Developer Console](https://developer.x.com/) · [Authentication overview](https://docs.x.com/fundamentals/authentication/overview) · [API key and secret](https://docs.x.com/fundamentals/authentication/oauth-1-0a/api-key-and-secret)
""",
    "bluesky": """# Bluesky setup
**Connector status:** Per-guild app-password authentication and queued text posting are implemented.

1. Create or select a Bluesky account and identify its full handle, such as `name.bsky.social`.
2. Create a dedicated app password in Bluesky account settings; do not use the account's primary password.
3. Store the app password on the EyeBot host:
   `docker compose run --rm --no-deps eyebot python src/manage_secrets.py set bluesky app_password --guild {guild_id}`
4. Set the handle with `!platform bluesky set handle <handle>`.
5. Enable `posting_enabled`, then use `!socialpost bluesky <text>` from the guild mod channel.
6. When `!platform bluesky enable` prompts, create or select the private social-media source channel. Attach one to four images there (or reply to an image message) and run `!socialmedia bluesky [caption]`.
7. Monitor any accessible public Bluesky account with `!platform bluesky account add <handle|profile_url> [<#destination>]`. Use `account list` and `account remove <handle|profile_url>` to manage sources. Replies and repost feed reasons are excluded.

References: [Bluesky API introduction](https://docs.bsky.app/docs/get-started) · [Posting guide](https://docs.bsky.app/blog/create-post) · [Bluesky account settings](https://bsky.app/settings/app-passwords)
""",
    "tiktok": """# TikTok setup
**Connector status:** Approved OAuth Content Posting and durable media jobs are implemented. General LIVE-status and live-chat APIs remain unavailable.

1. Open [TikTok for Developers](https://developers.tiktok.com/), register an app, and add the appropriate Login Kit or Content Posting products.
2. Configure an approved redirect URI and request only approved scopes. TikTok may require application review before production access.
3. Obtain the Client Key and Client Secret; the gateway performs user authorization and encrypted token storage.
4. Store the application values on the EyeBot host:
   `docker compose run --rm --no-deps eyebot python src/manage_secrets.py set tiktok client_key --guild {guild_id}`
   `docker compose run --rm --no-deps eyebot python src/manage_secrets.py set tiktok client_secret --guild {guild_id}`
5. You may store a future Discord route with `!platform tiktok set destination_channel <#channel>`.
6. Enable the OAuth gateway and run `!platform tiktok connect`. After TikTok approval, queue HTTPS-hosted videos with `!socialurl tiktok <url> [caption]`. TikTok's supported public products do not currently expose creator LIVE status, so EyeBot does not scrape it.
7. After TikTok approves `video.list` and the connected creator reauthorizes it, enable `videos_enabled` to deliver that connected account's new public videos to `destination_channel`. TikTok does not permit URL-only monitoring of arbitrary accounts through Display API.

References: [TikTok Developer Portal](https://developers.tiktok.com/) · [Login Kit for Web](https://developers.tiktok.com/doc/login-kit-web/) · [Token management](https://developers.tiktok.com/doc/login-kit-manage-user-access-tokens/)
""",
    "instagram": """# Instagram setup
**Connector status:** Instagram Live detection, Discord alerts, Meta OAuth, signed webhooks, and queued image posting are implemented for eligible professional accounts.

1. Create a Meta app in [Meta for Developers](https://developers.facebook.com/apps/) and add the appropriate Instagram API product.
2. Connect an eligible Instagram professional account and configure Facebook/Instagram permissions, redirect URIs, and App Review requirements.
3. Obtain the App ID and App Secret. The gateway resolves the configured professional account after authorization.
4. Store the application values on the EyeBot host:
   `docker compose run --rm --no-deps eyebot python src/manage_secrets.py set instagram app_id --guild {guild_id}`
   `docker compose run --rm --no-deps eyebot python src/manage_secrets.py set instagram app_secret --guild {guild_id}`
5. Set `account_id` and `destination_channel` with `!platform instagram set ...`.
6. Enable the OAuth gateway and run `!platform instagram connect`. After Meta approval, queue public HTTPS images with `!socialurl instagram <url> [caption]`.
7. Monitor another professional account available through Business Discovery with `!platform instagram account add <username|profile_url> [<#destination>]`. Use `account list` and `account remove <username|profile_url>` to manage it. Personal and private accounts are not supported.

References: [Meta apps](https://developers.facebook.com/apps/) · [Instagram Platform](https://developers.facebook.com/docs/instagram-platform/) · [Instagram API setup](https://developers.facebook.com/docs/instagram-platform/get-started/)
""",
    "substack": """# Substack setup
**Connector status:** Public RSS newsletter and podcast polling with per-guild Discord delivery is implemented. Authenticated/private publication access is not used.

1. Set the public publication URL with `!platform substack set publication_url https://name.substack.com`.
   Multiple public publications can instead be added with `!platform substack publication add <url> [<#destination>]` and managed with `publication list` or `publication remove <url>`.
2. Set the Discord destination and newsletter/podcast toggles with `!platform substack set ...`.
3. If authenticated access is required, store only the allowed `email` and `credential` values through the EyeBot host:
   `docker compose run --rm --no-deps eyebot python src/manage_secrets.py set substack email --guild {guild_id}`
   `docker compose run --rm --no-deps eyebot python src/manage_secrets.py set substack credential --guild {guild_id}`
4. Do not paste browser cookies into Discord. Confirm that any authenticated method complies with Substack's current terms.
5. Enable the connector. EyeBot polls the public feed every five minutes and persists the last delivered item.

References: [Substack](https://substack.com/) · [Substack Developer API](https://support.substack.com/hc/en-us/articles/45099095296916-Substack-Developer-API) · [API terms](https://substack.com/api-tos) · [Pinned unofficial client](https://github.com/NHagar/substack_api)
""",
    "kofi": """# Ko-fi setup
**Connector status:** Signed/verified webhook routing for donations, memberships, and shop orders is implemented through the HTTPS gateway.

1. Open [Ko-fi](https://ko-fi.com/), configure the creator account, and review webhook/API options in account settings.
2. Create or copy the Ko-fi verification token and configure the webhook target only after EyeBot exposes a public HTTPS webhook endpoint.
3. Store the verification token on the EyeBot host:
   `docker compose run --rm --no-deps eyebot python src/manage_secrets.py set kofi verification_token --guild {guild_id}`
4. Set `page_url`, `destination_channel`, and donation/membership/shop/webhook toggles with `!platform kofi set ...`.
5. Enable the gateway and Ko-fi connector, then set the webhook URL to `https://<host>/webhooks/kofi/{guild_id}`.

References: [Ko-fi](https://ko-fi.com/) · [Ko-fi webhooks](https://ko-fi.com/manage/webhooks) · [Ko-fi API documentation](https://help.ko-fi.com/hc/en-us/articles/360004162298-Does-Ko-fi-have-an-API-or-webhooks)
""",
}


def render_setup_instructions(platform_name: str, guild_id: str | int) -> str:
    """Return one platform guide with the shared security warning."""
    guide = PLATFORM_GUIDES[platform_name].format(guild_id=guild_id).strip()
    warning = COMMON_WARNING.format(guild_id=guild_id).strip()
    return f"{guide}\n\n{warning}"


def split_markdown_messages(text: str, *, limit: int = 1900) -> tuple[str, ...]:
    """Split Markdown at line boundaries without exceeding Discord limits."""
    pages = []
    page = ""
    for line in text.splitlines():
        candidate = f"{page}\n{line}" if page else line
        if len(candidate) > limit and page:
            pages.append(page)
            page = line
        else:
            page = candidate
    if page:
        pages.append(page)
    return tuple(pages)
