# EyeBot

Current release: **2.1.0**

EyeBot is a Python bot framework for tabletop-RPG utilities and shared chat
commands. Discord and Twitch are currently implemented. A platform-neutral
request/response layer allows the same gameplay commands to run through either
transport, while Discord-specific administration remains in Discord cogs.

The overall supervisor starts every enabled platform connector as a separate
child process inside one container. Optional connectors provide live alerts,
OAuth, signed webhooks, social publishing, or feed delivery according to the
capabilities listed below. External application approval and scopes are still
required before a connector can call its production platform API.

## Contents

- [Features](#features)
- [Platform status](#platform-status)
- [Requirements](#requirements)
- [Discord application setup](#discord-application-setup)
- [Installation with Docker Compose](#installation-with-docker-compose)
- [Local installation](#local-installation)
- [Encrypted platform secrets](#encrypted-platform-secrets)
- [Per-guild OAuth and webhook gateway](#per-guild-oauth-and-webhook-gateway)
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

| Platform | Config section | Connector status | Live alerts | Shared chat commands |
| --- | --- | --- | --- | --- |
| Discord | `discord` | Implemented | Destination | Yes |
| Twitch | `twitch` | Implemented | Yes | Yes |
| YouTube | `youtube` | Live alerts and chat API adapter | Yes | API adapter |
| Facebook | `facebook` | Live alerts and Page posting | Yes | Webhook events |
| Kick | `kick` | Live alerts and verified webhook chat commands | Yes | Yes |
| Twitter/X | `twitter` | Spaces alerts and posting | Yes | No |
| Bluesky | `bluesky` | Posting implemented | No | No |
| TikTok | `tiktok` | Approved Content Posting; LIVE API unavailable | No | No |
| Instagram | `instagram` | Live alerts and image posting | Yes | No |
| Substack | `substack` | RSS newsletters/podcasts | No | No |
| Ko-fi | `kofi` | Signed webhook delivery | No | No |

Keep a connector disabled until its credentials, scopes, guild account mapping,
and external provider approval are complete. A required child exiting causes
the supervisor to stop the container instead of silently running a partial
configuration.

## Requirements

### Docker installation

- Git
- Docker Engine or Docker Desktop with Docker Compose v2

The image supplies Python 3.12, Node.js, and the pinned Python dependencies.

### Local installation

- Git
- Python 3.12 or newer (`substack-api==1.3.0` requires Python 3.12)
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
| YouTube | `api_key`, `client_id`, `client_secret`, `access_token`, `refresh_token` |
| Facebook | `app_id`, `app_secret`, `access_token`, `refresh_token`, `webhook_verify_token` |
| Kick | `client_id`, `client_secret`, `access_token`, `refresh_token` |
| Twitter/X | `api_key`, `api_secret`, `bearer_token`, `client_id`, `client_secret`, `access_token`, `access_token_secret`, `refresh_token` |
| Bluesky | `app_password` |
| TikTok | `client_key`, `client_secret`, `access_token`, `refresh_token` |
| Instagram | `app_id`, `app_secret`, `access_token`, `refresh_token`, `webhook_verify_token` |
| Substack | `email`, `credential` |
| Ko-fi | `verification_token` |
| Email | `smtp_username`, `smtp_password` |

Direct entrypoints do not provide overall process supervision.

## Per-guild OAuth and webhook gateway

YouTube, Facebook, Instagram, Kick, X, and TikTok use the optional EyeBot
gateway for per-guild OAuth callbacks. Enable it only behind an HTTPS reverse
proxy:

```yaml
# config.yaml
gateway:
  enabled: true
  host: 0.0.0.0
  port: 8080
  public_base_url: https://bot.example.com
```

The Compose port defaults to `127.0.0.1:8080`, so it is not directly exposed
to the internet. Configure nginx, Caddy, or another TLS proxy; an nginx example
is provided at `deploy/nginx-eyebot.conf.example`. Register the exact callback
for each application:

```text
https://bot.example.com/oauth/<platform>/callback
```

Kick additionally uses one application-wide webhook endpoint:

```text
https://bot.example.com/webhooks/kick
```

Enable that URL in the Kick developer application. EyeBot verifies the
`Kick-Event-Signature` RSA signature over the exact raw request body, rejects
stale timestamps, persists message-ID deduplication under `data/webhooks/`,
and routes the verified broadcaster ID to one eligible guild. Kick OAuth must
grant `user:read`, `channel:read`, `chat:write`, and `events:subscribe`.

Store the platform application client ID/secret with `manage_secrets.py`, set
the guild's source account/channel parameters, then have a Manage Server user
run this in the guild mod channel:

```text
!platform youtube connect
!platform facebook connect
!platform instagram connect
!platform kick connect
!platform twitter connect
!platform tiktok connect
```

EyeBot deletes the guild invocation and sends a signed, single-use, ten-minute
authorization link to the moderator's DM. Callback state is HMAC-signed and
uses PKCE where the provider supports it. Access and refresh tokens are stored
only in the encrypted per-guild secret file. Public metadata such as scopes,
expiration, connection time, and account name is stored in that guild's YAML.
Account discovery verifies the authorized YouTube channel, Meta Page/Instagram
professional account, X user, or TikTok identity before saving it.

Disconnect and remove the guild's OAuth tokens with:

```text
!platform <platform> disconnect
```

Meta and Ko-fi webhooks use these routes:

```text
https://bot.example.com/webhooks/facebook/<guild_id>
https://bot.example.com/webhooks/instagram/<guild_id>
https://bot.example.com/webhooks/kofi/<guild_id>
```

Meta requests require `X-Hub-Signature-256`; Ko-fi events require the guild's
verification token. The gateway limits bodies to 1 MiB, rate-limits clients,
rejects duplicate events, disables Discord mentions, and routes only to the
configured guild destination.

### Social publishing commands

Posting commands require Manage Server. Text posts use the configured guild
mod channel. Enabling Twitter/X, Facebook, or Bluesky prompts the moderator to
create a private `#socialmedia_sources` channel, select an existing channel
already hidden from `@everyone`, or skip setup. EyeBot needs **Manage Channels**
to create the channel. The invoking command is deleted and a durable job is written under
`data/guilds/.platform_jobs/`. Only the enabled platform child consumes its
queue, and failed jobs retry three times before becoming `.failed` files.

```text
!socialpost bluesky Text to publish
!socialpost twitter Text to publish
!socialpost facebook Text to publish
!socialpost all Text for every enabled posting connector
!socialmedia twitter Caption for attached images
!socialmedia facebook Caption for attached images
!socialmedia bluesky Caption for attached images
!socialmedia all Caption for every enabled image connector
!socialurl instagram https://cdn.example.com/image.jpg Caption
!socialurl tiktok https://cdn.example.com/video.mp4 Caption
```

Run `!socialmedia` in the configured source channel and either attach one to
four images to the command or reply to an existing message containing the
images. EyeBot immediately validates and privately stages JPEG, PNG, GIF, or
WebP files so expiring Discord attachment URLs are not placed in the queue.
Each file may be at most 5 MB; Bluesky's current upload path applies a stricter
2 MB per-image limit. Hosted Instagram images must be JPEG; hosted TikTok
photos may be JPEG or WebP. Other formats remain available to attachment
platforms that accept them. The source channel setting and platform connection
are per guild. Platform credentials are never read from channel messages.

Moderators can also approve source messages by reaction. Put the caption in
the message body and attach one to four images. When public media hosting is
enabled, EyeBot temporarily publishes validated attachments through its HTTPS
gateway for Instagram and TikTok; an explicit stable HTTPS URL remains
available through `!socialurl`. EyeBot records the
guild, source-message ID, and destination so repeated reactions cannot create
duplicate posts across restarts.

| Reaction | Action |
|---|---|
| 🐦 | Queue attached images for Twitter/X |
| 🦋 | Queue attached images for Bluesky |
| 📘 | Queue attached images for Facebook |
| 📸 | Temporarily host attached images and queue them for Instagram |
| 🎵 | Temporarily host attached photos and queue them for TikTok |
| 📣 | Queue the message for every compatible enabled platform |
| ❌ | Cancel jobs that have not yet been claimed |

Only members with **Manage Server** can approve or cancel. EyeBot adds ✅ when
a job is queued, ⚠️ when validation fails, and keeps `!socialpost`,
`!socialmedia`, and `!socialurl` as manual alternatives. Ko-fi is intentionally
excluded because its supported integration is inbound payment webhooks, not
outbound publishing.

TikTok initially requests `SELF_ONLY` visibility. Production public posting
requires TikTok application review and compliance with its Content Posting UX
requirements. TikTok `PULL_FROM_URL` also requires ownership verification for
the configured media domain or URL prefix. Instagram media URLs must be
publicly retrievable HTTPS URLs.

### Temporary public media with Caddy

EyeBot's local public-media provider works for both a private standalone bot
and one installation serving multiple Discord guilds. It stores media under
separate guild prefixes, applies a per-guild quota, uses random batch names,
and deletes expired objects in the gateway process. The default Compose file
persists these files in the `public-media` Docker volume.

Enable the gateway and media provider in `config.yaml`:

```yaml
gateway:
  enabled: true
  host: 0.0.0.0
  port: 8080
  public_base_url: https://eyebot.example.com

public_media:
  enabled: true
  provider: local_caddy
  public_base_url: https://eyebot.example.com/media
  storage_path: /app/data/public_media
  retention_hours: 72
  cleanup_interval_seconds: 3600
  max_bytes_per_guild: 1073741824
```

When Caddy runs on the same Windows host as Docker Desktop, keep Compose bound
to localhost and reverse-proxy the gateway. Caddy does not need direct access
to the Docker media volume:

```caddyfile
eyebot.example.com {
	encode zstd gzip

	@eyebot_paths path /health /oauth/* /webhooks/* /media/*
	handle @eyebot_paths {
		reverse_proxy 127.0.0.1:8080
	}

	handle {
		respond "Not found" 404
	}
}
```

Format, validate, and reload Caddy:

```powershell
caddy fmt --overwrite .\Caddyfile
caddy validate --config .\Caddyfile
caddy reload --config .\Caddyfile
```

Recreate EyeBot after changing Compose or `config.yaml`:

```powershell
docker compose up --detach --build --force-recreate eyebot
curl.exe https://eyebot.example.com/health
```

The health response reports whether public media is enabled. A generated URL
has this form:

```text
https://eyebot.example.com/media/<guild-id>/<random-batch>/<safe-filename>
```

For a multi-guild installation, keep one shared volume and one gateway. Do not
create a public directory per server manually. EyeBot validates the Discord
guild ID, partitions storage automatically, and enforces
`max_bytes_per_guild` independently. The public URL is intentionally
unguessable but must remain anonymously readable while Meta or TikTok fetches
it. Do not place private or sensitive media in the source channel.

`local_caddy` is the implemented provider. The configuration and command help
reserve the following provider names for future storage adapters:

| Provider notation | Intended backend | Status |
| --- | --- | --- |
| `cloudflare_r2` | Cloudflare R2 bucket with an S3 endpoint and custom domain | Placeholder |
| `amazon_s3` | Amazon S3 bucket with a public or signed URL base | Placeholder |
| `azure_blob` | Azure Blob Storage account and container | Placeholder |
| `google_cloud_storage` | Google Cloud project and Cloud Storage bucket | Placeholder |

Cloud access keys, SAS values, and service-account credentials must eventually
be stored through EyeBot's encrypted secret service. The placeholder names do
not activate cloud storage in the current build; selecting one produces a
clear configuration error instead of silently writing to local storage.

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
| `private_install` | Restrict Twitch to host-configured channels; set `false` only for a shared multi-guild bot | `true` |
| `gateway.enabled` | Start the OAuth/webhook child | `false` |
| `gateway.public_base_url` | Externally reachable HTTPS origin | `https://bot.example.com` |
| `public_media.enabled` | Host temporary Instagram/TikTok media through the gateway | `false` |
| `public_media.provider` | Media adapter; currently only `local_caddy` is implemented | `local_caddy` |
| `public_media.public_base_url` | Public HTTPS media prefix ending in `/media` | `https://bot.example.com/media` |
| `public_media.storage_path` | Persistent media directory inside EyeBot | `/app/data/public_media` |
| `public_media.retention_hours` | Maximum temporary-media lifetime | `72` |
| `public_media.cleanup_interval_seconds` | Expiration scan interval | `3600` |
| `public_media.max_bytes_per_guild` | Independent storage quota for each guild | `1073741824` |
| `logging.level` | Configured logging level | `DEBUG` |
| `logging.output` | `terminal`, `syslog`, `both`, or a legacy file path | `both` |
| `logging.global_directory` | Folder for service-wide logs | `/app/data/logs/global` |
| `logging.global_file` | Active global filename supporting `{name}` | `{name}.txt` |
| `logging.guild_logs_enabled` | Also write records associated with a guild to its folder | `true` |
| `logging.guild_directory` | Root folder for guild-specific logs | `/app/data/logs/guilds` |
| `logging.guild_file` | Guild service filename supporting `{platform}` and `{name}` | `{platform}.txt` |
| `logging.max_bytes` | Maximum size of each active log before rotation | `10485760` |
| `logging.archive_days` | Completed backup window included in each ZIP archive | `30` |
| `logging.archive_count` | Number of ZIP archives retained in each folder | `2` |

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
socialmedia_sources_channel: "UNSET"
timers: {}
```

These entries are normally maintained by `!setprefix`, `!set_dm`, `!alias`,
`!privateroll`, `!setmodchannel`, `!platform ... enable`, and `!settimer`;
manual editing is optional.
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
  destination_channel:
```

| Key | Required | Meaning |
| --- | --- | --- |
| `twitch.enabled` | Yes | Starts or skips the Twitch child |
| `twitch.tmi_token` | Legacy only | Plaintext fallback; prefer the encrypted store |
| `twitch.client_id` | Legacy only | Plaintext fallback; prefer the encrypted store |
| `twitch.nick` | Recommended | Bot account name |
| `twitch.channels` | When enabled | YAML list of channel names to join |
| `twitch.destination_channel` | Optional | Default Discord channel ID for go-live posts; guilds can override it |

The Twitch entrypoint validates the token and channel list before connecting.
Use the YAML list shown above; do not provide a numeric channel ID.

For a bot operated only by its owner, leave `private_install: true` in
`config.yaml`; guild Twitch channel overrides are then ignored. For a hosted
bot shared by multiple Discord servers, set `private_install: false`. A server
moderator can then select that server's Twitch destination in its configured
mod channel or by bot DM:

```text
!platform twitch set channel target_channel
!platform twitch set destination_channel #stream-alerts
!platform twitch enable
```

On its next start, the Twitch child joins the connector-wide `channels` plus
each enabled guild's `channel`, with duplicates removed. Restart Twitch after
changing a channel: `!restart twitch` (or restart the container). The shared
bot account's OAuth token and application credentials remain host-managed;
guild moderators do not enter them through Discord.

Each enabled platform child owns its live detector. Twitch polls Helix while
its chat bot is connected; the other live-capable entrypoints run their own
poll loop. New event IDs are persisted under `data/guilds/.live_state/`, so
normal polls and process restarts do not duplicate an announcement. Going
offline clears the state and permits the next live event to post.

Twitch supports the shared gameplay commands and the native `!hello`
connectivity check. Discord-only administration is not exposed on Twitch.
Attachments and everything beginning with `| Attachments:` are omitted from
non-Discord command output.

### Discord bug reports

`!bugreport` is deliberately Discord-only and is not registered with the
platform-neutral command router. It sends the requesting user a DM containing
the originating guild name, instructions, and a selector for Bug Report,
Feature Request, or Other. Bug reports additionally request the affected
platform and command. Every form requests a Discord-safe explanation of at
most 4,000 characters and an optional contact email address.

Configure SMTP delivery in `config.yaml`:

```yaml
bug_reports:
  enabled: true
  recipient: eyebotdev@gmail.com
  sender: eyebotdev@gmail.com
  subject_prefix: "[EyeBot Report]"
  smtp_host: smtp.gmail.com
  smtp_port: 587
  smtp_starttls: true
  smtp_ssl: false
  smtp_timeout: 15
  cooldown_seconds: 300
  max_explanation_length: 4000
  max_attachments: 3
  max_attachment_bytes: 5242880
  max_total_attachment_bytes: 10485760
  allowed_attachment_types:
    - image/png
    - image/jpeg
    - image/gif
    - image/webp
    - application/pdf
    - text/plain
```

Store SMTP authentication in the encrypted global secret store:

```bash
docker compose run --rm --no-deps eyebot python src/manage_secrets.py set email smtp_username
docker compose run --rm --no-deps eyebot python src/manage_secrets.py set email smtp_password
```

For the EyeBot Gmail mailbox, enter `eyebotdev@gmail.com` as the SMTP
username. Enter a dedicated Google App Password as the SMTP password; never
enter the mailbox's normal Google Account password. The Google Account must
have 2-Step Verification enabled before an App Password can be created.

Do not put an SMTP password in `config.yaml` or `platforms.yaml`. Restart EyeBot
after changing configuration or encrypted credentials.

Users may upload allowed files directly in the private report modal. EyeBot
downloads these ephemeral Discord attachments immediately during submission
and retains its configured maximum of three files by default, even though
Discord supports up to ten. Attachments on the original `!bugreport` message
remain temporarily supported for backward compatibility and count toward the
same configured maximum. EyeBot enforces attachment count, individual size,
combined size, extension, declared MIME type, and binary signature. Text
attachments are redacted before email delivery. Users must remove visible
credentials from screenshots and PDFs because text redaction cannot inspect
pixels.

In guild channels, EyeBot attempts to delete the invoking `!bugreport` message
after successfully sending the private form. This requires the **Manage
Messages** permission. The channel acknowledgement is deleted automatically
after ten seconds. Prefix-command replies cannot be ephemeral; only Discord
interaction responses, such as slash-command responses and modal submissions,
support the ephemeral flag.

Every submission receives a traceable ID such as
`BUG-20260815-143000-A1B2C3`. The report body and contact email are never placed
in logs. Audit logs contain only the report ID, type, Discord user ID, and guild
association. Known configured secrets and common token/password patterns are
redacted from form fields, text attachments, and diagnostic errors. SMTP work
runs outside the Discord event loop and has a bounded timeout.

Discord does not expose a guild member's account email to a bot token. The
optional address is therefore entered privately by the user in the modal; it
is not collected automatically.

### Discord support tickets

EyeBot provides a Discord-only private support workflow through `/ticket`.
Each user may have at most three open or assigned tickets. The ticket modal
accepts a required description, an optional same-server Discord message link,
and up to four optional PNG, JPEG, GIF, or WebP images. Ephemeral modal uploads
are downloaded immediately, validated, re-encoded without metadata, and posted
only to the configured moderator log channel. Message-link previews are
suppressed.

Run `/ticket-setup` with moderator permissions to select an existing standard
text channel, create `#support_tickets`, or disable tickets. A moderator log
channel must already be configured with `!setmodchannel`. Ticket setup is
stored in the individual guild YAML file; ticket records are stored atomically
under `data/guilds/.tickets/` and recover from their own backup files.

The public support channel shows only the ticket number and state—it never
identifies the opener. The moderator ticket contains the opener, description,
optional link, and images, together with these controls:

- 📋 **Assign** — atomically assigns the ticket, creates a private support
  thread, adds the opener, notifies them by DM, and updates the public status.
- ✅ **Resolve** — resolves an assigned ticket, exports a bounded transcript to
  the moderator channel, removes the opener, locks and archives the thread,
  and deletes the public status after 30 seconds.
- ❌ **Cancel** — requires confirmation, cancels the ticket, performs the same
  privacy cleanup, and deletes the public status after 30 seconds.

Moderator application commands:

| Command | Purpose |
| --- | --- |
| `/resolved` | Resolve the ticket associated with the current private thread |
| `/resolved ticketnumber:TICKET-000001` | Resolve a ticket from another channel |
| `/ticket-status ticketnumber:TICKET-000001` | Privately display one ticket's state |
| `/ticket-list` | Privately list active tickets without their descriptions |
| `/ticket-reopen ticketnumber:TICKET-000001` | Reopen a closed ticket; requires Manage Server |

Support ticket runtime limits are global defaults in `config.yaml`:

```yaml
support_tickets:
  enabled: true
  max_open_per_user: 3
  max_description_length: 4000
  max_images: 4
  max_image_bytes: 5242880
  max_total_image_bytes: 15728640
  max_image_pixels: 40000000
  status_delete_seconds: 30
  thread_auto_archive_minutes: 1440
  transcript_max_messages: 500
  opening_cooldown_seconds: 60
```

EyeBot requires **View Channels**, **Send Messages**, **Manage Channels**,
**Manage Messages**, **Create Private Threads**, **Send Messages in Threads**,
**Manage Threads**, **Read Message History**, **Attach Files**, and **Embed
Links** for the configured support and moderator channels. Moderators who need
access to every private ticket thread require **Manage Threads**. If the bot
cannot DM a ticket opener, the ticket remains valid and updates continue in the
private thread.

The bot installation must include both the `bot` and `applications.commands`
OAuth scopes so Discord can register and display the slash commands.

### Google Sheets

In `config.yaml`:

```yaml
google_sheets:
  credentials_file: /app/service_account.json
  cache_ttl: 21600
  stale_ttl: 604800
  preload: true
  refresh_in_background: true
  refresh_interval: 21600
  persistent_cache_dir: /app/data/cache/google_sheets
```

| Key | Required | Meaning |
| --- | --- | --- |
| `google_sheets.credentials_file` | For Sheets-backed commands | Path to the service-account JSON |
| `google_sheets.cache_ttl` | No | Fresh in-memory/disk cache lifetime in seconds; defaults to 6 hours |
| `google_sheets.stale_ttl` | No | Maximum age of usable cached data; defaults to 7 days |
| `google_sheets.preload` | No | Warm every registered command workbook when the bot process starts |
| `google_sheets.refresh_in_background` | No | Serve stale data immediately while refreshing it asynchronously |
| `google_sheets.refresh_interval` | No | Proactive refresh interval in seconds; defaults to 6 hours |
| `google_sheets.persistent_cache_dir` | No | Snapshot directory retained across container restarts |

`GOOGLE_SERVICE_ACCOUNT_FILE` can supply the credential path when
`credentials_file` is omitted.

### Logging destinations

EyeBot can write each message to Docker's terminal output and a rotating file
at the same time:

```yaml
logging:
  level: INFO
  output: both
  global_directory: /app/data/logs/global
  global_file: "{name}.txt"
  guild_logs_enabled: true
  guild_directory: /app/data/logs/guilds
  guild_file: "{platform}.txt"
  max_bytes: 10485760
  archive_days: 30
  archive_count: 2
```

`{name}` creates separate active files such as `discord.txt`, `gateway.txt`,
and `kick.txt`, avoiding several processes writing the same file. Records tied
to a guild are written both globally and beneath
`guilds/<guild_id>/<platform>.txt`. The Compose `log-data` volume retains these
files when the container is recreated. Use
`output: terminal` (or the backward-compatible `syslog`) for terminal only, or
put a filename directly in `output` for the legacy file-only behavior.

When an active file reaches `max_bytes`, EyeBot renames it using the date and
time of its final entry, for example `20260815-1427_kick.txt`. Once the oldest
rolled file completes a 30-day window, all rolled service files in that window
and folder are placed into `YYYYMMDD-HHMM_30-day-archive.zip`. Global and each
guild folder are archived independently. Only the two newest archives remain;
creating a third removes the oldest archive after the new ZIP is safely built.

View terminal output with `docker compose logs -f eyebot`. List the persistent
files with `docker compose exec eyebot sh -c "find /app/data/logs -type f -maxdepth 4 -print"`.

### Live-event notifications and remaining placeholders

Twitch, YouTube, Facebook, Kick, X Spaces, and Instagram entrypoints detect
live transitions while their platform child is enabled and post to each
guild's validated `destination_channel`. The Discord bot requires View Channel,
Send Messages, and Embed Links in every destination. Poll intervals are
host-controlled with `live_poll_seconds` in `platforms.yaml` and are bounded to
30–3600 seconds. YouTube defaults to 900 seconds because `search.list` consumes
100 API quota units per request.

TikTok can store a future destination, but its supported public developer APIs
do not expose creator LIVE status. EyeBot does not scrape TikTok or store an
interactive browser session. Remaining placeholder capabilities are:

- YouTube: videos, community posts, and livestream chat commands
- Facebook: publishing and livestream chat commands
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

The Compose file mounts `./service_account.json` read-only by default and keeps
worksheet snapshots in its `cache-data` volume. Set
`GOOGLE_SERVICE_ACCOUNT_SOURCE` when the key is stored elsewhere. The effective
mount is:

```yaml
- type: bind
  source: ./service_account.json
  target: /app/service_account.json
  read_only: true
```

Restart the container after adding or replacing credentials.

EyeBot registers the Carousing, Trinket, and Components workbooks as their cogs
load. Discord warms them after extension loading; Twitch warms them when its bot
becomes ready; and the HTTPS gateway warms them before accepting webhook chat
commands. Expired snapshots remain immediately usable while a background
refresh runs, and the persistent snapshot provides recovery during a temporary
Google outage.

Administrators may force an authoritative reload without restarting EyeBot:

```text
!carousing refresh
!trinket refresh
!flora refresh
!potion refresh
!poison refresh
```

On Discord these refresh operations require Manage Server or Administrator. In
livestream chat they require the authenticated moderator or broadcaster role.
Ordinary command use never forces a synchronous Google request while a usable
cached snapshot exists.

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
| `!bugreport` | Open the private DM report workflow; optional attachments belong on the command message |
| `!platform <name>` | Display effective guild parameters and masked secret presence |
| `!platform <guild_id>` | Display every effective platform setting for a managed guild |
| `!platform twitch channel add <name> [<#destination>]` | Add a Twitch channel with an optional live-alert destination |
| `!platform twitch channel remove <name>` | Remove a Twitch channel from the current guild |
| `!platform twitch channel list` | List Twitch channels owned by the current guild |
| `!platform facebook page add <url> [<#destination>]` | Monitor posts from an accessible Facebook Page |
| `!platform facebook page remove <url|page_id>` | Stop monitoring a Facebook Page |
| `!platform facebook page list` | List Facebook Pages monitored by the guild |
| `!platform instagram account add <username\|url> [<#destination>]` | Monitor an accessible professional Instagram account |
| `!platform instagram account remove <username\|url>` | Stop monitoring an Instagram account |
| `!platform instagram account list` | List Instagram accounts monitored by the guild |
| `!platform twitter account add <username\|url> [<#destination>]` | Monitor posts from a public X account |
| `!platform twitter account remove <username\|url>` | Stop monitoring an X account |
| `!platform twitter account list` | List X accounts monitored by the guild |
| `!platform bluesky account add <handle\|url> [<#destination>]` | Monitor posts from a public Bluesky account |
| `!platform bluesky account remove <handle\|url>` | Stop monitoring a Bluesky account |
| `!platform bluesky account list` | List Bluesky accounts monitored by the guild |
| `!platform kick channel add <name> [<#destination>]` | Monitor a public Kick channel's go-live status |
| `!platform kick channel remove <name>` | Stop monitoring a Kick channel |
| `!platform kick channel list` | List monitored Kick channels |
| `!platform substack publication add <url> [<#destination>]` | Monitor a public Substack RSS publication |
| `!platform substack publication remove <url>` | Stop monitoring a Substack publication |
| `!platform substack publication list` | List monitored Substack publications |
| `!platform <name> set <parameter> <value>` | Set a validated guild override for one platform |
| `!platform <name> default <parameter\|all>` | Remove overrides and inherit `platforms.yaml` values |
| `!platform <name> enable` | Enable that platform's service for this server only |
| `!platform <name> disable` | Disable that platform's service for this server only |
| `!platform <name> on\|off` | Bot owner: allow or prohibit the connector globally |
| `!platform <name> global <parameter> <value>` | Bot owner: set a validated global non-secret parameter |
| `!platform <name> global set <parameter> <value>` | Explicit form of the global-setting command |
| `!platform <name> global list` | Bot owner: list allowed global non-secret parameters and values |
| `!platform <name> post enabled\|disabled` | Bot owner: set the global posting default where supported |
| `!platform <name> chat on\|off` | Bot owner: set the global livestream-chat default where supported |
| `!platform <name> videos on\|off` | Bot owner: set the global video-notification default where supported |
| `!platform <name> connect` | DM a signed per-guild OAuth link to the moderator |
| `!platform <name> disconnect` | Remove that guild's OAuth tokens and connection metadata |
| `!socialpost <name\|all> <text>` | Queue a text post for enabled social connectors |
| `!socialmedia <twitter\|facebook\|bluesky\|instagram\|tiktok\|all> [caption]` | Queue one to four attached/replied images from the private source channel |
| `!socialurl <instagram\|tiktok> <https-url> [caption]` | Queue an approved public media URL |
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
!platform twitch set channel server_channel
!platform twitch set destination_channel #stream-alerts
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

The bot-owner-only `on` and `off` actions control the global `available` gate.
An unavailable connector cannot run even when a guild has enabled it. When an
available connector is enabled by the first guild, EyeBot dynamically starts
its worker; it stops the worker after the final enabled guild disables it.
`post`, `chat`, and `videos` update only parameters supported by that platform.

The bot owner can also manage validated non-secret global defaults:

```text
!platform kick global live_poll_seconds 120
!platform youtube global set videos_enabled true
!platform kick global list
```

Polling intervals accept whole seconds from 15 through 86400. Credential and
token parameters are rejected and must be stored with host-side
`manage_secrets.py`.

The read-only `!platform <name>` status command shows effective values and
whether each value is inherited or overridden by the guild. Secret values are
never displayed: `*****` means a global or guild secret is present and `NULL`
means it is absent.

`!platform <guild_id>` produces a Markdown report for every platform configured
for that guild. The report uses an underlined guild heading, a bullet for each
platform, and separate block-quoted Global Parameters, Guild Parameters, and
Secrets sections. The guild heading is sent first and every platform is sent as
a separate Discord message, so parameters from different platforms are never
combined in one post. It follows the same Manage Server and
moderation-channel/DM restrictions as the other platform commands.

A shared installation can associate multiple Twitch channels with one guild:

```text
!platform twitch channel add first_channel
!platform twitch channel add second_channel #second-stream-alerts
!platform twitch channel list
!platform twitch channel remove first_channel
```

Channel names are normalized, duplicates are ignored, and a guild can store up
to 100 Twitch channels. An optional destination routes that channel's go-live
alerts to a specific Discord channel; otherwise the guild's Twitch
`destination_channel` is inherited. EyeBot restarts the running Twitch child
after a list change so its joined chats are refreshed. The existing singular `channel`
setting is folded into the list the first time `channel add` or `channel remove`
is used. All Twitch channels belonging to a guild share that guild's configured
`destination_channel` for live notifications.

`default` does not copy a value into the guild file. It removes the override,
so the current value in `platforms.yaml` is inherited just as it is for a newly
joined server. Authentication values—including tokens, API keys, client/app
secrets, OAuth credentials, and app passwords—cannot be set through Discord.
They remain platform-wide host configuration.

Accepted guild parameters:

| Platform | Parameters |
| --- | --- |
| Discord | `enabled`, `mod_channel_name` |
| Twitch | `enabled`, `nick`, `channel`, `destination_channel` |
| YouTube | `enabled`, `channel_id`, `destination_channel`, `videos_enabled`, `community_posts_enabled`, `livestream_chat_commands_enabled` |
| Facebook | `enabled`, `page_id`, `destination_channel`, `posting_enabled`, `livestream_chat_commands_enabled` |
| Kick | `enabled`, `channel`, `destination_channel`, `livestream_chat_commands_enabled` |
| Twitter/X | `enabled`, `user_id`, `destination_channel`, `posting_enabled` |
| Bluesky | `enabled`, `handle`, `posting_enabled` |
| TikTok | `enabled`, `destination_channel`, `posting_enabled` |
| Instagram | `enabled`, `account_id`, `destination_channel`, `posting_enabled` |
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
- Keep unconfigured connectors disabled until their credentials, scopes, and account mappings are reviewed.
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
