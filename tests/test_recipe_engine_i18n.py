from __future__ import annotations

from src.kitchen.construct import Need, Recipe
from src.kitchen.recipe_engine import RecipeEngine


def build_test_recipe() -> Recipe:
    return Recipe(
        id="test_recipe_i18n",
        name="Test recipe",
        name_uk="\u0422\u0435\u0441\u0442\u043e\u0432\u0438\u0439 \u0440\u0435\u0446\u0435\u043f\u0442",
        comment="Serve warm",
        ingredients=[
            Need(item="milk", role="required"),
            Need(item="eggs", role="required", amount="normal"),
            Need(item="butter", role="addition", accepts=["ghee"]),
        ],
    )


def test_recipe_engine_explanations_default_to_english() -> None:
    engine = RecipeEngine(recipes=[build_test_recipe()], inventory={})

    match = engine.match_recipe_by_id(
        recipe_id="test_recipe_i18n",
        inventory={
            "eggs": "little",
            "ghee": "normal",
        },
    )

    assert match is not None
    assert match["name"] == "Test recipe"
    assert "missing: milk" in match["explanations"]
    assert "have eggs, but too little" in match["explanations"]
    assert "butter substituted by accepted item: ghee" in match["explanations"]
    assert match["comment_text"] == "Comment: Serve warm"


def test_recipe_engine_explanations_switch_to_ukrainian_templates() -> None:
    engine = RecipeEngine(recipes=[build_test_recipe()], inventory={}, lang="uk")

    match = engine.match_recipe_by_id(
        recipe_id="test_recipe_i18n",
        inventory={
            "eggs": "little",
            "ghee": "normal",
        },
    )

    assert match is not None
    assert match["name"] == "Test recipe / \u0422\u0435\u0441\u0442\u043e\u0432\u0438\u0439 \u0440\u0435\u0446\u0435\u043f\u0442"
    assert "\u043d\u0435 \u0432\u0438\u0441\u0442\u0430\u0447\u0430\u0454: \u043c\u043e\u043b\u043e\u043a\u043e" in match["explanations"]
    assert "\u0454 \u044f\u0439\u0446\u044f, \u0430\u043b\u0435 \u0437\u0430\u043c\u0430\u043b\u043e" in match["explanations"]
    assert (
        "\u043c\u0430\u0441\u043b\u043e \u0432\u0435\u0440\u0448\u043a\u043e\u0432\u0435 "
        "\u0437\u0430\u043c\u0456\u043d\u0435\u043d\u043e \u0434\u043e\u043f\u0443\u0441\u0442\u0438\u043c\u0438\u043c "
        "\u0456\u043d\u0433\u0440\u0435\u0434\u0456\u0454\u043d\u0442\u043e\u043c: \u0433\u0445\u0456 / "
        "\u0442\u043e\u043f\u043b\u0435\u043d\u0430 \u043e\u043b\u0456\u044f"
    ) in match["explanations"]
    assert match["comment_text"] == "\u041a\u043e\u043c\u0435\u043d\u0442\u0430\u0440: Serve warm"


def test_recipe_engine_filter_explanations_use_localized_facet_labels() -> None:
    recipe = Recipe(
        id="facet_recipe_i18n",
        name="Facet recipe",
        ingredients=[Need(item="milk", role="required")],
        facets={
            "cuisine": ["ukrainian"],
            "dish_type": ["breakfast"],
            "time": "under_30",
            "method": ["fry"],
        },
    )
    engine = RecipeEngine(recipes=[recipe], inventory={}, lang="uk")

    match = engine.match_recipe(
        recipe=recipe,
        inventory={"milk": "normal"},
        filters=[("cuisine", "ukrainian"), ("time", "under_30"), ("method", "fry")],
        prefer_categories=[],
    )

    assert (
        "\u043f\u0456\u0434\u0445\u043e\u0434\u0438\u0442\u044c \u043f\u0456\u0434 \u0444\u0456\u043b\u044c\u0442\u0440: "
        "\u043a\u0443\u0445\u043d\u044f=\u0423\u043a\u0440\u0430\u0457\u043d\u0441\u044c\u043a\u0430 \u043a\u0443\u0445\u043d\u044f"
    ) in match["explanations"]
    assert (
        "\u043f\u0456\u0434\u0445\u043e\u0434\u0438\u0442\u044c \u043f\u0456\u0434 \u0444\u0456\u043b\u044c\u0442\u0440: "
        "\u0447\u0430\u0441=\u0434\u043e 30 \u0445\u0432\u0438\u043b\u0438\u043d"
    ) in match["explanations"]
    assert (
        "\u043f\u0456\u0434\u0445\u043e\u0434\u0438\u0442\u044c \u043f\u0456\u0434 \u0444\u0456\u043b\u044c\u0442\u0440: "
        "\u0441\u043f\u043e\u0441\u0456\u0431=\u0421\u043c\u0430\u0436\u0438\u0442\u0438"
    ) in match["explanations"]
