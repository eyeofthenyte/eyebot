"""OAuth provider contracts for guild-scoped social connections."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class OAuthProvider:
    name: str
    authorize_url: str
    token_url: str
    client_id_parameter: str
    client_secret_parameter: str
    default_scopes: tuple[str, ...]
    uses_pkce: bool = True
    authorize_client_field: str = "client_id"
    token_client_field: str = "client_id"

    # Confidential OAuth clients such as X authenticate to the token
    # endpoint with HTTP Basic authentication instead of putting the
    # client secret in the form body.
    uses_basic_token_auth: bool = False


OAUTH_PROVIDERS = {
    "youtube": OAuthProvider(
        "youtube",
        "https://accounts.google.com/o/oauth2/v2/auth",
        "https://oauth2.googleapis.com/token",
        "client_id",
        "client_secret",
        (
            "https://www.googleapis.com/auth/youtube.readonly",
            "https://www.googleapis.com/auth/youtube.force-ssl",
        ),
    ),
    "facebook": OAuthProvider(
        "facebook",
        "https://www.facebook.com/v26.0/dialog/oauth",
        "https://graph.facebook.com/v26.0/oauth/access_token",
        "app_id",
        "app_secret",
        ("pages_show_list", "pages_read_engagement", "pages_manage_posts"),
        uses_pkce=False,
    ),
    "instagram": OAuthProvider(
        "instagram",
        "https://www.facebook.com/v26.0/dialog/oauth",
        "https://graph.facebook.com/v26.0/oauth/access_token",
        "app_id",
        "app_secret",
        (
            "instagram_basic",
            "instagram_content_publish",
            "pages_show_list",
        ),
        uses_pkce=False,
    ),
    "kick": OAuthProvider(
        "kick",
        "https://id.kick.com/oauth/authorize",
        "https://id.kick.com/oauth/token",
        "client_id",
        "client_secret",
        ("user:read", "channel:read", "chat:write"),
    ),
	"twitter": OAuthProvider(
		"twitter",
		"https://x.com/i/oauth2/authorize",
		"https://api.x.com/2/oauth2/token",
		"client_id",
		"client_secret",
		(
			"tweet.read",
			"tweet.write",
			"users.read",
			"media.write",
			"offline.access",
		),
		uses_basic_token_auth=True,
	),
    "tiktok": OAuthProvider(
        "tiktok",
        "https://www.tiktok.com/v2/auth/authorize/",
        "https://open.tiktokapis.com/v2/oauth/token/",
        "client_key",
        "client_secret",
        ("user.info.basic", "video.list", "video.publish"),
        authorize_client_field="client_key",
        token_client_field="client_key",
    ),
}


def get_oauth_provider(platform: str) -> OAuthProvider:
    try:
        return OAUTH_PROVIDERS[platform.strip().casefold()]
    except KeyError as error:
        raise ValueError(f"OAuth is not configured for platform: {platform}") from error
