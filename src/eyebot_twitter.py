"""Placeholder entrypoint for the future EyeBot Twitter/X integration."""

from adapters.twitter_adapter import TWITTER_ADAPTER


def main():
    TWITTER_ADAPTER.require_implementation()


if __name__ == "__main__":
    main()
