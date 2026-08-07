from __future__ import annotations

from core.cog_registry import build_portable_router


class PortableCogHost:
    """Minimal host for running portable cog callbacks outside Discord."""

    def __init__(self, *, config, logger):
        self.config = config
        self.logger = logger
        self.cogs = {}
        self.guilds = ()
        self.google_sheets = None

    def add_cog(self, cog):
        self.cogs[type(cog).__name__] = cog

    def get_command(self, name):
        normalized = name.strip().casefold()
        for cog in self.cogs.values():
            for command in cog.get_commands():
                names = (command.name, *command.aliases)
                if normalized in (item.casefold() for item in names):
                    return command
        return None

    async def wait_until_ready(self):
        return None


def build_portable_runtime(*, config, logger):
    """Create the shared cog router without constructing a Discord bot."""
    from cogs.carousing import Carousing
    from cogs.components import Components
    from cogs.gems import Gems
    from cogs.help import Help
    from cogs.hoard import Hoard
    from cogs.loot import Loot
    from cogs.namegen import NameGen
    from cogs.oracle import Oracle
    from cogs.roller import Roll, load_config
    from cogs.trinket import Trinket
    from cogs.wildmagic import WildMagic

    host = PortableCogHost(config=config, logger=logger)
    for cog_type in (
        Carousing,
        Components,
        Gems,
        Help,
        Hoard,
        Loot,
        NameGen,
        Oracle,
        Trinket,
        WildMagic,
    ):
        host.add_cog(cog_type(host))

    # Roll.__init__ schedules Discord guild initialization. The portable host
    # needs the parser/roller state but intentionally has no guild lifecycle.
    roller = Roll.__new__(Roll)
    roller.bot = host
    roller.platform_config_service = None
    roller.config = load_config()
    host.add_cog(roller)

    return host, build_portable_router(host.cogs, strict=True)
