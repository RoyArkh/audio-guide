"""Save a database dump read from stdin, e.g. pg_dump ... | python -m app.backup backups/2026-11-08.dump
Run nightly on the server by scripts/backup.sh."""

import sys

from app.storage import get_storage


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit("Usage: python -m app.backup <key>")
    key = sys.argv[1]

    data = sys.stdin.buffer.read()
    if not data:
        sys.exit("No backup data on stdin: did pg_dump fail?")

    get_storage().save(key, data)
    print(f"Saved {key} ({len(data) // 1024} KB)")


if __name__ == "__main__":
    main()
