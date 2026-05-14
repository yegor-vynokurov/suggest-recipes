from __future__ import annotations

from pathlib import Path

import yaml

from src.kitchen.constants import ING_PATH
from src.kitchen.parse_recipes import load_recipes_from_yaml


def test_load_recipes_from_yaml_keeps_recipe_metadata_fields() -> None:
    recipes = load_recipes_from_yaml(str(ING_PATH))
    recipes_by_id = {recipe.id: recipe for recipe in recipes}

    mayonnaise = recipes_by_id["french_mayonnaise_maison"]
    deruny = recipes_by_id["ukrainian_deruny"]

    assert mayonnaise.missing_allowed == 1
    assert mayonnaise.source_family == "french:mayonnaise_maison"
    assert mayonnaise.source_file == "recipe_templates_french_v0_1.yaml"

    assert deruny.missing_allowed == 1
    assert deruny.source_family == "ukrainian:deruny"
    assert deruny.source_file == "recipe_templates_ukrainian_v0_1.yaml"


def test_load_recipes_from_yaml_keeps_ukrainian_serving_roles_soft() -> None:
    recipes = load_recipes_from_yaml(str(ING_PATH))
    recipes_by_id = {recipe.id: recipe for recipe in recipes}

    expected_roles = {
        ("ukrainian_cold_borscht_kholodnyk", "sour_cream"): "addition",
        ("ukrainian_deruny_meat", "sour_cream"): "addition",
        ("ukrainian_salad_vinaigrette", "plant_oil"): "addition",
        ("ukrainian_salad_cabbage_peas_sourcream", "sour_cream"): "addition",
        ("ukrainian_cabbage_carrot_salad", "plant_oil"): "addition",
        ("ukrainian_cucumber_sourcream_salad", "sour_cream"): "addition",
        ("ukrainian_tomato_cucumber_salad", "plant_oil"): "addition",
        ("ukrainian_salad_shuba", "mayonnaise"): "required",
    }

    for (recipe_id, item_id), expected_role in expected_roles.items():
        recipe = recipes_by_id[recipe_id]
        need = next(ingredient for ingredient in recipe.ingredients if ingredient.item == item_id)
        assert need.role == expected_role


def test_load_recipes_from_yaml_reads_new_localized_recipe_fields(tmp_path: Path) -> None:
    path = tmp_path / "recipes.yaml"
    path.write_text(
        yaml.safe_dump(
            {
                "recipes": [
                    {
                        "id": "localized_recipe",
                        "name": "English recipe",
                        "name_uk": "Український рецепт",
                        "comment": "English comment",
                        "comment_uk": "Український коментар",
                        "ingredients": [
                            {"item": "eggs", "role": "main"},
                        ],
                    }
                ]
            },
            allow_unicode=True,
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    [recipe] = load_recipes_from_yaml(str(path))

    assert recipe.name == "English recipe"
    assert recipe.name_uk == "Український рецепт"
    assert recipe.comment == "English comment"
    assert recipe.comment_uk == "Український коментар"


def test_load_recipes_from_yaml_keeps_backward_compatibility_with_old_fields(
    tmp_path: Path,
) -> None:
    path = tmp_path / "recipes.yaml"
    path.write_text(
        yaml.safe_dump(
            {
                "recipes": [
                    {
                        "id": "legacy_recipe",
                        "name": "Legacy recipe / старый рецепт",
                        "note": "Legacy note",
                        "ingredients": [
                            {"item": "eggs", "role": "main"},
                        ],
                    }
                ]
            },
            allow_unicode=True,
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    [recipe] = load_recipes_from_yaml(str(path))

    assert recipe.name == "Legacy recipe / старый рецепт"
    assert recipe.name_uk == ""
    assert recipe.comment == "Legacy note"
    assert recipe.comment_uk == ""
