"""Placeholder entrypoint for the future EyeBot YouTube integration."""

from adapters.youtube_adapter import YOUTUBE_ADAPTER


def main():
    YOUTUBE_ADAPTER.require_implementation()


if __name__ == "__main__":
    main()
