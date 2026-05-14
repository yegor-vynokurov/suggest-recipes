from __future__ import annotations

from src.kitchen.ingredient_catalog import IngredientCatalog


def make_catalog() -> IngredientCatalog:
    return IngredientCatalog(
        categories={
            "dairy": {
                "name": "dairy",
                "name_uk": "молочне",
                "parents": ["protein"],
            },
            "protein": {
                "name": {"en": "protein", "uk": "білок"},
                "parents": ["ingredient"],
            },
        },
        ingredients={
            "milk": {
                "name": "milk",
                "name_uk": "молоко",
                "comment": "whole milk",
                "comment_uk": "цільне молоко",
                "groups": ["dairy"],
            },
            "cream": {
                "name": {"en": "cream", "uk": "вершки"},
                "comment": {"en": "heavy cream", "uk": "жирні вершки"},
                "groups": ["dairy"],
            },
            "mystery_item": {
                "name_uk": "таємничий інгредієнт",
                "groups": ["protein"],
            },
        },
    )


def test_item_name_uses_selected_language_with_en_fallback() -> None:
    catalog = make_catalog()

    assert catalog.item_name("milk", "en") == "milk"
    assert catalog.item_name("milk", "uk") == "молоко"
    assert catalog.item_name("cream", "en") == "cream"
    assert catalog.item_name("cream", "uk") == "вершки"


def test_item_name_for_uk_falls_back_to_english_then_item_id() -> None:
    catalog = make_catalog()

    assert catalog.item_name("mystery_item", "uk") == "таємничий інгредієнт"
    assert catalog.item_name("mystery_item", "en") == "mystery_item"
    assert catalog.item_name("unknown_item", "uk") == "unknown_item"


def test_category_name_supports_string_and_dict_translations() -> None:
    catalog = make_catalog()

    assert catalog.category_name("dairy", "en") == "dairy"
    assert catalog.category_name("dairy", "uk") == "молочне"
    assert catalog.category_name("protein", "en") == "protein"
    assert catalog.category_name("protein", "uk") == "білок"
    assert catalog.category_name("unknown_category", "uk") == "unknown_category"


def test_item_comment_uses_uk_then_en_then_item_id() -> None:
    catalog = make_catalog()

    assert catalog.item_comment("milk", "uk") == "цільне молоко"
    assert catalog.item_comment("milk", "en") == "whole milk"
    assert catalog.item_comment("cream", "uk") == "жирні вершки"
    assert catalog.item_comment("mystery_item", "uk") == "mystery_item"
    assert catalog.item_comment("unknown_item", "uk") == "unknown_item"
