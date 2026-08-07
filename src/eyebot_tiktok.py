"""Placeholder entrypoint for the future EyeBot TikTok integration."""

from adapters.tiktok_adapter import TIKTOK_ADAPTER


def main():
    TIKTOK_ADAPTER.require_implementation()


if __name__ == "__main__":
    main()
