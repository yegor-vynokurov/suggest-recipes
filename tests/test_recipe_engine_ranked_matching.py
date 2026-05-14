from __future__ import annotations

import src.kitchen.constants as cnst
from src.kitchen.construct import Need
from src.kitchen.recipe_engine import RecipeEngine


def make_engine() -> RecipeEngine:
    return RecipeEngine(recipes=[], inventory={})


def test_match_need_prefers_explicit_accept_item_before_accept_category() -> None:
    engine = make_engine()
    need = Need(
        item="buttermilk",
        role="required",
        accepts=["milk_like", "milk"],
    )

    match = engine.match_need(need, inventory={"milk": "normal"})

    assert match["used_id"] == "milk"
    assert match["match_type"] == "accepted_variant"
    assert match["source_kind"] == "ingredient"
    assert match["source_relation"] == "accepts"


def test_match_need_can_fallback_to_parent_category_with_penalty() -> None:
    engine = make_engine()
    need = Need(
        item="buttermilk",
        role="required",
        accepts=["fermented_dairy"],
    )

    match = engine.match_need(need, inventory={"milk": "normal"})

    assert match["used_id"] == "milk"
    assert match["match_type"] == "accepted_category_match"
    assert match["source_id"] == "dairy"
    assert match["source_kind"] == "parent_category"
    assert match["source_depth"] == 1
    assert match["score"] < round(
        cnst.ROLE_WEIGHT["required"] * cnst.CATEGORY_MATCH_SIMILARITY,
        2,
    )


def test_accept_category_match_keeps_additional_mustard_facet() -> None:
    engine = make_engine()
    need = Need(
        item="mustard",
        role="required",
        amount="little",
        accepts=["sauce"],
    )

    match = engine.match_need(need, inventory={"mayonnaise": "normal"})

    assert match["match_type"] == "missing"
    assert match["used_id"] is None


def test_accept_category_match_keeps_additional_salo_facet() -> None:
    engine = make_engine()
    need = Need(
        item="salo",
        role="required",
        accepts=["fat"],
    )

    match = engine.match_need(need, inventory={"butter": "normal"})

    assert match["match_type"] == "missing"
    assert match["used_id"] is None


def test_accept_category_match_still_allows_plain_butter_to_use_fat_family() -> None:
    engine = make_engine()
    need = Need(
        item="butter",
        role="required",
        accepts=["fat"],
    )

    match = engine.match_need(need, inventory={"olive_oil": "normal"})

    assert match["match_type"] == "accepted_category_match"
    assert match["used_id"] == "olive_oil"


def test_match_need_does_not_fallback_from_offal_to_generic_meat() -> None:
    engine = make_engine()
    need = Need(
        item="liver",
        role="main",
        accepts=["offal"],
    )

    match = engine.match_need(need, inventory={"chicken_fillet": "normal"})

    assert match["match_type"] == "missing"
    assert match["used_id"] is None


def test_match_need_can_use_minced_meat_without_falling_back_to_fillet() -> None:
    engine = make_engine()
    need = Need(
        item="liver",
        role="main",
        accepts=["minced_meat"],
    )

    match = engine.match_need(need, inventory={"ground_beef": "normal"})

    assert match["match_type"] == "accepted_category_match"
    assert match["used_id"] == "ground_beef"
    assert match["source_id"] == "minced_meat"


def test_match_need_does_not_fallback_from_fruit_preserve_to_generic_sauce() -> None:
    engine = make_engine()
    need = Need(
        item="raspberry_jam",
        role="required",
        accepts=["fruit_preserve"],
    )

    match = engine.match_need(need, inventory={"mayonnaise": "normal"})

    assert match["match_type"] == "missing"
    assert match["used_id"] is None
