from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from src.kitchen.recipe_collection import (
    bootstrap_lang_from_argv,
    build_parser,
    build_recipe_bundle,
    copy_single_recipe_file,
)


ROOT = Path(__file__).resolve().parents[1]


def run_recipe_collection(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "src.kitchen.recipe_collection",
            *args,
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


def write_recipe_template(path: Path, cuisine_id: str = "test") -> None:
    data = {
        "metadata": {
            "version": "0.1",
            "kind": "recipes",
            "cuisines": {
                cuisine_id: f"{cuisine_id.title()} cuisine",
            },
        },
        "recipes": [
            {
                "id": "test_recipe",
                "name": "Test recipe",
                "facets": {
                    "cuisine": [cuisine_id],
                },
                "ingredients": [
                    {
                        "item": "water",
                        "role": "required",
                    }
                ],
            }
        ],
    }
    path.write_text(
        yaml.safe_dump(data, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )


def test_recipe_collection_bootstrap_lang_detects_cli_flag() -> None:
    assert bootstrap_lang_from_argv(["--lang", "uk", "list"]) == "uk"
    assert bootstrap_lang_from_argv(["build", "--lang=uk"]) == "uk"
    assert bootstrap_lang_from_argv(["list"]) == "en"


def test_recipe_collection_build_parser_localizes_help_for_ukrainian() -> None:
    parser = build_parser(lang="uk")

    help_text = parser.format_help()

    assert "Зібрати data/recipes/read.yaml з файлів рецептів для вибраної кухні." in help_text
    assert "Мова CLI: en (типово) або uk." in help_text
    assert "Показати кухні, доступні в data/recipes." in help_text


def test_build_recipe_bundle_localizes_missing_dir_error() -> None:
    with pytest.raises(FileNotFoundError, match="Теку рецептів не знайдено"):
        build_recipe_bundle(
            cuisines="test",
            recipes_dir=Path("missing-recipes-dir"),
            output_path=Path("unused.yaml"),
            lang="uk",
        )


def test_copy_single_recipe_file_localizes_invalid_cuisine_error() -> None:
    with pytest.raises(ValueError, match="copy_single_recipe_file працює лише для однієї конкретної кухні"):
        copy_single_recipe_file("all", lang="uk")


def test_recipe_collection_list_cli_localizes_empty_output(tmp_path: Path) -> None:
    result = run_recipe_collection("list", "--recipes-dir", str(tmp_path), "--lang", "uk")

    assert result.returncode == 0, result.stderr
    assert "Кухні не знайдено." in result.stdout


def test_recipe_collection_build_cli_localizes_summary_in_english(tmp_path: Path) -> None:
    recipes_dir = tmp_path / "recipes"
    recipes_dir.mkdir()
    write_recipe_template(recipes_dir / "recipe_templates_test_v0_1.yaml")
    output_path = tmp_path / "read.yaml"

    result = run_recipe_collection(
        "build",
        "--recipes-dir",
        str(recipes_dir),
        "--cuisine",
        "test",
        "--output",
        str(output_path),
        "--lang",
        "en",
    )

    assert result.returncode == 0, result.stderr
    assert "Recipe bundle built." in result.stdout
    assert "Cuisines: test" in result.stdout
    assert "Recipes: 1" in result.stdout
    assert "Sources:" in result.stdout
    assert output_path.exists()


def test_recipe_collection_list_cli_uses_localized_cuisine_labels_without_file_names(
    tmp_path: Path,
) -> None:
    recipes_dir = tmp_path / "recipes"
    recipes_dir.mkdir()
    write_recipe_template(recipes_dir / "recipe_templates_ukrainian_v0_1.yaml", cuisine_id="ukrainian")

    result = run_recipe_collection("list", "--recipes-dir", str(recipes_dir), "--lang", "uk")

    assert result.returncode == 0, result.stderr
    assert "Доступні кухні:" in result.stdout
    assert "- Українська кухня" in result.stdout
    assert "recipe_templates_ukrainian_v0_1.yaml" not in result.stdout


def test_recipe_collection_list_available_cuisines_uses_existing_files_not_nested_facets(
    tmp_path: Path,
) -> None:
    recipes_dir = tmp_path / "recipes"
    recipes_dir.mkdir()
    (recipes_dir / "recipe_templates_scandinavian_v0_1.yaml").write_text(
        yaml.safe_dump(
            {
                "metadata": {
                    "version": "0.1",
                    "kind": "recipes",
                    "cuisines": {
                        "scandinavian": "Scandinavian cuisine",
                        "norwegian": "Norwegian cuisine",
                        "swedish": "Swedish cuisine",
                    },
                },
                "recipes": [
                    {
                        "id": "test_recipe",
                        "name": "Test recipe",
                        "facets": {
                            "cuisine": ["scandinavian", "norwegian", "swedish"],
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

    result = run_recipe_collection("list", "--recipes-dir", str(recipes_dir), "--lang", "en")

    assert result.returncode == 0, result.stderr
    assert "Available cuisines:" in result.stdout
    assert "- Scandinavian cuisine" in result.stdout
    assert "Norwegian" not in result.stdout
    assert "Swedish" not in result.stdout


def test_recipe_collection_build_cli_uses_localized_cuisine_summary(tmp_path: Path) -> None:
    recipes_dir = tmp_path / "recipes"
    recipes_dir.mkdir()
    write_recipe_template(recipes_dir / "recipe_templates_ukrainian_v0_1.yaml", cuisine_id="ukrainian")
    output_path = tmp_path / "read.yaml"

    result = run_recipe_collection(
        "build",
        "--recipes-dir",
        str(recipes_dir),
        "--cuisine",
        "ukrainian",
        "--output",
        str(output_path),
        "--lang",
        "uk",
    )

    assert result.returncode == 0, result.stderr
    assert "Пакет рецептів зібрано." in result.stdout
    assert "Кухні: Українська кухня" in result.stdout
