"""File system utilities."""

from pathlib import Path
from typing import Any

import orjson


def ensure_dir(path: Path) -> None:
    """Create directory if it doesn't exist."""
    path.mkdir(parents=True, exist_ok=True)


def save_json(data: Any, file_path: Path) -> None:
    """Save data as JSON file with proper formatting."""
    file_path.write_bytes(orjson.dumps(data, option=orjson.OPT_INDENT_2))