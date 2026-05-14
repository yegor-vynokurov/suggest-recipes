from __future__ import annotations

import src.kitchen.constants as cnst
from src.kitchen.recipe_engine import RecipeEngine


def test_distance_to_category_uses_real_graph_depth() -> None:
    assert cnst.distance_to_category("fermented_dairy", "dairy") == 1
    assert cnst.distance_to_category("milk_like", "protein") == 2
    assert cnst.distance_to_category("milk", "dairy") == 0
    assert cnst.distance_to_category("milk", "protein") == 1
    assert cnst.distance_to_category("fruit_preserve", "sauce") == 1
    assert cnst.distance_to_category("offal", "meat") == 1
    assert cnst.distance_to_category("water", "dairy") is None


def test_is_descendant_works_for_categories_and_ingredients() -> None:
    assert cnst.is_descendant("fermented_dairy", "dairy") is True
    assert cnst.is_descendant("milk", "protein") is True
    assert cnst.is_descendant("plant_oil", "animal_fat") is False


def test_shared_parents_finds_common_ancestors() -> None:
    shared = cnst.shared_parents("olive_oil", "smalec")

    assert "fat" in shared
    assert "ingredient" in shared
    assert "plant_oil" not in shared
    assert "animal_fat" not in shared


def test_recipe_engine_collect_category_fallbacks_uses_catalog_distance() -> None:
    engine = RecipeEngine(recipes=[], inventory={})

    assert engine.collect_category_fallbacks("fermented_dairy") == [
        ("fermented_dairy", 0),
        ("dairy", 1),
        ("protein", 2),
        ("ingredient", 3),
    ]


def test_runtime_catalog_includes_new_structural_subcategories() -> None:
    expected_parents = {
        "meat_on_bone": ["meat_piece"],
        "prepared_meat": ["meat_product"],
        "fish_product": ["fish"],
        "marinated_fish": ["fish_product"],
        "salted_fish": ["fish_product"],
        "dried_fish": ["fish_product"],
        "smoked_fish": ["fish_product"],
        "crustacean": ["seafood"],
        "flatbread": ["bread_base"],
        "berry": ["fresh_fruit"],
        "pickled_vegetable": ["vegetable"],
        "fruit_preserve": ["sauce", "sweetener"],
    }

    for category_id, parents in expected_parents.items():
        assert cnst.CATEGORIES[category_id]["parents"] == parents

    assert cnst.is_descendant("sausage_product", "prepared_meat") is True


def test_runtime_catalog_uses_new_subcategories_for_moved_items() -> None:
    assert cnst.is_descendant("langoustine", "crustacean") is True
    assert cnst.is_descendant("shrimp", "crustacean") is True
    assert cnst.is_descendant("smoked_salmon", "smoked_fish") is True
    assert cnst.is_descendant("salted_herring", "fish_product") is True
    assert cnst.is_descendant("salami", "prepared_meat") is True
    assert cnst.is_descendant("beef_bones", "meat_on_bone") is True
    assert cnst.is_descendant("lefse", "flatbread") is True
    assert cnst.is_descendant("raspberry", "berry") is True
    assert cnst.is_descendant("pickled_cucumber", "pickled_vegetable") is True
    assert cnst.is_descendant("apricot_jam", "fruit_preserve") is True
