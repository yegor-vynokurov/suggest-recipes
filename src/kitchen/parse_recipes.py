from __future__ import annotations

from typing import Any

import yaml

from src.kitchen.construct import Recipe, Need
from src.kitchen.recipe_validation import validate_accept_categories


def _coerce_text(value: Any) -> str:
    if isinstance(value, str):
        return value.strip()
    return ""


def _read_localized_recipe_field(
    recipe_data: dict[str, Any],
    field: str,
    legacy_fallback_field: str | None = None,
) -> tuple[str, str]:
    value = recipe_data.get(field)
    value_uk = recipe_data.get(f"{field}_uk")

    if isinstance(value, dict):
        primary = _coerce_text(value.get("en"))
        localized_uk = _coerce_text(value.get("uk"))
    else:
        primary = _coerce_text(value)
        localized_uk = _coerce_text(value_uk)

    if legacy_fallback_field:
        legacy_value = recipe_data.get(legacy_fallback_field)
        legacy_value_uk = recipe_data.get(f"{legacy_fallback_field}_uk")

        if not primary:
            if isinstance(legacy_value, dict):
                primary = _coerce_text(legacy_value.get("en"))
            else:
                primary = _coerce_text(legacy_value)

        if not localized_uk:
            if isinstance(legacy_value, dict):
                localized_uk = _coerce_text(legacy_value.get("uk"))
            else:
                localized_uk = _coerce_text(legacy_value_uk)

    return primary, localized_uk


def load_recipes_from_yaml(path: str) -> list[Recipe]:
    with open(path, "r", encoding="utf-8") as file:
        data = yaml.safe_load(file) or {}

    validate_accept_categories(data, path)

    recipes = []

    for recipe_data in data.get("recipes", []):
        needs = []
        name, name_uk = _read_localized_recipe_field(recipe_data, "name")
        comment, comment_uk = _read_localized_recipe_field(
            recipe_data,
            "comment",
            legacy_fallback_field="note",
        )

        for item in recipe_data.get("ingredients", []):
            needs.append(
                Need(
                    item=item["item"],
                    role=item["role"],
                    amount=item.get("amount", "normal"),
                    accepts=item.get("accepts", []),
                    note=item.get("note", ""),
                )
            )

        recipes.append(
            Recipe(
                id=recipe_data["id"],
                name=name,
                ingredients=needs,
                comment=comment,
                name_uk=name_uk,
                comment_uk=comment_uk,
                kind=recipe_data.get("kind", "dish"),
                tags=recipe_data.get("tags", []),
                facets=recipe_data.get("facets", {}),
                uses_components=recipe_data.get("uses_components", []),
                component_for=recipe_data.get("component_for", []),
                missing_allowed=recipe_data.get("missing_allowed", 0),
                source_family=recipe_data.get("source_family", ""),
                source_file=recipe_data.get("source_file", ""),
            )
        )

    return recipes
