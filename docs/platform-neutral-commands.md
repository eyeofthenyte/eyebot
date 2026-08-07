# Platform-neutral commands

The `core` package separates command behavior from Discord, Twitch, YouTube,
Facebook, Kick, and other platform SDKs.

## Request flow

Each transport adapter converts its native event into a `CommandRequest`:

```python
request = CommandRequest.from_text(
    platform=CommandPlatform.DISCORD,
    surface=CommandSurface.CHANNEL,
    actor=CommandActor(
        id=str(message.author.id),
        username=message.author.name,
        display_name=message.author.display_name,
    ),
    location=CommandLocation(
        channel_id=str(message.channel.id),
        channel_name=message.channel.name,
        community_id=str(message.guild.id),
        community_name=message.guild.name,
    ),
    content=message.content,
    prefix="!",
)
```

The request contains only strings, enums, tuples, timestamps, and metadata.
It never contains a Discord context, Twitch context, or other SDK object.

## Generic handlers

Handlers receive a request and return a `CommandResponse`:

```python
router = CommandRouter()


@router.command("hello", aliases=("hi",))
async def hello(request):
    return CommandResponse.text(
        f"Hello {request.actor.display_name or request.actor.username}!"
    )
```

Handlers may also return cards and attachments:

```python
return CommandResponse(
    messages=(
        ResponseMessage(
            card=ResponseCard(
                title="Roll result",
                fields=(
                    ResponseField(name="Total", value="17"),
                ),
            )
        ),
    ),
    visibility=ResponseVisibility.REQUESTER,
)
```

## Response delivery

The originating adapter translates neutral response objects into native output:

- Discord maps cards to embeds and attachments to `discord.File`.
- Twitch, YouTube, Facebook, and Kick flatten cards into chat-safe text.
- `PUBLIC` replies in the originating channel.
- `REQUESTER` replies privately to the invoking user.
- `MODERATORS` targets the configured moderation destination.
- `BLIND` hides results from the requester and targets the configured game
  master or moderator destination.

Adapters own message-size limits, pagination, permissions, and delivery errors.
Generic command handlers own command rules and returned information.

## Transport adapters

`CommandTransportAdapter` owns the shared dispatch lifecycle:

1. Convert a native message to `CommandRequest`.
2. Leave non-commands and commands outside the portable registry untouched.
3. Dispatch registered commands through `CommandRouter`.
4. Render and deliver the resulting `CommandResponse`.

`DiscordTransportAdapter` maps Discord users, roles, channels, guilds, embeds,
and attachments. The Discord entry point sends portable commands through this
adapter and passes Discord-only commands to `discord.py`.

`TwitchTransportAdapter` maps Twitch chatters, badges, channels, rooms, and
cards. Cards are flattened into readable chat text and split into messages no
longer than 450 characters, leaving safety margin below Twitch's 500-character
limit. Attachments are Discord-only: non-Discord output omits attachment names
and removes any `| Attachments:` suffix together with everything following it.
The Twitch entry point uses `build_portable_runtime()` to load the same portable
cog callbacks used by Discord. Only its `hello` connectivity check remains a
native Twitch command.

The Twitch process connects only when `twitch.enabled` is the YAML boolean
`true`. It defaults to `false`; when disabled, the entrypoint logs its state and
returns without constructing or running the Twitch bot.

Docker Compose runs `src/eyebot.py` as the overall bot supervisor. Each enabled
platform runs in its own child process, allowing each SDK to retain its blocking
client loop while sharing one container. The supervisor forwards SIGTERM and
SIGINT to all children and treats an unexpected child exit as a container
failure so the Compose restart policy can recover it. Startup validation
reports missing `twitch.tmi_token` or `twitch.channels` before Twitch attempts
a connection.

The supervisor exposes a loopback-only control endpoint for restarting an
individual enabled child. Container operators use
`python src/eyebot.py restart <platform>` from inside the container. The
Discord-only, owner-checked `!restart <platform>` administration command calls
the same endpoint. Unknown, disabled, and non-running platforms are rejected;
restarting one child does not interrupt the other enabled platforms.

Private or blind Twitch results are never posted publicly. A deployment may
inject a Twitch destination resolver when it has an authenticated whisper or
moderator-channel implementation; otherwise the adapter posts only a delivery
configuration notice, not the protected result.

## Future platform placeholders

Disabled placeholder descriptors and blank configuration sections are provided
for YouTube, Facebook, Kick, Twitter/X, Bluesky, TikTok, Instagram, Substack,
and Ko-fi. These placeholders document intended capabilities without making
network calls or implying that authentication and API support are complete.

Each platform also has a matching `src/eyebot_<platform>.py` placeholder
entrypoint. Importing these modules has no side effects. Running one directly
raises an explicit `NotImplementedError` until its connector is implemented.

- YouTube: videos, community posts, and livestream chat commands
- Facebook: publishing and livestream chat commands
- Kick: livestream chat commands
- Twitter/X, Bluesky, TikTok, and Instagram: publishing
- Substack: newsletter and podcast retrieval
- Ko-fi: donation, membership, shop-order, and webhook events

Every corresponding `enabled` setting defaults to `false`, and every credential
value is blank in `config.yaml.dist`. Enabling an unimplemented placeholder
causes its child process to report that the connector is not implemented; the
supervisor then stops the group rather than silently running a partial setup.

## Cog migration boundary

The shared cog registry exposes commands whose inputs and outputs are portable:
carousing; component, flora, potion, and poison lookups; gems; help; hoards;
loot; name generation; oracle; rolls; trinkets; and wild magic.

Discord continues to own operations that inherently manipulate Discord state:
channel creation, message purging and timers, roles, reactions, guild
administration, extension loading, and private-channel permissions. Roller
alias administration and DM/private-channel configuration therefore remain
native Discord commands.

The cog bridge captures existing callback output as `CommandResponse` values.
Discord and Twitch both send portable messages through the same registry and
router. Discord resolves `REQUESTER` and `BLIND` visibility at its transport
boundary, including configured DM channel and DM role destinations.

## Serialization

Requests and responses support `to_dict()` and `from_dict()`. This allows them
to cross process boundaries, enter a queue, or be logged without serializing
platform SDK objects.
