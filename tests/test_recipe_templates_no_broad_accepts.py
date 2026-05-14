from __future__ import annotations

from pathlib import Path

import yaml

from src.kitchen.recipe_validation import BROAD_ACCEPT_CATEGORIES


TEMPLATES_DIR = Path("data/recipes")
BUNDLE_PATH = TEMPLATES_DIR / "read.yaml"


def collect_broad_accept_issues(recipes: list[dict], source_name: str) -> list[str]:
    issues: list[str] = []

    for recipe in recipes:
        recipe_id = recipe.get("id", "<missing id>")
        for need in recipe.get("ingredients", []) or []:
            accepts = need.get("accepts") or []
            broad = [accepted for accepted in accepts if accepted in BROAD_ACCEPT_CATEGORIES]
            if not broad:
                continue

            issues.append(
                f"{source_name}:{recipe_id}:{need.get('item')} -> {', '.join(broad)}"
            )

    return issues


def test_recipe_templates_do_not_use_broad_accept_categories() -> None:
    issues: list[str] = []

    for path in sorted(TEMPLATES_DIR.glob("recipe_templates_*.yaml")):
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or []
        recipes = data if isinstance(data, list) else data.get("recipes", [])
        issues.extend(collect_broad_accept_issues(recipes, path.name))

    assert not issues, "Found broad accepts in recipe templates:\n" + "\n".join(issues[:20])


def test_recipe_bundle_does_not_use_broad_accept_categories() -> None:
    data = yaml.safe_load(BUNDLE_PATH.read_text(encoding="utf-8")) or {}
    recipes = data.get("recipes", []) or []
    issues = collect_broad_accept_issues(recipes, BUNDLE_PATH.name)

    assert not issues, "Found broad accepts in recipe bundle:\n" + "\n".join(issues[:20])
