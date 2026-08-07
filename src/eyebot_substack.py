"""Placeholder entrypoint for the future EyeBot Substack integration."""

from adapters.substack_adapter import SUBSTACK_ADAPTER


def main():
    SUBSTACK_ADAPTER.require_implementation()


if __name__ == "__main__":
    main()
