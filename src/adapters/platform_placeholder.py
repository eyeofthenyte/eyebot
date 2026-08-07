from __future__ import annotations

from dataclasses import dataclass

from core.command_model import CommandPlatform


@dataclass(frozen=True)
class PlatformAdapterPlaceholder:
    """Describes a future platform integration without enabling it."""

    platform: CommandPlatform
    capabilities: tuple[str, ...]
    implemented: bool = False

    def require_implementation(self):
        raise NotImplementedError(
            f"The {self.platform.value} adapter is a placeholder and is not "
            "implemented yet."
        )
