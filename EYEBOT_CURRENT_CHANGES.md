# EyeBot Current Changes

## Summary

This change set restructures EyeBot into a safer multi-platform, multi-server
application. It separates global, platform, guild, and secret configuration;
adds platform-neutral command transports; hardens Discord roll delivery; adds
guild-scoped platform administration; expands Docker support; and introduces
encrypted global and per-guild credential storage.

## Configuration architecture

- Reduced `config.yaml` to process-wide settings such as the command prefix,
  logging, and shared Google Sheets configuration.
- Moved platform credentials, connector toggles, and platform-wide defaults to
  `platforms.yaml` using the new `platforms.yaml.dist` template.
- Added `PlatformConfigService` to merge global and platform configuration
  without making mutable runtime data part of the tracked source tree.
- Added a default command prefix for every newly discovered Discord guild.
- Added a per-guild prefix override and the Manage Server command:

  ```text
  !setprefix <prefix>
  <current-prefix>setprefix reset
  ```

- Discord direct messages and non-Discord transports continue to use the
  process-wide prefix.

## Separate Discord guild files

- Replaced the shared `discord.guilds` mapping in `platforms.yaml` with one
  mutable YAML file per Discord server:

  ```text
  data/guilds/<guild_id>.yaml
  ```

- Added strict numeric guild-ID validation to prevent path traversal.
- Added atomic file replacement, restrictive Unix permissions, per-file
  backups, and corruption recovery.
- Added automatic migration from both the former embedded
  `platforms.yaml -> discord.guilds` structure and the legacy Roller/Clear JSON
  files.
- Existing guild-file values take precedence during migration.
- Added a dedicated persistent `guild-data` Docker volume.

## Encrypted platform secrets

- Added authenticated Fernet encryption for platform credentials.
- Added separate encrypted scopes for global defaults and individual Discord
  guilds:

  ```text
  data/secrets/global.secrets
  data/secrets/guilds/<guild_id>.secrets
  ```

- Stores the master encryption key separately at
  `secrets/eyebot_master_key` or the configured Docker secret path.
- Added atomic encrypted writes, encrypted backups, `0600` file permissions,
  `0700` directories, wrong-key detection, and fail-closed startup behavior.
- Added a platform/parameter allowlist covering Discord, Twitch, YouTube,
  Facebook, Kick, Twitter/X, Bluesky, TikTok, Instagram, Substack, and Ko-fi.
- Added uniform precedence:

  1. Guild-specific encrypted secret.
  2. Global encrypted secret.
  3. Legacy plaintext `platforms.yaml` value.

- Removed interactive plaintext Discord-token persistence from bot startup.
- Added `cryptography` as a pinned direct dependency.

### Secret-management CLI

Added `src/manage_secrets.py` with hidden interactive entry and confirmation:

```bash
# Create the master key once
python src/manage_secrets.py init

# Global secret
python src/manage_secrets.py set discord bot_token
python src/manage_secrets.py set youtube client_secret

# Guild-specific override
python src/manage_secrets.py set youtube client_secret \
  --guild 123456789012345678

# List names without values
python src/manage_secrets.py list
python src/manage_secrets.py list --guild 123456789012345678

# Delete a secret
python src/manage_secrets.py delete youtube client_secret \
  --guild 123456789012345678
```

The CLI never accepts secret values as ordinary command-line arguments. It can
read unattended values from a protected `--value-file` and rejects
group/world-readable files on POSIX systems.

## Guild platform administration

- Added the Discord-specific `platform.py` cog.
- Added validated guild-scoped platform overrides:

  ```text
  !platform <platform> set <parameter> <value>
  !platform <platform> default <parameter>
  !platform <platform> default all
  !platform <platform> enable
  !platform <platform> disable
  ```

- `enable` and `disable` change only the selected guild's `enabled` override;
  they do not reset any other platform parameters.
- `default` removes an override and restores inheritance from
  `platforms.yaml`.
- Added validation for booleans, Discord channel mentions/IDs, numeric Meta
  IDs, YouTube channel IDs, Twitch names/lists, Bluesky handles, HTTPS URLs,
  Ko-fi domains, lengths, and bounded list sizes.
- Authentication tokens and credentials cannot be entered through Discord;
  the cog directs administrators to the encrypted host-side secret manager.
- Requires Manage Server permission.
- In a guild, platform commands are accepted only in the configured moderation
  channel. If no moderation channel is set, EyeBot directs the administrator
  to run `!setmodchannel` or use a direct message.
- Guild command invocations are deleted so only the bot response remains when
  EyeBot has Manage Messages permission.
- In direct messages, EyeBot automatically selects the only shared guild the
  user manages. When several are available, the explicit form is supported:

  ```text
  !platform <guild_id> <platform> <action> [parameter] [value]
  ```

## Platform-neutral command layer and transports

- Added a platform-neutral request/response model and shared command routing.
- Adapted Discord and Twitch into transports around the shared command layer.
- Preserved Discord-specific operations in Discord cogs, including guild
  administration, roles, reactions, channel creation, private permissions,
  message purging, and extension management.
- Added platform placeholders and configuration sections for YouTube,
  Facebook, Kick, Twitter/X, Bluesky, TikTok, Instagram, Substack, and Ko-fi.
- Added supervisor support for starting and restarting enabled platform child
  processes.
- Prevented non-Discord transports from displaying Discord attachment suffixes.

## Roller and Discord output protections

- Corrected duplicate, requester-private, DM-channel, and blind-result delivery
  behavior.
- Added bounded dice parsing and computational-work validation.
- Set the maximum die size to `10,000`.
- Added limits for expression length, comma-separated expressions, repeat
  counts, dice counts, components, rerolls, explosions, keep/drop operations,
  and estimated workload.
- Added Discord embed-size protection, field limits, total-character limits,
  result splitting, and long-breakdown truncation.
- Moved Roller and Clear mutable guild settings into the new per-guild storage
  layer.

## Google Sheets service

- Isolated Google Sheets access behind a reusable service.
- Preserved shared caching and configuration behavior for sheet-backed cogs.
- Kept service-account credentials outside tracked configuration.

## Dependencies and containers

- Added pinned clients or API dependencies for Discord, Twitch, YouTube,
  Facebook, Kick, Twitter/X, Bluesky, TikTok, Instagram, Substack, Ko-fi, and
  encrypted secret handling.
- Updated the container build to install and import-check required packages.
- Corrected Docker/Compose file references and configuration mounts.
- Added separate Docker persistence for guild configuration and encrypted
  secret ciphertext.
- Added Docker Compose master-key secret mounting at
  `/run/secrets/eyebot_master_key`.
- Continued running the container as the non-root UID/GID `10001` user.
- Expanded `.gitignore` and `.dockerignore` to exclude credentials, master
  keys, encrypted stores, guild data, backups, caches, and runtime output.

## Help and documentation

- Expanded the README into installation, Docker, local setup, configuration,
  permissions, command, platform, migration, recovery, and security guidance.
- Updated the help cog to render command usage metadata.
- Added complete `!help platform` syntax and restrictions.
- Documented encrypted-secret initialization, global and guild commands,
  Docker provisioning, resolution precedence, supported parameters, backup
  responsibilities, and master-key recovery limitations.

## Tests and validation

- Added and expanded tests for:

  - Dice parsing and bounded rolls.
  - Loot tables.
  - Configuration recovery.
  - Discord transport routing.
  - Platform placeholders.
  - Per-guild prefix handling.
  - Separate guild-file migration and recovery.
  - Platform command validation and access restrictions.
  - Guild-specific enable/disable isolation.
  - DM guild resolution.
  - Encrypted secret non-disclosure.
  - Global/guild secret precedence.
  - Missing and incorrect encryption keys.
  - Encrypted backup recovery.
  - Secret-name and guild-ID validation.
  - Secret CLI initialization and provisioning.

Validation result:

```text
Ran 126 tests
OK
```

Python compilation, pinned dependency checks, Compose YAML parsing, archive
integrity checking, and `git diff --check` also pass.

## Deployment and migration notes

1. Copy `config.yaml.dist` to `config.yaml` and `platforms.yaml.dist` to
   `platforms.yaml`.
2. Install the pinned requirements.
3. Run `python src/manage_secrets.py init` exactly once and back up the created
   master key separately.
4. Move plaintext credentials from `platforms.yaml` into encrypted storage.
5. Blank the migrated plaintext credential values.
6. Rebuild the container after dependency changes.
7. Back up `guild-data`, `secret-data`, both YAML files, and the master key
   before upgrading.
8. Never replace the master key while encrypted stores still depend on it.

The legacy plaintext credential fallback remains available for migration, but
new deployments should use encrypted storage exclusively.
