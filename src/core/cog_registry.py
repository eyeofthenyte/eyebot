from __future__ import annotations

from collections.abc import Mapping

from core.cog_bridge import LegacyCogHandler, PortableCommandSpec
from core.command_router import CommandRouter


PORTABLE_COMMANDS = (
    PortableCommandSpec(
        "Carousing", "_carousing", "carousing",
        ("carouse", "drinking", "getdrinks", "pubcrawl"),
        "optional_joined", "action",
    ),
    PortableCommandSpec(
        "Components", "_collect", "collect",
        ("search", "find", "gather"), "joined", "select",
    ),
    PortableCommandSpec(
        "Components", "_flora", "flora", ("hinfo",), "joined", "select",
    ),
    PortableCommandSpec(
        "Components", "potion", "potion", (), "joined", "select",
    ),
    PortableCommandSpec(
        "Components", "poison", "poison", (), "joined", "select",
    ),
    PortableCommandSpec("Gems", "gems", "gems", (), "joined", "gemstring"),
    PortableCommandSpec("Help", "list_commands", "commands"),
    PortableCommandSpec(
        "Help", "help_command", "help", (), "optional_joined", "command_name",
    ),
    PortableCommandSpec("Hoard", "hoard", "hoard", (), "joined", "select"),
    PortableCommandSpec("Loot", "loot", "loot", (), "joined", "select"),
    PortableCommandSpec("NameGen", "namegen", "namegen", (), "variadic"),
    PortableCommandSpec("Oracle", "oracle", "oracle", (), "joined", "question"),
    PortableCommandSpec(
        "Roll", "roll", "roll", ("r",), "optional_joined", "args", True,
    ),
    PortableCommandSpec(
        "Trinket", "trinket", "trinket", (), "joined", "select",
    ),
    PortableCommandSpec(
        "WildMagic", "_wildmagic", "wildmagic",
        ("wm", "surge"), "joined", "select",
    ),
)


def build_portable_router(
    cogs: Mapping[str, object],
    *,
    strict: bool = True,
) -> CommandRouter:
    """Register every non-platform-specific cog command in one shared router."""
    router = CommandRouter()
    normalized_cogs = {name.casefold(): cog for name, cog in cogs.items()}
    missing = []
    for spec in PORTABLE_COMMANDS:
        cog = normalized_cogs.get(spec.cog_name.casefold())
        if cog is None:
            missing.append(spec.cog_name)
            continue
        router.register(
            spec.command,
            LegacyCogHandler(cog, spec),
            aliases=spec.aliases,
        )
    if strict and missing:
        names = ", ".join(sorted(set(missing)))
        raise RuntimeError(f"Portable command cogs were not loaded: {names}")
    return router
