PLAIN_TEXT_PLATFORMS = frozenset(
    {"twitch", "youtube", "kick", "facebook", "tiktok"}
)


def uses_plain_text_namegen_output(platform):
    platform_value = getattr(platform, "value", platform)
    return str(platform_value or "").casefold() in PLAIN_TEXT_PLATFORMS


def format_namegen_output(results, quantity, race=None, *, plain_text=False):
    name_type = "Random" if race is None else race.title()
    if plain_text:
        return f"<Generated {quantity} {name_type} Name(s)>-- {', '.join(results)}"

    result_str = "\n".join(results)
    return f"**Generated {quantity} {name_type} Name(s):**\n```{result_str}```"
