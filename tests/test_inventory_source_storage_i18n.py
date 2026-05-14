from __future__ import annotations

from pathlib import Path

import yaml

from src.kitchen import constants as cnst
from src.kitchen.inventory_source import InventorySource


EGGS_UK = "\u044f\u0439\u0446\u044f"


def write_recipe_yaml(path: Path) -> None:
    data = {
        "recipes": [
            {
                "id": "test_recipe",
                "name": "Test recipe",
                "ingredients": [
                    {"item": "eggs", "role": "main", "amount": "normal"},
                ],
            }
        ]
    }
    path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")


def patch_eggs_i18n(monkeypatch) -> None:
    ingredient = dict(cnst.INGREDIENTS["eggs"])
    ingredient["name"] = "eggs"
    ingredient["name_uk"] = EGGS_UK
    monkeypatch.setitem(cnst.INGREDIENTS, "eggs", ingredient)


def test_inventory_source_yaml_import_uses_item_id_and_ignores_stored_name(
    tmp_path: Path,
    monkeypatch,
) -> None:
    patch_eggs_i18n(monkeypatch)
    recipes_path = tmp_path / "recipes.yaml"
    inventory_path = tmp_path / "inventory.yaml"
    write_recipe_yaml(recipes_path)
    inventory_path.write_text(
        yaml.safe_dump(
            {
                "inventory": {
                    "eggs": {
                        "name": "WRONG NAME",
                        "amount": "many",
                    }
                }
            },
            allow_unicode=True,
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    source = InventorySource(
        str(recipes_path),
        mode="yaml",
        inventory_path=str(inventory_path),
        lang="uk",
    )
    inventory = source.load_yaml_inventory_full()

    assert inventory["eggs"]["name"] == EGGS_UK
    assert inventory["eggs"]["amount"] == "many"
    assert source.load_existing_for_engine()["eggs"] == "many"


def test_inventory_source_csv_import_uses_item_id_and_ignores_stored_name(
    tmp_path: Path,
    monkeypatch,
) -> None:
    patch_eggs_i18n(monkeypatch)
    recipes_path = tmp_path / "recipes.yaml"
    inventory_path = tmp_path / "inventory.csv"
    write_recipe_yaml(recipes_path)
    inventory_path.write_text(
        "item_id,name,amount\neggs,WRONG NAME,many\n",
        encoding="utf-8",
    )

    source = InventorySource(
        str(recipes_path),
        mode="csv",
        inventory_path=str(inventory_path),
        lang="uk",
    )
    inventory = source.load_csv_inventory_full()

    assert inventory["eggs"]["name"] == EGGS_UK
    assert inventory["eggs"]["amount"] == "many"
    assert source.load_existing_for_engine()["eggs"] == "many"


def test_inventory_source_csv_import_supports_item_id_and_amount_only(
    tmp_path: Path,
    monkeypatch,
) -> None:
    patch_eggs_i18n(monkeypatch)
    recipes_path = tmp_path / "recipes.yaml"
    inventory_path = tmp_path / "inventory.csv"
    write_recipe_yaml(recipes_path)
    inventory_path.write_text(
        "item_id,amount\neggs,many\n",
        encoding="utf-8",
    )

    source = InventorySource(
        str(recipes_path),
        mode="csv",
        inventory_path=str(inventory_path),
        lang="uk",
    )
    inventory = source.load_csv_inventory_full()

    assert inventory["eggs"]["name"] == EGGS_UK
    assert inventory["eggs"]["amount"] == "many"


def test_inventory_source_saves_display_names_but_keeps_amounts_by_item_id(
    tmp_path: Path,
    monkeypatch,
) -> None:
    patch_eggs_i18n(monkeypatch)
    recipes_path = tmp_path / "recipes.yaml"
    yaml_path = tmp_path / "inventory.yaml"
    csv_path = tmp_path / "inventory.csv"
    write_recipe_yaml(recipes_path)

    yaml_source = InventorySource(
        str(recipes_path),
        mode="yaml",
        inventory_path=str(yaml_path),
        lang="uk",
    )
    yaml_source.save_yaml_inventory_full(
        {
            "eggs": {
                "name": "OUTDATED NAME",
                "amount": "many",
            }
        }
    )
    saved_yaml = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    assert saved_yaml["inventory"]["eggs"]["name"] == EGGS_UK
    assert saved_yaml["inventory"]["eggs"]["amount"] == "many"

    csv_source = InventorySource(
        str(recipes_path),
        mode="csv",
        inventory_path=str(csv_path),
        lang="uk",
    )
    csv_source.save_csv_inventory_full(
        {
            "eggs": {
                "name": "OUTDATED NAME",
                "amount": "many",
            }
        }
    )
    csv_text = csv_path.read_text(encoding="utf-8")
    assert f"eggs,{EGGS_UK},many" in csv_text


def test_inventory_source_uses_language_specific_default_csv_path() -> None:
    source_en = InventorySource("data/recipes/read.yaml", mode="csv", lang="en")
    source_uk = InventorySource("data/recipes/read.yaml", mode="csv", lang="uk")

    assert source_en.inventory_path == cnst.CURRENT_INVENTORY_CSV_EN_PATH
    assert source_uk.inventory_path == cnst.CURRENT_INVENTORY_CSV_UK_PATH
