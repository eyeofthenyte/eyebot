"""Placeholder entrypoint for the future EyeBot Bluesky integration."""

from adapters.bluesky_adapter import BLUESKY_ADAPTER


def main():
    BLUESKY_ADAPTER.require_implementation()


if __name__ == "__main__":
    main()
