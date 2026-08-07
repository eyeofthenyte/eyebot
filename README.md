# EyeBot

EyeBot is a Python bot framework for tabletop-RPG utilities and shared chat
commands. Discord and Twitch are currently implemented. A platform-neutral
request/response layer allows the same gameplay commands to run through either
transport, while Discord-specific administration remains in Discord cogs.

The overall supervisor starts every enabled platform bot as a separate child
process inside one container. YouTube, Facebook, Kick, Twitter/X, Bluesky,
TikTok, Instagram, Substack, and Ko-fi currently have configuration and
entrypoint placeholders only. Their pinned Python API dependencies are included
in `requirements.txt`; installing them does not make the placeholder adapters
operational until their authentication and transport logic is implemented.

## Contents

- [Features](#features)
- [Platform status](#platform-status)
- [Requirements](#requirements)
- [Discord application setup](#discord-application-setup)
- [Installation with Docker Compose](#installation-with-docker-compose)
- [Local installation](#local-installation)
- [Encrypted platform secrets](#encrypted-platform-secrets)
- [Configuration reference](#configuration-reference)
- [Google Sheets setup](#google-sheets-setup)
- [Permissions](#permissions)
- [Running and operating EyeBot](#running-and-operating-eyebot)
- [Command guide](#command-guide)
- [Dice syntax and limits](#dice-syntax-and-limits)
- [Persistent data](#persistent-data)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)
- [Security](#security)

## Features

- Discord and Twitch transport adapters around a shared command layer.
- One supervisor process for all enabled platform connectors.
- Owner-only platform restart commands from Discord or the container shell.
- Advanced bounded dice parsing, aliases, private rolls, and blind rolls.
- Discord embed-size protection and bounded roll-output pagination.
- Fantasy name generation backed by JavaScript race libraries.
- Loot, treasure-hoard, gem, trinket, herbalism, alchemy, oracle, carousing,
  and wild-magic commands.
- Cached Google Sheets access through one reusable asynchronous service.
- YAML configuration recovery from a dated backup.

## Platform status

| Platform | Config section | Status | Shared chat commands |
| --- | --- | --- | --- |
| Discord | `discord` | Implemented | Yes |
| Twitch | `twitch` | Implemented | Yes |
| YouTube | `youtube` | Placeholder | No |
| Facebook | `facebook` | Placeholder | No |
| Kick | `kick` | Placeholder | No |
| Twitter/X | `twitter` | Placeholder | No |
| Bluesky | `bluesky` | Placeholder | No |
| TikTok | `tiktok` | Placeholder | No |
| Instagram | `instagram` | Placeholder | No |
| Substack | `substack` | Placeholder | No |
| Ko-fi | `kofi` | Placeholder | No |

Leave placeholder platforms disabled. Enabling one starts its placeholder
entrypoint, which exits with a not-implemented error; the supervisor then stops
the other children so the container does not silently run a partial setup.

## Requirements

### Docker installation

- Git
- Docker Engine or Docker Desktop with Docker Compose v2

The image supplies Python 3.11, Node.js, and the pinned Python dependencies.

### Local installation

- Git
- Python 3.11
- Node.js, required by `!namegen`

Pinned Python packages are listed in `requirements.txt`:

| Integration | Packages |
| --- | --- |
| Discord | `discord.py` |
| Twitch | `twitchio` |
| YouTube | `google-api-python-client`, `google-auth-oauthlib` |
| Facebook | `facebook-sdk`, `requests` |
| Kick | `kickapi`, `aiohttp` |
| Twitter/X | `tweepy` |
| Bluesky | `atproto` |
| TikTok | `TikTokApi` |
| Instagram | `instagrapi` |
| Substack | `substack-api`, `feedparser` |
| Ko-fi | `aiohttp` and `requests` for webhook handling |
| Google Sheets | `gspread` |
| Configuration/runtime | `PyYAML`, `typing_extensions` |

Some listed packages are community clients because their platforms do not
provide a maintained general-purpose Python SDK. Pin updates should therefore
be tested against the corresponding adapter before deployment.

## Discord application setup

1. Create an application in the
   [Discord Developer Portal](https://discord.com/developers/applications).
2. Open **Bot**, create the bot user, and copy or reset its token.
3. Under **Privileged Gateway Intents**, enable:
   - **Message Content Intent**
   - **Server Members Intent**
4. Open **OAuth2 > URL Generator**.
5. Select the `bot` scope.
6. Select the permissions appropriate for the commands you intend to use.
   See [Permissions](#permissions).
7. Open the generated URL and invite the bot to the desired server.
8. Store the token with `python src/manage_secrets.py set discord bot_token`.

EyeBot uses prefix commands, not application/slash commands, so the
`applications.commands` scope is not required by the current code.

Never paste a bot token into an issue, log, screenshot, commit, or chat. If a
token has been exposed, reset it in the Developer Portal before starting the
bot again.

## Installation with Docker Compose

Docker Compose is the recommended deployment.

```bash
git clone https://github.com/eyeofthenyte/eyebot.git
cd eyebot
cp config.yaml.dist config.yaml
cp platforms.yaml.dist platforms.yaml
```

PowerShell equivalent:

```powershell
git clone https://github.com/eyeofthenyte/eyebot.git
Set-Location eyebot
Copy-Item config.yaml.dist config.yaml
Copy-Item platforms.yaml.dist platforms.yaml
```

Edit `config.yaml` for global settings and `platforms.yaml` for connector and
non-secret settings. Before Compose reads its secret declaration, install the
pinned dependencies and create the one-time master key:

```bash
python -m pip install --requirement requirements.txt
python src/manage_secrets.py init
```

Build the image, enter the global Discord token through hidden input, and then
start EyeBot:

```bash
docker compose build eyebot
docker compose run --rm eyebot python src/manage_secrets.py set discord bot_token
docker compose up --detach
```

Do not replace `secrets/eyebot_master_key` after encrypted values have been
stored. Back it up separately; without it, the encrypted secret volume cannot
be recovered.

Subsequent builds and starts use:

```bash
docker compose up --detach --build
```

After changing dependencies or when replacing an older image, force a clean
dependency layer:

```bash
docker compose build --no-cache eyebot
docker compose up --detach --force-recreate
```

The Docker build runs `pip check` and imports every required top-level runtime
package, including `yaml` from `PyYAML`. A missing dependency therefore fails
the image build instead of crashing the container at startup.

Follow its logs:

```bash
docker compose logs --follow eyebot
```

Check container state and health:

```bash
docker compose ps
```

Stop EyeBot:

```bash
docker compose down
```

The equivalent Make targets are:

```bash
make build
make start
make logs
make restart
make stop
```

## Local installation

Create and activate a virtual environment:

```bash
git clone https://github.com/eyeofthenyte/eyebot.git
cd eyebot
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install --requirement requirements.txt
cp config.yaml.dist config.yaml
cp platforms.yaml.dist platforms.yaml
```

PowerShell activation and configuration:

```powershell
git clone https://github.com/eyeofthenyte/eyebot.git
Set-Location eyebot
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install --requirement requirements.txt
Copy-Item config.yaml.dist config.yaml
Copy-Item platforms.yaml.dist platforms.yaml
```

Initialize encrypted storage and enter the global Discord token:

```bash
python src/manage_secrets.py init
python src/manage_secrets.py set discord bot_token
```

Edit both YAML files for non-secret configuration, then run all enabled
connectors:

```bash
python src/eyebot.py
```

For connector-specific debugging, run an implemented entrypoint directly:

```bash
python src/eyebot_discord.py
python src/eyebot_twitch.py
```

## Encrypted platform secrets

EyeBot stores secret values as authenticated Fernet ciphertext. One store holds
global defaults and a separate encrypted file is used for each guild that needs
different credentials:

```text
secrets/
└── eyebot_master_key
data/
└── secrets/
    ├── global.secrets
    └── guilds/
        ├── 123456789012345678.secrets
        └── 234567890123456789.secrets
```

The key and ciphertext are deliberately stored separately. Both directories
are excluded from Git and the Docker build context. Secret values are never
displayed by the management tool.

Use the same interface for single-server and multi-server installations. Omit
`--guild` for a global credential or provide a Discord guild ID for an
override:

```bash
# Hidden interactive input and confirmation
python src/manage_secrets.py set youtube client_secret

# One guild overrides the global YouTube secret
python src/manage_secrets.py set youtube client_secret --guild 123456789012345678

# Show stored names only, never values
python src/manage_secrets.py list
python src/manage_secrets.py list --guild 123456789012345678

# Remove one value
python src/manage_secrets.py delete youtube client_secret --guild 123456789012345678
```

For Docker, run the same operations in a one-off Compose container so they use
the `secret-data` volume:

```bash
docker compose run --rm eyebot python src/manage_secrets.py set youtube client_secret
docker compose run --rm eyebot python src/manage_secrets.py set youtube client_secret --guild 123456789012345678
docker compose run --rm eyebot python src/manage_secrets.py list
```

For unattended provisioning, `--value-file /protected/path` reads a value from
a protected file. Never put a secret directly on the command line because it
may be retained in shell history or process listings.

Resolution order is:

1. Guild-specific encrypted secret.
2. Global encrypted secret.
3. Legacy plaintext value in `platforms.yaml`.

The third level exists for migration compatibility only. Move existing
credentials into the encrypted store, blank their `platforms.yaml` values, and
restart EyeBot. Guild secrets affect adapters that request effective guild
configuration; process-level connection credentials, such as the Discord bot
token, must have a global value.

Supported secret parameters:

| Platform | Secret parameters |
| --- | --- |
| Discord | `bot_token` |
| Twitch | `tmi_token`, `client_id` |
| YouTube | `api_key`, `client_id`, `client_secret`, `refresh_token` |
| Facebook | `app_id`, `app_secret`, `access_token` |
| Kick | `client_id`, `client_secret`, `access_token` |
| Twitter/X | `api_key`, `api_secret`, `bearer_token`, `access_token`, `access_token_secret` |
| Bluesky | `app_password` |
| TikTok | `client_key`, `client_secret`, `access_token` |
| Instagram | `app_id`, `app_secret`, `access_token` |
| Substack | `email`, `credential` |
| Ko-fi | `verification_token` |

Direct entrypoints do not provide overall process supervision.

## Configuration reference

Start from `config.yaml.dist` and `platforms.yaml.dist`. YAML indentation
matters, and enable flags must be YAML booleans (`true` or `false`), not quoted
strings.

`config.yaml` contains process-wide settings. `platforms.yaml` contains
platform credentials and connector-wide toggles. Mutable Discord settings are
stored separately in `data/guilds/<guild_id>.yaml`; the runtime presents those
files to existing cogs as one guild mapping.

### Core settings

| Key | Meaning | Default |
| --- | --- | --- |
| `prefix` | Prefix used to recognize commands | `!` |
| `logging.level` | Configured logging level | `DEBUG` |
| `logging.output` | Log filename or `syslog` | `output.log` |

Examples in this guide use `!`. This is also the default for newly discovered
Discord guilds. A server can override it with `!setprefix <prefix>` and return
to the global value with `<current-prefix>setprefix reset`. Discord DMs and
non-Discord platforms continue using the global prefix.

### Discord

In `platforms.yaml`:

```yaml
discord:
  enabled: true
  bot_token:
```

| Key | Required | Meaning |
| --- | --- | --- |
| `discord.enabled` | Yes | Starts or skips the Discord child |
| `discord.bot_token` | Legacy only | Plaintext fallback; prefer the encrypted store |

For backward compatibility, a missing `discord.enabled` value is treated as
enabled. Set it explicitly in new installations.

Mutable server settings are stored in `data/guilds/<guild_id>.yaml`:

```yaml
guild_name: Example Campaign
prefix: "!"
dm_channel: "UNSET"
dm_role: "UNSET"
aliases: {}
user_channels: {}
mod_channel: "UNSET"
timers: {}
```

These entries are normally maintained by `!setprefix`, `!set_dm`, `!alias`,
`!privateroll`, `!setmodchannel`, and `!settimer`; manual editing is optional.
Only numeric Discord snowflake IDs are accepted as filenames.

### Twitch

In `platforms.yaml`:

```yaml
twitch:
  enabled: true
  tmi_token:
  client_id:
  nick: your_bot_name
  channels:
    - your_channel_name
```

| Key | Required | Meaning |
| --- | --- | --- |
| `twitch.enabled` | Yes | Starts or skips the Twitch child |
| `twitch.tmi_token` | Legacy only | Plaintext fallback; prefer the encrypted store |
| `twitch.client_id` | Legacy only | Plaintext fallback; prefer the encrypted store |
| `twitch.nick` | Recommended | Bot account name |
| `twitch.channels` | When enabled | YAML list of channel names to join |

The Twitch entrypoint validates the token and channel list before connecting.
Use the YAML list shown above; do not provide a numeric channel ID.

Twitch supports the shared gameplay commands and the native `!hello`
connectivity check. Discord-only administration is not exposed on Twitch.
Attachments and everything beginning with `| Attachments:` are omitted from
non-Discord command output.

### Google Sheets

In `config.yaml`:

```yaml
google_sheets:
  credentials_file: service_account.json
  cache_ttl: 300
```

| Key | Required | Meaning |
| --- | --- | --- |
| `google_sheets.credentials_file` | For Sheets-backed commands | Path to the service-account JSON |
| `google_sheets.cache_ttl` | No | Worksheet cache lifetime in seconds |

`GOOGLE_SERVICE_ACCOUNT_FILE` can supply the credential path when
`credentials_file` is omitted.

### Placeholder platforms

Every placeholder section defaults to `enabled: false`. Its other blank
credentials and feature toggles document the intended integration contract.
They do not currently create API connections or implement posting:

- YouTube: videos, community posts, and livestream chat commands
- Facebook: publishing and livestream chat commands
- Kick: livestream chat commands
- Twitter/X, Bluesky, TikTok, and Instagram: publishing
- Substack: newsletter and podcast retrieval
- Ko-fi: donation, membership, shop-order, and webhook events

## Google Sheets setup

The `carousing`, `flora`, `potion`, `poison`, and `trinket` commands require
Google Sheets access.

1. Create a Google Cloud project.
2. Enable the Google Sheets API and Google Drive API.
3. Create a service account and download its JSON key.
4. Save the key as `service_account.json` in the project root, or configure a
   different path.
5. Share every required spreadsheet with the service account's email address
   as a viewer.
6. Keep the key outside Git. `service_account.json` is ignored by this
   repository.

The default Compose file does not mount the service-account key. If Sheets
commands are required in Docker, add this read-only bind mount beneath the
existing `eyebot.volumes` list:

```yaml
- type: bind
  source: ./service_account.json
  target: /app/service_account.json
  read_only: true
```

Restart the container after adding or replacing credentials.

## Permissions

### Discord gateway intents

The bot requests:

- Guilds
- Guild messages
- Message content
- Guild members

Message Content and Server Members must also be enabled in the Developer Portal
or Discord may reject the connection or omit required event data.

### Recommended bot permissions

Grant only what the enabled commands need:

| Permission | Used for |
| --- | --- |
| View Channels | Reading command channels and configured destinations |
| Send Messages | All responses |
| Embed Links | Rich command responses |
| Attach Files | Discord command icons and images |
| Read Message History | Reactions, menus, and moderation workflows |
| Add Reactions | Alias confirmation and interactive setup |
| Manage Messages | `clear`/`purge`, platform-command cleanup, invoking-message cleanup, reaction cleanup |
| Manage Channels | Creating DM/mod channels and timer administration |
| Manage Roles | Creating the configured DM role |

If EyeBot creates roles or channels, place its role high enough in the server
role hierarchy to perform those operations. Administrator permission is not
required for normal operation.

### Command caller permissions

| Command | Caller requirement |
| --- | --- |
| `shutdown`, `restart`, `servers`, `load`, `unload`, `reload` | Bot owner |
| `leave` | Server Administrator or bot owner |
| `clear` / `purge` | Manage Messages |
| `setmodchannel` | Manage Server |
| `settimer` | Manage Channels |
| `setprefix` | Manage Server |
| `platform` | Manage Server |
| `set_dm` | Server Administrator or configured DM role |
| `privateroll list` | Manage Messages, Manage Server, or Administrator |
| `privateroll set ... @user` | Manage Messages, Manage Server, or Administrator |
| `alias remove` | Alias creator or Manage Server |

The bot owner is the owner of the Discord application as resolved by
`discord.py`.

## Running and operating EyeBot

### Overall supervisor

`src/eyebot.py` merges `config.yaml` and `platforms.yaml`, then starts one
process per enabled platform. It forwards SIGINT/SIGTERM during shutdown. If an enabled child exits
unexpectedly, the supervisor stops the other children and returns a failure so
Docker's restart policy can recover the container.

The healthcheck confirms that the supervisor process is running.

### Restart one platform

From the running container:

```bash
docker compose exec eyebot python src/eyebot.py restart twitch
docker compose exec eyebot python src/eyebot.py restart discord
```

From Discord as the bot owner:

```text
!restart twitch
!restart discord
```

The supervisor accepts only known, enabled, running platforms. Restarting one
child leaves the others running. Discord sends an acknowledgment before
restarting itself.

The internal control endpoint binds to `127.0.0.1:8765` inside the container.
Override its port for all processes with:

```yaml
environment:
  EYEBOT_PROCESS: src/eyebot.py
  EYEBOT_CONTROL_PORT: "9876"
```

Do not publish this internal control port from Docker.

## Command guide

Commands in [Shared gameplay commands](#shared-gameplay-commands) are registered
in the platform-neutral command layer and are available on Discord and Twitch.
Output formatting differs by platform: Discord supports embeds and files;
Twitch receives flattened, chat-safe text.

Commands in [Discord-only commands](#discord-only-commands) manipulate Discord
state and are intentionally unavailable on other transports.

### Discovering commands

| Command | Description |
| --- | --- |
| `!commands` | List loaded commands grouped by cog |
| `!help` | Show the basic help menu |
| `!help <command>` | Show the command's detailed docstring |

### Shared gameplay commands

| Command | Aliases | Description and example |
| --- | --- | --- |
| `!carousing` | `carouse`, `drinking`, `getdrinks`, `pubcrawl` | Random carousing-table result |
| `!collect <biome>` | `search`, `find`, `gather` | Find an alchemy component; e.g. `!collect forest` |
| `!flora <name>` | `hinfo` | Ingredient information; use `!flora list` for names |
| `!potion <item, item>` | — | Calculate potion difficulty; e.g. `!potion mandrake root, wyrmtongue petals` |
| `!poison <item, item>` | — | Calculate poison difficulty from comma-space-separated ingredients |
| `!gems <gp> <count>` | — | Draw 1–50 gems; tiers: 10, 50, 100, 500, 1000, 5000 |
| `!hoard <1-4>` | — | Generate a DMG treasure hoard |
| `!loot <1-4>` | — | Generate individual DMG treasure |
| `!namegen <race> [m/f/b] [count]` | — | Generate 1–100 fantasy names |
| `!oracle <question>` | — | Ask a question of at least three words |
| `!roll <expression>` | `r` | Roll bounded dice expressions; see [Dice syntax and limits](#dice-syntax-and-limits) |
| `!trinket <class>` | — | Draw a class-themed trinket from Google Sheets |
| `!wildmagic <1-2>` | `wm`, `surge` | Draw from a wild-magic table |

Valid `collect` biomes are `arctic`, `common`, `desert`, `forest`, `grass`,
`hills`, `mountain`, `swamp`, `underdark`, and `water`.

Name generation examples:

```text
!namegen elf
!namegen dwarf m 10
!namegen f 5
!namegen 20
```

Run `!namegen` without arguments to list the installed race libraries.

### Discord roll aliases and delivery

| Command | Description |
| --- | --- |
| `!alias add <name> <expression>` | Add or interactively overwrite a guild alias |
| `!alias remove <name>` | Remove an alias with confirmation |
| `!alias list [@user]` | List guild aliases, optionally by creator |
| `!roll @<name>` | Roll a saved alias |
| `!set_dm` | Configure the guild DM channel and DM role interactively |
| `!privateroll set #channel [@user]` | Set a private roll channel |
| `!privateroll disable` | Remove your private roll channel |
| `!privateroll show` | Show your private roll channel |
| `!privateroll list` | List assignments; moderators only |

Roll delivery flags must appear at the end of the command:

```text
!roll 1d20+5 -dm
!roll @Test Attack -dm
!roll 1d20 -blind
```

- `-dm` sends to the configured guild DM channel first, then a configured user
  private-roll channel, then the requester's Discord direct messages.
- `-blind` sends only to the configured guild DM channel or configured DM-role
  members. It never posts the protected result publicly.

### Discord moderation and administration

| Command | Description |
| --- | --- |
| `!clear [amount]` | Delete up to 100 messages; alias: `purge`; default: 100 |
| `!setmodchannel` | Configure or disable the moderation-log channel |
| `!settimer <interval> [duration]` | Auto-clear the current channel; values are minutes; interval `0` disables |
| `!setprefix <prefix>` | Set this server's 1–5 character command prefix; use `reset` for the global default |
| `!platform <name> set <parameter> <value>` | Set a validated guild override for one platform |
| `!platform <name> default <parameter\|all>` | Remove overrides and inherit `platforms.yaml` values |
| `!platform <name> enable` | Enable that platform's service for this server only |
| `!platform <name> disable` | Disable that platform's service for this server only |
| `!leave <exact guild name>` | Make EyeBot leave a server |
| `!servers` | DM the owner a list of connected servers |
| `!shutdown` | Close the Discord child; aliases: `sd`, `_shutdown` |
| `!restart <platform>` | Restart an enabled platform child |
| `!load <extension>` | Load a Discord cog |
| `!unload <extension>` | Unload a Discord cog |
| `!reload <extension>` | Reload a Discord cog |

Extension names are the module name without `.py`, such as `roller`.

Platform names are `discord`, `twitch`, `youtube`, `facebook`, `kick`,
`twitter`, `bluesky`, `tiktok`, `instagram`, `substack`, and `kofi`. Examples:

```text
!platform youtube set videos_enabled true
!platform youtube set destination_channel #announcements
!platform twitch set channels first_channel, second_channel
!platform substack set publication_url https://example.substack.com
!platform youtube disable
!platform youtube enable
!platform youtube default videos_enabled
!platform youtube default all
```

Inside a server, these commands are accepted only in that guild's configured
moderation channel. If `mod_channel` is `UNSET` or `DISABLED`, EyeBot directs an
administrator to run `!setmodchannel` or retry through a bot DM. Server command
messages are deleted so only the bot response remains. EyeBot therefore needs
Manage Messages in the moderation channel. If Discord denies deletion, the
setting command still runs and the bot logs the cleanup failure.

In a direct message, the ordinary syntax works when the user manages exactly
one server shared with EyeBot. If the user manages several shared servers, use:

```text
!platform <guild_id> <platform> <action> [parameter] [value]
!platform 123456789012345678 youtube disable
!platform 123456789012345678 youtube set videos_enabled true
```

EyeBot verifies Manage Server permission against the selected guild. Discord
does not permit a bot to delete a user's DM, so the user invocation remains in
the private conversation.

`enable` and `disable` modify only the guild's `enabled` override. They do not
reset, remove, or otherwise change any of that platform's other parameters.

`default` does not copy a value into the guild file. It removes the override,
so the current value in `platforms.yaml` is inherited just as it is for a newly
joined server. Authentication values—including tokens, API keys, client/app
secrets, OAuth credentials, and app passwords—cannot be set through Discord.
They remain platform-wide host configuration.

Accepted guild parameters:

| Platform | Parameters |
| --- | --- |
| Discord | `enabled`, `mod_channel_name` |
| Twitch | `enabled`, `nick`, `channels` |
| YouTube | `enabled`, `channel_id`, `destination_channel`, `videos_enabled`, `community_posts_enabled`, `livestream_chat_commands_enabled` |
| Facebook | `enabled`, `page_id`, `destination_channel`, `posting_enabled`, `livestream_chat_commands_enabled` |
| Kick | `enabled`, `channel`, `livestream_chat_commands_enabled` |
| Twitter/X | `enabled`, `posting_enabled` |
| Bluesky | `enabled`, `handle`, `posting_enabled` |
| TikTok | `enabled`, `posting_enabled` |
| Instagram | `enabled`, `account_id`, `posting_enabled` |
| Substack | `enabled`, `publication_url`, `destination_channel`, `newsletters_enabled`, `podcasts_enabled` |
| Ko-fi | `enabled`, `page_url`, `destination_channel`, `donations_enabled`, `memberships_enabled`, `shop_orders_enabled`, `webhooks_enabled` |

Boolean values accept `true/false`, `yes/no`, `on/off`, `enabled/disabled`, or
`1/0`. Destination channels accept a Discord channel mention or numeric ID.
URLs must use HTTPS and cannot contain embedded credentials. Account names,
handles, platform IDs, lists, and URLs are length- and character-validated.

### Twitch-only command

| Command | Description |
| --- | --- |
| `!hello` | Confirm that the Twitch bot is connected and responding |

Private and blind results are never sent to public Twitch chat. Without an
authenticated private/moderator destination resolver, Twitch returns a
configuration notice instead of the protected result.

## Dice syntax and limits

### Syntax

| Form | Meaning | Example |
| --- | --- | --- |
| `NdS` | Roll N dice with S sides | `2d6` |
| `+N` / `-N` | Add or subtract a flat modifier | `1d20+5` |
| `+NdS` / `-NdS` | Add or subtract another dice component | `2d6+1d4-2` |
| `adv` | Roll the component twice and keep the higher total | `1d20adv+5` |
| `dis` | Roll the component twice and keep the lower total | `1d20dis+5` |
| `kN` | Keep the highest N dice | `4d6k3` |
| `lN` | Drop the lowest N dice | `4d6l1` |
| `ex` | Explode dice that roll their maximum | `2d6ex` |
| `r=N` | Reroll a specific result | `4d6r=1` |
| `r<N` / `r>N` | Reroll results below/above a target | `4d6r<2` |
| `iN` | Repeat a dice component N times | `1d20i5` |

Use commas or new lines for multiple expressions:

```text
!roll 1d20+5, 2d6+3
```

### Validation bounds

| Limit | Value |
| --- | ---: |
| Dice per component | 100 |
| Die sides | 2–10,000 |
| Repeat count (`iN`) | 1–20 |
| Expression length | 200 characters |
| Expressions per command | 10 |
| Additive/subtractive components per expression | 20 |
| Absolute flat modifier | 1,000,000 |
| Explosions per die | 10 |
| Rerolls per die | 10 |
| Estimated work units per expression/command | 10,000 |

Keep and drop values must be possible for the number of dice. Reroll targets
must be possible for the die, and a reroll condition cannot cover every face.
Advantage and disadvantage cannot be combined.

Discord output uses conservative embed limits, at most 24 fields per embed,
5,600 total characters per embed, and 10 embeds per roll. Extremely long dice
and repeat breakdowns are abbreviated or truncated.

## Persistent data

EyeBot writes several runtime files:

| Path | Contents |
| --- | --- |
| `config.yaml` | Global prefix, logging, and shared service settings |
| `platforms.yaml` | Connector-wide toggles and legacy credential fallback |
| `data/guilds/<guild_id>.yaml` | One Discord server's mutable settings |
| `data/guilds/<guild_id>.yaml.bak` | Previous valid version of that guild file |
| `data/secrets/global.secrets` | Encrypted global platform credentials |
| `data/secrets/guilds/<guild_id>.secrets` | Encrypted guild credential overrides |
| `*.secrets.bak` | Previous encrypted version of a secret store |
| `secrets/eyebot_master_key` | Encryption key; stored separately from ciphertext |
| `backup-YYYY-MM-DD.bak` | Latest global YAML recovery backup |
| `platforms-backup-YYYY-MM-DD.bak` | Latest platform YAML recovery backup |
| `src/cogs/roller/config.json` | Legacy source imported during migration |
| `src/cogs/clear/config.json` | Legacy source imported during migration |
| `output.log` | Default log output |

Compose bind-mounts both top-level YAML files, stores guild files in the named
volume `guild-data`, and stores ciphertext in `secret-data`. To inspect the
volumes without displaying decrypted values, use:

```bash
docker run --rm -v eyebot_guild-data:/guilds alpine ls -la /guilds
docker run --rm -v eyebot_secret-data:/secrets alpine ls -la /secrets
```

On first startup, any former `discord.guilds` entries in `platforms.yaml` and
values from the two legacy JSON files are migrated into individual guild files.
Existing guild-file values take precedence. The old embedded `guilds` section
is then removed from `platforms.yaml`.

Each guild file contains its name, prefix, DM channel and role, aliases, user
private-roll channels, moderation-log channel, and per-channel auto-clear
timers. Writes use a temporary file and atomic replacement. The directory is
set to mode `0700` and files to `0600` where the operating system supports Unix
permissions. A corrupt guild file is restored from its `.yaml.bak` copy.

The image runs as UID/GID `10001`. On Linux, make sure that account can write
`platforms.yaml`. Back up both YAML files, both data volumes, and the master key
before upgrades. Keep the master-key backup separate from ciphertext backups.
Local installations may override storage with `EYEBOT_GUILD_CONFIG_DIR`,
`EYEBOT_SECRET_DIR`, and `EYEBOT_MASTER_KEY_FILE`.

## Testing

The test suite uses Python's standard `unittest` runner:

```bash
PYTHONPATH=src:. python -m unittest discover -s tests -v
```

PowerShell:

```powershell
$env:PYTHONPATH = "src;."
python -m unittest discover -s tests -v
```

Additional validation:

```bash
python -m compileall -q src tests healthcheck.py
docker compose config
```

## Troubleshooting

### Discord connects but commands do not respond

- Confirm **Message Content Intent** is enabled in the Developer Portal.
- Confirm the bot can view the channel and send messages.
- Confirm the command uses the configured prefix.
- Check `docker compose logs eyebot` for cog-loading errors.

### Discord rejects the connection

- Reset and recopy the bot token.
- Enable both privileged intents requested by the code.
- Ensure YAML indentation did not move `bot_token` outside `discord`.

### `ModuleNotFoundError: No module named 'yaml'`

The import name is `yaml`, while the package name in `requirements.txt` is
`PyYAML`. Rebuild the standard root-level `Dockerfile` without cached layers:

```bash
docker compose down
docker compose build --no-cache eyebot
docker compose up --detach --force-recreate
docker compose logs --follow eyebot
```

Do not install a package named `yaml` or add `pip install` commands to the
running container. The image build must install `PyYAML==6.0.3` from the pinned
manifest. If Docker still starts an old image, remove that specific EyeBot image
and rebuild it; do not delete unrelated Docker images or volumes.

### Twitch does not connect

- Set `twitch.enabled: true` as a Boolean.
- Provide `twitch.tmi_token`.
- Provide at least one textual entry in `twitch.channels`.
- Check the token belongs to the bot account and has chat access.
- Inspect `docker compose logs eyebot` for validation or authentication errors.

### Restart command cannot connect

- Run the shell form inside the container with `docker compose exec`.
- Confirm the overall process is `src/eyebot.py`, not a direct platform
  entrypoint.
- Confirm every process uses the same `EYEBOT_CONTROL_PORT`.
- Do not publish or externally proxy the control port.

### Google Sheets commands report unavailable data

- Confirm the JSON credential file exists at the configured path.
- Mount it into the container when using Docker.
- Share the required sheets with the service account email.
- Enable both Sheets and Drive APIs in the Google Cloud project.

### Configuration recovery

EyeBot creates separate dated backups for the two top-level YAML files. When
loading either file fails, its service attempts to restore the latest matching
backup. Each guild file also keeps its immediately previous valid contents in
`<guild_id>.yaml.bak` for isolated recovery. Each encrypted secret store keeps
one encrypted `.bak` version. EyeBot fails closed if ciphertext exists without
the matching key or neither encrypted copy can be authenticated.

## Security

- Never commit `config.yaml`, `platforms.yaml`, service-account keys, OAuth
  tokens, `data/guilds/`, `data/secrets/`, `secrets/`, or backups.
- Never pass secret values as command-line arguments or Discord commands.
- Back up the master key separately; losing it makes encrypted stores
  unrecoverable, while exposing it together with ciphertext exposes secrets.
- Keep placeholder connectors disabled until implemented and reviewed.
- Do not expose the supervisor's loopback control port.
- Grant the Discord bot only the permissions required by enabled commands.
- Run the container as the included non-root `eyebot` user.
- Rotate any credential immediately if it appears in Git history, logs,
  screenshots, chat, or an archive.
- Removing a secret from the latest commit does not remove it from Git history.
  Revoke or rotate it first, then clean history if required.

## Acknowledgments

Thanks to surdaft for help and inspiration during the project's early
development.
