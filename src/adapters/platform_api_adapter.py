"""Common contracts and bounded HTTP handling for social API adapters."""

from __future__ import annotations

from dataclasses import dataclass

from core.command_model import CommandPlatform


class PlatformCapabilityError(RuntimeError):
    pass


@dataclass(frozen=True)
class PlatformApiAdapter:
    platform: CommandPlatform
    capabilities: tuple[str, ...]
    implemented: bool = True

    def require(self, capability: str) -> None:
        if capability not in self.capabilities:
            raise PlatformCapabilityError(
                f"{self.platform.value} does not implement {capability}"
            )


async def json_request(session, method, url, *, expected=(200,), **kwargs):
    async with session.request(method, url, **kwargs) as response:
        body = await response.json(content_type=None)
        if response.status not in expected:
            detail = body.get("error") if isinstance(body, dict) else body
            raise RuntimeError(f"Platform API HTTP {response.status}: {detail}")
        return body
