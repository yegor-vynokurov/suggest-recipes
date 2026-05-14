from __future__ import annotations

import pytest

from src.kitchen.constants import ALWAYS_AVAILABLE_INVENTORY, ING_PATH
from src.kitchen.parse_recipes import load_recipes_from_yaml
from src.kitchen.recipe_engine import RecipeEngine


def find_match_item(match: dict, required_id: str) -> dict:
    for item in match["matches"]:
        if item["required_id"] == required_id:
            return item

    raise KeyError(f"required_id={required_id} not found in match for {match['recipe_id']}")


@pytest.fixture(scope="module")
def engine() -> RecipeEngine:
    recipes = load_recipes_from_yaml(str(ING_PATH))
    return RecipeEngine(recipes=recipes, inventory={})


def test_majgombocleves_does_not_replace_liver_with_chicken_fillet(
    engine: RecipeEngine,
) -> None:
    match = engine.match_recipe_by_id(
        recipe_id="hungarian_majgombocleves",
        inventory={
            **ALWAYS_AVAILABLE_INVENTORY,
            "chicken_fillet": "normal",
            "broth": "normal",
            "flour": "little",
            "eggs": "little",
            "parsley": "little",
            "black_pepper": "spice",
        },
    )

    assert match is not None

    liver = find_match_item(match, "liver")

    assert liver["match_type"] == "missing"
    assert liver["used_id"] is None
    assert match["status"] == "missing_main"
    assert "liver substituted by category: chicken fillet" not in match["explanations"]


def test_majgombocleves_can_use_minced_meat_as_fallback(engine: RecipeEngine) -> None:
    match = engine.match_recipe_by_id(
        recipe_id="hungarian_majgombocleves",
        inventory={
            **ALWAYS_AVAILABLE_INVENTORY,
            "ground_beef": "normal",
            "breadcrumbs": "normal",
            "eggs": "little",
            "broth_meat": "normal",
            "carrot": "little",
            "onion": "little",
        },
    )

    assert match is not None

    liver = find_match_item(match, "liver")

    assert liver["match_type"] == "accepted_category_match"
    assert liver["used_id"] == "ground_beef"
    assert liver["source_id"] == "minced_meat"


def test_hallongrottor_does_not_replace_raspberry_jam_with_mayonnaise(
    engine: RecipeEngine,
) -> None:
    match = engine.match_recipe_by_id(
        recipe_id="scandinavian_hallongrottor",
        inventory={
            **ALWAYS_AVAILABLE_INVENTORY,
            "flour": "normal",
            "butter": "normal",
            "sugar": "normal",
            "mayonnaise": "little",
        },
    )

    assert match is not None

    raspberry_jam = find_match_item(match, "raspberry_jam")

    assert raspberry_jam["match_type"] == "missing"
    assert raspberry_jam["used_id"] is None
    assert match["status"] == "missing_one"
    assert "raspberry jam substituted by category: mayonnaise" not in match["explanations"]


def test_hallongrottor_can_use_other_fruit_preserve(engine: RecipeEngine) -> None:
    match = engine.match_recipe_by_id(
        recipe_id="scandinavian_hallongrottor",
        inventory={
            **ALWAYS_AVAILABLE_INVENTORY,
            "flour": "normal",
            "butter": "normal",
            "sugar": "normal",
            "plum_jam": "normal",
        },
    )

    assert match is not None

    raspberry_jam = find_match_item(match, "raspberry_jam")

    assert raspberry_jam["match_type"] == "accepted_category_match"
    assert raspberry_jam["used_id"] == "plum_jam"
    assert raspberry_jam["source_id"] == "fruit_preserve"
