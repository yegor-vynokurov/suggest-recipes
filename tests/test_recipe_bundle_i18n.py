from __future__ import annotations

from pathlib import Path

import yaml

from src.kitchen.recipe_collection import build_recipe_bundle


def test_build_recipe_bundle_preserves_localized_recipe_fields(tmp_path: Path) -> None:
    recipes_dir = tmp_path / "recipes"
    recipes_dir.mkdir()
    source_path = recipes_dir / "recipe_templates_test_v0_1.yaml"
    source_path.write_text(
        yaml.safe_dump(
            {
                "metadata": {
                    "version": "0.1",
                    "kind": "recipes",
                    "cuisines": {
                        "test": "Test cuisine",
                    },
                },
                "recipes": [
                    {
                        "id": "localized_recipe",
                        "name": "English recipe",
                        "name_uk": "Український рецепт",
                        "comment": "English comment",
                        "comment_uk": "Український коментар",
                        "facets": {
                            "cuisine": ["test"],
                        },
                        "ingredients": [
                            {"item": "water", "role": "required"},
                        ],
                    }
                ],
            },
            allow_unicode=True,
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    output_path = tmp_path / "read.yaml"

    result = build_recipe_bundle(
        cuisines="test",
        recipes_dir=recipes_dir,
        output_path=output_path,
        lang="en",
    )
    bundle = yaml.safe_load(output_path.read_text(encoding="utf-8")) or {}
    [recipe] = bundle["recipes"]

    assert result["recipe_count"] == 1
    assert recipe["name"] == "English recipe"
    assert recipe["name_uk"] == "Український рецепт"
    assert recipe["comment"] == "English comment"
    assert recipe["comment_uk"] == "Український коментар"
    assert recipe["source_file"] == source_path.name
