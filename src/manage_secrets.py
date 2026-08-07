"""Safely create and manage EyeBot's encrypted platform secrets."""

from __future__ import annotations

import argparse
import getpass
import os
import sys
from pathlib import Path

from core.platform_secret_schema import PLATFORM_SECRET_PARAMETERS
from services.platformSecretService import PlatformSecretService


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SECRET_DIR = PROJECT_ROOT / "data" / "secrets"
DEFAULT_KEY_FILE = PROJECT_ROOT / "secrets" / "eyebot_master_key"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Manage encrypted global and per-guild EyeBot secrets.",
    )
    parser.add_argument(
        "--secret-dir",
        default=os.getenv("EYEBOT_SECRET_DIR", str(DEFAULT_SECRET_DIR)),
    )
    parser.add_argument(
        "--key-file",
        default=os.getenv("EYEBOT_MASTER_KEY_FILE", str(DEFAULT_KEY_FILE)),
    )
    commands = parser.add_subparsers(dest="command", required=True)

    commands.add_parser("init", help="Create a new master key without replacing one")

    set_parser = commands.add_parser("set", help="Create or replace one secret")
    _add_secret_selector(set_parser)
    set_parser.add_argument(
        "--value-file",
        help="Read the secret from a protected file instead of prompting",
    )

    delete_parser = commands.add_parser("delete", help="Delete one secret")
    _add_secret_selector(delete_parser)
    delete_parser.add_argument("--yes", action="store_true")

    list_parser = commands.add_parser("list", help="List names without values")
    list_parser.add_argument("--guild", help="Discord guild ID; omit for global")
    return parser


def _add_secret_selector(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("platform", choices=tuple(PLATFORM_SECRET_PARAMETERS))
    parser.add_argument("parameter")
    parser.add_argument("--guild", help="Discord guild ID; omit for global")


def _service(arguments) -> PlatformSecretService:
    return PlatformSecretService(
        arguments.secret_dir,
        master_key_file=arguments.key_file,
    )


def _read_secret(arguments) -> str:
    if arguments.value_file:
        source = Path(arguments.value_file)
        if os.name == "posix" and source.stat().st_mode & 0o077:
            raise PermissionError(
                "The value file must not be accessible by group or other users"
            )
        value = source.read_text(encoding="utf-8").rstrip("\r\n")
    else:
        value = getpass.getpass("Secret value: ")
        confirmation = getpass.getpass("Confirm secret value: ")
        if value != confirmation:
            raise ValueError("Secret values did not match")
    if not value:
        raise ValueError("Secret values cannot be empty")
    return value


def main(argv=None) -> int:
    parser = build_parser()
    arguments = parser.parse_args(argv)
    try:
        if arguments.command == "init":
            path = PlatformSecretService.generate_key_file(arguments.key_file)
            print(f"Created EyeBot master key: {path}")
            return 0

        service = _service(arguments)
        if arguments.command == "set":
            service.set_secret(
                arguments.platform,
                arguments.parameter,
                _read_secret(arguments),
                guild_id=arguments.guild,
            )
            scope = f"guild {arguments.guild}" if arguments.guild else "global"
            print(f"Stored {scope} secret {arguments.platform}.{arguments.parameter}.")
            return 0

        if arguments.command == "delete":
            if not arguments.yes:
                answer = input("Delete this secret? Type 'yes' to continue: ")
                if answer.casefold() != "yes":
                    print("Cancelled.")
                    return 1
            removed = service.delete_secret(
                arguments.platform,
                arguments.parameter,
                guild_id=arguments.guild,
            )
            print("Secret deleted." if removed else "Secret was not set.")
            return 0

        names = service.list_secret_names(guild_id=arguments.guild)
        if not names:
            print("No secrets are stored for this scope.")
            return 0
        for platform, parameters in names.items():
            print(f"{platform}: {', '.join(parameters)}")
        return 0
    except (OSError, RuntimeError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
