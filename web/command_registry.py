from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
COGS = ROOT / "cogs"


def discover_commands() -> list[dict[str, str]]:
    """Discover public slash commands directly from the bot's Cog source files."""
    commands: list[dict[str, str]] = []
    for path in sorted(COGS.glob("*.py")):
        if path.name.startswith("__"):
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        category = path.stem
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            for decorator in node.decorator_list:
                if not isinstance(decorator, ast.Call):
                    continue
                func = decorator.func
                if not (isinstance(func, ast.Attribute) and func.attr == "command"):
                    continue
                name = None
                description = ""
                for keyword in decorator.keywords:
                    if keyword.arg == "name" and isinstance(keyword.value, ast.Constant):
                        name = keyword.value.value
                    elif keyword.arg == "description" and isinstance(keyword.value, ast.Constant):
                        description = str(keyword.value.value)
                if not name:
                    continue
                commands.append({
                    "name": str(name),
                    "description": description,
                    "category": category,
                    "source": str(path.relative_to(ROOT)).replace("\\", "/"),
                })
                break
    return sorted(commands, key=lambda item: (item["category"], item["name"]))


if __name__ == "__main__":
    import json

    print(json.dumps(discover_commands(), ensure_ascii=False, indent=2))
