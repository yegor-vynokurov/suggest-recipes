from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
INGREDIENTS_PATH = ROOT / "data" / "inventory" / "ingredients" / "ingredients_vegetables_mushrooms_fruits.yaml"
INGREDIENTS_DIR = ROOT / "data" / "inventory" / "ingredients"
RECIPES_DIR = ROOT / "data" / "recipes"
LEGACY_IDS = {"mushrooms", "olives", "raw_onion"}


def iter_source_ingredient_ids() -> Iterable[str]:
    for path in sorted(INGREDIENTS_DIR.glob("ingredients_*.yaml")):
        if path.name == "ingredients_all_merged.yaml":
            continue

        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        ingredients = data.get("ingredients", {}) or {}
        for ingredient_id in ingredients:
            yield ingredient_id


def test_duplicate_ingredient_ids_are_removed_from_catalog_and_moved_to_aliases() -> None:
    data = yaml.safe_load(INGREDIENTS_PATH.read_text(encoding="utf-8")) or {}
    ingredients = data.get("ingredients", {}) or {}

    for duplicate_id in LEGACY_IDS:
        assert duplicate_id not in ingredients

    assert "mushrooms" in (ingredients["mushroom"].get("aliases", []) or [])
    assert "olives" in (ingredients["olive"].get("aliases", []) or [])
    assert "raw onion" in (ingredients["onion"].get("aliases", []) or [])


def test_recipe_templates_use_canonical_ingredient_ids() -> None:
    assert sorted(RECIPES_DIR.glob("recipe_templates_*.yaml"))

    for path in sorted(RECIPES_DIR.glob("recipe_templates_*.yaml")):
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}

        for recipe in data.get("recipes", []) or []:
            for ingredient in recipe.get("ingredients", []) or []:
                assert ingredient.get("item") not in LEGACY_IDS, (
                    f"{path.name}:{recipe['id']} still uses legacy item id {ingredient.get('item')!r}"
                )
                accepts = ingredient.get("accepts", []) or []
                assert not LEGACY_IDS.intersection(accepts), (
                    f"{path.name}:{recipe['id']} still uses legacy accepts ids {accepts!r}"
                )


def test_source_catalog_has_no_more_obvious_duplicate_style_ids() -> None:
    ingredient_ids = set(iter_source_ingredient_ids())
    duplicate_style_pairs: list[tuple[str, str]] = []

    for ingredient_id in sorted(ingredient_ids):
        if ingredient_id.startswith("raw_"):
            base_id = ingredient_id[4:]
            if base_id in ingredient_ids:
                duplicate_style_pairs.append((ingredient_id, base_id))

        if ingredient_id.endswith("es"):
            singular_id = ingredient_id[:-2]
            if singular_id in ingredient_ids:
                duplicate_style_pairs.append((ingredient_id, singular_id))
        elif ingredient_id.endswith("s"):
            singular_id = ingredient_id[:-1]
            if singular_id in ingredient_ids:
                duplicate_style_pairs.append((ingredient_id, singular_id))

    assert not duplicate_style_pairs, (
        "Found more obvious duplicate-style ingredient ids; keep only one canonical id "
        f"and move the other form into aliases: {duplicate_style_pairs!r}"
    )
