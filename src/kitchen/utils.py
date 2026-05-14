from __future__ import annotations

from pathlib import Path
from typing import Any

from .yaml_store import DEFAULT_YAML_STORE


def load_yaml(path: str | Path) -> dict[str, Any]:
    return DEFAULT_YAML_STORE.load(path)
