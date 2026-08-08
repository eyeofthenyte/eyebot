"""Generate per-guild authorization URLs and exchange OAuth codes."""

from __future__ import annotations

from urllib.parse import urlencode

from aiohttp import BasicAuth

from core.oauth_provider import get_oauth_provider
from services.oauthStateService import OAuthStateService


class OAuthService:
    def __init__(
        self,
        config,
        platform_service,
        state_service: OAuthStateService,
        public_base_url: str,
    ):
        self.config = config
        self.platform_service = platform_service
        self.state_service = state_service
        self.public_base_url = public_base_url.rstrip("/")
        if not self.public_base_url.startswith("https://"):
            raise ValueError("OAuth public base URL must use HTTPS")

    def redirect_uri(self, platform: str) -> str:
        return f"{self.public_base_url}/oauth/{platform}/callback"

    def authorization_url(self, guild_id, platform, moderator_id) -> str:
        provider = get_oauth_provider(platform)
        settings = self.platform_service.effective_guild_platform(guild_id, platform)
        client_id = settings.get(provider.client_id_parameter)
        if not client_id:
            raise ValueError(
                f"Missing {platform}.{provider.client_id_parameter} client credential"
            )
        state_token, state = self.state_service.issue(
            str(guild_id), platform, str(moderator_id)
        )
        parameters = {
            provider.authorize_client_field: client_id,
            "redirect_uri": self.redirect_uri(platform),
            "response_type": "code",
            "scope": " ".join(provider.default_scopes),
            "state": state_token,
        }
        if provider.uses_pkce:
            parameters.update(
                {
                    "code_challenge": self.state_service.code_challenge(state),
                    "code_challenge_method": "S256",
                }
            )
        if platform == "youtube":
            parameters.update({"access_type": "offline", "prompt": "consent"})
        return provider.authorize_url + "?" + urlencode(parameters)

    async def exchange_callback(self, platform, code, state_token, session):
        provider = get_oauth_provider(platform)
        state = self.state_service.consume(state_token)

        if state.platform != platform:
            raise ValueError("OAuth platform does not match signed state")

        settings = self.platform_service.effective_guild_platform(
            state.guild_id,
            platform,
        )
        client_id = settings.get(provider.client_id_parameter)
        client_secret = settings.get(provider.client_secret_parameter)

        if not client_id or not client_secret:
            raise ValueError("OAuth client credentials are not configured")

        payload = {
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": self.redirect_uri(platform),
        }
        request_options = {}

        if getattr(provider, "uses_basic_token_auth", False):
            from aiohttp import BasicAuth

            request_options["auth"] = BasicAuth(client_id, client_secret)
        else:
            payload[provider.token_client_field] = client_id
            payload["client_secret"] = client_secret

        if provider.uses_pkce:
            payload["code_verifier"] = state.code_verifier

        async with session.post(
            provider.token_url,
            data=payload,
            **request_options,
        ) as response:
            body = await response.json(content_type=None)

            if response.status < 200 or response.status >= 300:
                message = (
                    body.get("error_description")
                    or body.get("error")
                    or response.status
                )
                raise ValueError(f"OAuth token exchange failed: {message}")

        return state, body
