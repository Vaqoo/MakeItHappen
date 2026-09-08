from __future__ import annotations

import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
COGS = ROOT / "cogs"


def _literal(node: ast.AST, default: object = None) -> object:
    try:
        return ast.literal_eval(node)
    except (ValueError, TypeError):
        return default


def discover_commands() -> list[dict[str, str]]:
    """Discover slash commands directly from the bot's Cog source files."""
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
                    if keyword.arg == "name":
                        value = _literal(keyword.value)
                        if isinstance(value, str):
                            name = value
                    elif keyword.arg == "description":
                        value = _literal(keyword.value)
                        if value is not None:
                            description = str(value)
                if not name:
                    name = node.name
                commands.append({
                    "name": str(name),
                    "description": description,
                    "category": category,
                    "source": str(path.relative_to(ROOT)).replace("\\", "/"),
                })
                break
    return sorted(commands, key=lambda item: (item["category"], item["name"]))


def get_command_manifest() -> dict[str, object]:
    commands = discover_commands()
    return {
        "source": "cogs/*.py",
        "generated_by": "web/command_registry.py",
        "count": len(commands),
        "commands": commands,
    }


if __name__ == "__main__":
    print(json.dumps(get_command_manifest(), ensure_ascii=False, indent=2))
