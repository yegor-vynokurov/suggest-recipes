from __future__ import annotations

import re
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
RECIPES_DIR = ROOT / "data" / "recipes"
CYRILLIC_RE = re.compile(r"[\u0400-\u04FF]")


def iter_source_recipes() -> list[tuple[Path, dict]]:
    result: list[tuple[Path, dict]] = []

    for path in sorted(RECIPES_DIR.glob("recipe_templates_*.yaml")):
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}

        for recipe in data.get("recipes", []) or []:
            result.append((path, recipe))

    return result


def test_recipe_templates_use_localized_name_and_comment_fields() -> None:
    recipes = iter_source_recipes()

    assert recipes

    for path, recipe in recipes:
        recipe_id = recipe["id"]
        name = (recipe.get("name") or "").strip()
        name_uk = (recipe.get("name_uk") or "").strip()
        comment = (recipe.get("comment") or "").strip()
        comment_uk = (recipe.get("comment_uk") or "").strip()
        note = (recipe.get("note") or "").strip()

        assert name, f"{path.name}:{recipe_id} is missing English name"
        assert name_uk, f"{path.name}:{recipe_id} is missing Ukrainian name"
        assert " / " not in name, f"{path.name}:{recipe_id} still uses hybrid name: {name!r}"
        assert " / " not in name_uk, f"{path.name}:{recipe_id} still uses hybrid Ukrainian name: {name_uk!r}"
        assert not CYRILLIC_RE.search(name), f"{path.name}:{recipe_id} English name still contains Cyrillic: {name!r}"
        assert not note, f"{path.name}:{recipe_id} still uses legacy note field"

        if comment:
            assert comment_uk, f"{path.name}:{recipe_id} is missing Ukrainian comment"
            assert not CYRILLIC_RE.search(comment), (
                f"{path.name}:{recipe_id} English comment still contains Cyrillic: {comment!r}"
            )
