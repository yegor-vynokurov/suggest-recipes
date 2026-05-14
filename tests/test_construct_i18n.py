from __future__ import annotations

from src.kitchen.construct import Need, Recipe


def test_recipe_keeps_english_fields_as_primary_and_ukrainian_as_optional() -> None:
    recipe = Recipe(
        id="test_recipe",
        name="Test recipe",
        ingredients=[Need("eggs", "main")],
        comment="English comment",
    )

    assert recipe.name == "Test recipe"
    assert recipe.comment == "English comment"
    assert recipe.name_uk == ""
    assert recipe.comment_uk == ""


def test_recipe_allows_explicit_ukrainian_localized_fields() -> None:
    recipe = Recipe(
        id="test_recipe",
        name="Test recipe",
        ingredients=[Need("eggs", "main")],
        comment="English comment",
        name_uk="Тестовий рецепт",
        comment_uk="Український коментар",
    )

    assert recipe.name == "Test recipe"
    assert recipe.comment == "English comment"
    assert recipe.name_uk == "Тестовий рецепт"
    assert recipe.comment_uk == "Український коментар"


def test_recipe_old_positional_constructor_shape_still_works() -> None:
    recipe = Recipe(
        "legacy_recipe",
        "Legacy recipe",
        [Need("eggs", "main")],
        "Legacy comment",
    )

    assert recipe.name == "Legacy recipe"
    assert recipe.comment == "Legacy comment"
    assert recipe.name_uk == ""
    assert recipe.comment_uk == ""
