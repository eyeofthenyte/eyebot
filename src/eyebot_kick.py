"""Placeholder entrypoint for the future EyeBot Kick integration."""

from adapters.kick_adapter import KICK_ADAPTER


def main():
    KICK_ADAPTER.require_implementation()


if __name__ == "__main__":
    main()
