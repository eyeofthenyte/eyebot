"""HTTPS-facing OAuth callback and signed webhook gateway."""

from __future__ import annotations

import os
import time

from services.liveNotificationService import load_platform_runtime
from services.accountDiscoveryService import discover_oauth_account
from services.logService import LogService
from services.oauthService import OAuthService
from services.oauthStateService import OAuthStateService, resolve_oauth_state_key
from services.platformConnectionService import PlatformConnectionService
from services.webhookService import WebhookService


def create_app(config=None, platform_service=None):
    from aiohttp import web

    if config is None or platform_service is None:
        config, platform_service = load_platform_runtime("gateway")
    logger = LogService("gateway", config["logging"])
    gateway = config.get("gateway", {})
    state_key = resolve_oauth_state_key()
    public_url = str(gateway.get("public_base_url") or "")
    states = OAuthStateService(state_key)
    oauth = OAuthService(config, platform_service, states, public_url)
    connections = PlatformConnectionService(platform_service)
    webhooks = WebhookService(config, platform_service, logger)

    request_windows = {}

    @web.middleware
    async def safe_errors(request, handler):
        try:
            address = request.remote or "unknown"
            now = time.monotonic()
            window = [seen for seen in request_windows.get(address, ()) if now - seen < 60]
            if len(window) >= 60:
                raise web.HTTPTooManyRequests(text="Gateway request limit exceeded.")
            window.append(now)
            request_windows[address] = window
            return await handler(request)
        except web.HTTPException:
            raise
        except (KeyError, TypeError, ValueError) as error:
            logger.warning(f"Rejected gateway request: {error}")
            raise web.HTTPBadRequest(text=str(error))

    app = web.Application(
        client_max_size=1_048_576,
        middlewares=[safe_errors],
    )

    async def health(request):
        return web.json_response({"status": "ok"})

    async def oauth_start(request):
        platform = request.match_info["platform"].casefold()
        start = states.verify_start_request(request.query.get("request", ""))
        if platform != start["platform"]:
            raise web.HTTPBadRequest(text="OAuth platform mismatch.")
        url = oauth.authorization_url(
            start["guild_id"], platform, start["moderator_id"]
        )
        raise web.HTTPFound(url)

    async def oauth_callback(request):
        platform = request.match_info["platform"].casefold()
        if request.query.get("error"):
            raise web.HTTPBadRequest(text="Authorization was denied.")
        code = request.query.get("code", "")
        state_token = request.query.get("state", "")
        state, token_response = await oauth.exchange_callback(
            platform, code, state_token, request.app["client_session"]
        )
        token_response = await discover_oauth_account(
            platform,
            state.guild_id,
            token_response,
            platform_service,
            request.app["client_session"],
        )
        connections.save_token_response(state.guild_id, platform, token_response)
        return web.Response(text="EyeBot connection saved. You may close this window.")

    async def meta_verify(request):
        result = await webhooks.meta_challenge(
            request.match_info["guild_id"],
            request.match_info["platform"],
            request.query,
        )
        return web.Response(text=result)

    async def meta_event(request):
        raw = await request.read()
        await webhooks.handle_meta(
            request.match_info["guild_id"],
            request.match_info["platform"],
            raw,
            request.headers.get("X-Hub-Signature-256", ""),
            request.app["client_session"],
        )
        return web.Response(text="EVENT_RECEIVED")

    async def kofi_event(request):
        await webhooks.handle_kofi(
            request.match_info["guild_id"],
            await request.post(),
            request.app["client_session"],
        )
        return web.Response(text="ok")

    async def start_session(app):
        import aiohttp

        app["client_session"] = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30)
        )

    async def close_session(app):
        await app["client_session"].close()

    app.on_startup.append(start_session)
    app.on_cleanup.append(close_session)
    app.router.add_get("/health", health)
    app.router.add_get("/oauth/{platform}/start", oauth_start)
    app.router.add_get("/oauth/{platform}/callback", oauth_callback)
    app.router.add_get("/webhooks/{platform:facebook|instagram}/{guild_id}", meta_verify)
    app.router.add_post("/webhooks/{platform:facebook|instagram}/{guild_id}", meta_event)
    app.router.add_post("/webhooks/kofi/{guild_id}", kofi_event)
    return app


def main():
    from aiohttp import web

    config, platforms = load_platform_runtime("gateway")
    gateway = config.get("gateway", {})
    if gateway.get("enabled") is not True:
        return 0
    web.run_app(
        create_app(config, platforms),
        host=str(gateway.get("host") or "127.0.0.1"),
        port=int(gateway.get("port") or 8080),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
