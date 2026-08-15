"""HTTPS-facing OAuth callback and signed webhook gateway."""

from __future__ import annotations

import asyncio
import os
import time

from services.liveNotificationService import load_platform_runtime
from services.accountDiscoveryService import discover_oauth_account
from services.logService import LogService
from services.oauthService import OAuthService
from services.oauthStateService import OAuthStateService, resolve_oauth_state_key
from services.platformConnectionService import PlatformConnectionService
from services.publicMediaService import PublicMediaService
from services.webhookService import WebhookService
from services.kickWebhookService import (
    KickWebhookAuthenticationError,
    KickWebhookDuplicateError,
    KickWebhookError,
    KickWebhookService,
)
from core.portable_runtime import build_portable_runtime
from services.kickCommandService import KickCommandService
from services.kickSubscriptionService import KickSubscriptionService


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
    kick_webhooks = KickWebhookService(
        platform_service.guild_config_dir.parent / "webhooks" / "kick-events.json"
    )
    _command_host, command_router = build_portable_runtime(
        config=config,
        logger=logger,
    )
    kick_commands = KickCommandService(
        config, platform_service, command_router, kick_webhooks, logger
    )
    kick_subscriptions = KickSubscriptionService(platform_service, logger)
    public_media = PublicMediaService(config, platform_service.guild_config_dir)

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
        return web.json_response(
            {
                "status": "ok",
                "public_media": "enabled" if public_media.enabled else "disabled",
            }
        )

    async def webhook_status(request):
        return web.json_response(
            {
                "service": "EyeBot webhook gateway",
                "status": "available",
                "platforms": ["facebook", "instagram", "kick", "kofi"],
            }
        )

    async def serve_public_media(request):
        if not public_media.enabled:
            raise web.HTTPNotFound()
        try:
            path = public_media.resolve(
                request.match_info["guild_id"],
                request.match_info["batch"],
                request.match_info["filename"],
            )
        except (FileNotFoundError, ValueError):
            raise web.HTTPNotFound() from None
        return web.FileResponse(
            path,
            headers={
                "Cache-Control": "public, max-age=3600",
                "X-Content-Type-Options": "nosniff",
                "Content-Security-Policy": "default-src 'none'; sandbox",
            },
        )

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
        if platform == "kick":
            kick_settings = platform_service.effective_guild_platform(
                state.guild_id, "kick"
            )
            if kick_settings.get("livestream_chat_commands_enabled") is True:
                await kick_subscriptions.ensure_chat(
                    state.guild_id, request.app["client_session"]
                )
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

    async def kick_event(request):
        raw_body = await request.read()
        event = None
        try:
            event = kick_webhooks.authenticate(raw_body, request.headers)
            kick_webhooks.claim(event)
            outcome = await kick_commands.handle(
                event, request.headers, request.app["client_session"]
            )
            kick_webhooks.remember(event)
        except KickWebhookDuplicateError as error:
            # Kick retries deliveries. Previously accepted message IDs are
            # acknowledged without executing them again.
            return web.Response(status=204)
        except KickWebhookAuthenticationError as error:
            raise web.HTTPUnauthorized(text=str(error)) from error
        except KickWebhookError as error:
            raise web.HTTPBadRequest(text=str(error)) from error
        except Exception:
            if event is not None:
                kick_webhooks.release(event.message_id)
            raise
        logger.info(
            f"Accepted Kick webhook {event.event_type} message "
            f"{event.message_id} ({outcome})"
        )
        return web.Response(status=204)

    async def start_session(app):
        import aiohttp

        app["client_session"] = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30)
        )
        if _command_host.google_sheets is not None:
            await _command_host.google_sheets.start()
        try:
            await kick_webhooks.refresh_public_key(app["client_session"])
        except Exception as error:
            logger.warning(
                f"Unable to refresh Kick webhook public key; using bundled key: {error}"
            )
        app["kick_subscription_task"] = asyncio.create_task(
            kick_subscriptions.run_forever(app["client_session"])
        )

    async def close_session(app):
        task = app.get("kick_subscription_task")
        if task is not None:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        if _command_host.google_sheets is not None:
            await _command_host.google_sheets.close()
        await app["client_session"].close()

    async def public_media_cleanup(app):
        if not public_media.enabled:
            yield
            return
        public_media.cleanup_expired()
        task = asyncio.create_task(public_media.cleanup_forever())
        app["public_media_cleanup_task"] = task
        try:
            yield
        finally:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

    app.on_startup.append(start_session)
    app.on_cleanup.append(close_session)
    app.cleanup_ctx.append(public_media_cleanup)
    app.router.add_get("/health", health)
    app.router.add_get("/webhooks", webhook_status)
    app.router.add_get(
        "/media/{guild_id}/{batch}/{filename}",
        serve_public_media,
    )
    app.router.add_get("/oauth/{platform}/start", oauth_start)
    app.router.add_get("/oauth/{platform}/callback", oauth_callback)
    app.router.add_get("/webhooks/{platform:facebook|instagram}/{guild_id}", meta_verify)
    app.router.add_post("/webhooks/{platform:facebook|instagram}/{guild_id}", meta_event)
    app.router.add_post("/webhooks/kofi/{guild_id}", kofi_event)
    app.router.add_post("/webhooks/kick", kick_event)
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
