"""Placeholder entrypoint for the future EyeBot Ko-fi integration."""

from adapters.kofi_adapter import KOFI_ADAPTER


def main():
    KOFI_ADAPTER.require_implementation()


if __name__ == "__main__":
    main()
