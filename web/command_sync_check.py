from __future__ import annotations

import json
from pathlib import Path

from command_registry import get_command_manifest

ROOT = Path(__file__).resolve().parent
MANIFEST = ROOT / "commands.json"


def main() -> None:
    expected = get_command_manifest()
    if not MANIFEST.exists():
        raise SystemExit("web/commands.json is missing. Run: python web/sync_commands.py")
    actual = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if actual != expected:
        raise SystemExit(
            "web/commands.json is out of date. Run: python web/sync_commands.py and commit the result."
        )
    print(f"Command registry is up to date ({expected['count']} commands).")


if __name__ == "__main__":
    main()
