"""Allowlisted platform credentials for encrypted secret storage."""

PLATFORM_SECRET_PARAMETERS = {
    "discord": frozenset({"bot_token"}),
    "twitch": frozenset({"tmi_token", "client_id"}),
    "youtube": frozenset(
        {"api_key", "client_id", "client_secret", "refresh_token"}
    ),
    "facebook": frozenset(
        {"app_id", "app_secret", "access_token"}
    ),
    "kick": frozenset(
        {"client_id", "client_secret", "access_token"}
    ),
    "twitter": frozenset(
        {
            "api_key",
            "api_secret",
            "bearer_token",
            "access_token",
            "access_token_secret",
        }
    ),
    "bluesky": frozenset({"app_password"}),
    "tiktok": frozenset(
        {"client_key", "client_secret", "access_token"}
    ),
    "instagram": frozenset(
        {"app_id", "app_secret", "access_token"}
    ),
    "substack": frozenset({"email", "credential"}),
    "kofi": frozenset({"verification_token"}),
}


def validate_secret_name(platform: str, parameter: str) -> tuple[str, str]:
    selected_platform = platform.strip().casefold()
    selected_parameter = parameter.strip().casefold()
    allowed = PLATFORM_SECRET_PARAMETERS.get(selected_platform)
    if allowed is None:
        raise ValueError(f"Unsupported platform: {platform}")
    if selected_parameter not in allowed:
        choices = ", ".join(sorted(allowed))
        raise ValueError(
            f"Unsupported secret for {selected_platform}: {parameter}. "
            f"Allowed values: {choices}"
        )
    return selected_platform, selected_parameter
