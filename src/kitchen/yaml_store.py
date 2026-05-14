from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class YamlStore:
    allow_unicode: bool = True
    sort_keys: bool = False
    width: int = 120

    def load(self, path: str | Path) -> dict[str, Any]:
        resolved_path = Path(path)
        with resolved_path.open("r", encoding="utf-8") as file:
            return yaml.safe_load(file) or {}

    def save(self, path: str | Path, data: dict[str, Any]) -> None:
        resolved_path = Path(path)
        resolved_path.parent.mkdir(parents=True, exist_ok=True)

        with resolved_path.open("w", encoding="utf-8") as file:
            yaml.safe_dump(
                data,
                file,
                allow_unicode=self.allow_unicode,
                sort_keys=self.sort_keys,
                width=self.width,
            )


DEFAULT_YAML_STORE = YamlStore()
