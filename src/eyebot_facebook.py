"""Placeholder entrypoint for the future EyeBot Facebook integration."""

from adapters.facebook_adapter import FACEBOOK_ADAPTER


def main():
    FACEBOOK_ADAPTER.require_implementation()


if __name__ == "__main__":
    main()
