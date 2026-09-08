from __future__ import annotations

import json
from pathlib import Path

from command_registry import get_command_manifest

OUT = Path(__file__).resolve().parent / "commands.json"

if __name__ == "__main__":
    OUT.write_text(json.dumps(get_command_manifest(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {OUT} with {get_command_manifest()['count']} commands.")
