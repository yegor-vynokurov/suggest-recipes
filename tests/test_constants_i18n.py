from __future__ import annotations

import src.kitchen.constants as cnst


def test_default_item_and_category_display_names_are_english_canonical() -> None:
    assert cnst.item_name("eggs") == "eggs"
    assert cnst.item_name("plant_oil") == "plant oil"
    assert cnst.category_name("dairy") == "dairy"
    assert cnst.item_name("unknown_item") == "unknown item"


def test_recipe_facets_default_to_english_labels() -> None:
    assert cnst.RECIPE_FACETS["cuisine"]["ukrainian"] == "Ukrainian cuisine"
    assert cnst.RECIPE_FACETS["dish_type"]["main"] == "Main course"
    assert cnst.RECIPE_FACETS["time"]["under_30"] == "under 30 minutes"
    assert cnst.RECIPE_FACETS["method"]["fry"] == "Fry"


def test_recipe_facet_labels_can_be_localized_to_ukrainian() -> None:
    assert cnst.facet_label("cuisine", "ukrainian", "uk") == "Українська кухня"
    assert cnst.facet_label("dish_type", "main", "uk") == "Основна страва"
    assert cnst.facet_label("time", "under_30", "uk") == "до 30 хвилин"
    assert cnst.facet_label("method", "fry", "uk") == "Смажити"


def test_recipe_facet_helpers_fall_back_safely() -> None:
    assert cnst.facet_label("time", "under_60", "ru") == "under 1 hour"
    assert cnst.facet_label("unknown_facet", "custom_value", "uk") == "custom value"
    assert cnst.facet_labels("time", "uk")["over_60"] == "понад 1 годину"


def test_filter_aliases_support_english_and_ukrainian_dish_type_shortcuts() -> None:
    assert cnst.FILTER_ALIASES["soup"] == ("dish_type", "soup")
    assert cnst.FILTER_ALIASES["main"] == ("dish_type", "main")
    assert cnst.FILTER_ALIASES["salad"] == ("dish_type", "salad")
    assert cnst.FILTER_ALIASES["breakfast"] == ("dish_type", "breakfast")
    assert cnst.FILTER_ALIASES["перша_страва"] == ("dish_type", "soup")
    assert cnst.FILTER_ALIASES["основна_страва"] == ("dish_type", "main")
    assert cnst.FILTER_ALIASES["випічка"] == ("dish_type", "bread")
