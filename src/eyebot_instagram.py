"""Placeholder entrypoint for the future EyeBot Instagram integration."""

from adapters.instagram_adapter import INSTAGRAM_ADAPTER


def main():
    INSTAGRAM_ADAPTER.require_implementation()


if __name__ == "__main__":
    main()
