from __future__ import annotations

import builtins
from pathlib import Path

import yaml

from src.kitchen import constants as cnst
from src.kitchen.inventory_source import InventorySource


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
    ingredient["name_uk"] = "яйця"
    monkeypatch.setitem(cnst.INGREDIENTS, "eggs", ingredient)


def test_inventory_source_item_name_uses_selected_language(
    tmp_path: Path,
    monkeypatch,
) -> None:
    patch_eggs_i18n(monkeypatch)
    recipes_path = tmp_path / "recipes.yaml"
    write_recipe_yaml(recipes_path)

    source_en = InventorySource(str(recipes_path), mode="yaml", lang="en")
    source_uk = InventorySource(str(recipes_path), mode="yaml", lang="uk")

    assert source_en.item_name("eggs") == "eggs"
    assert source_uk.item_name("eggs") == "яйця"


def test_inventory_source_make_empty_inventory_keeps_localized_names(
    tmp_path: Path,
    monkeypatch,
) -> None:
    patch_eggs_i18n(monkeypatch)
    recipes_path = tmp_path / "recipes.yaml"
    write_recipe_yaml(recipes_path)

    source = InventorySource(str(recipes_path), mode="yaml", lang="uk")
    inventory = source.make_empty_inventory()

    assert inventory["eggs"]["name"] == "яйця"
    assert inventory["eggs"]["amount"] == "none"


def test_inventory_source_cli_prompt_and_messages_are_localized(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    patch_eggs_i18n(monkeypatch)
    recipes_path = tmp_path / "recipes.yaml"
    write_recipe_yaml(recipes_path)

    prompts: list[str] = []
    responses = iter(["bad", ""])

    def fake_input(prompt: str) -> str:
        prompts.append(prompt)
        return next(responses)

    monkeypatch.setattr(builtins, "input", fake_input)

    source = InventorySource(str(recipes_path), mode="cli", lang="uk")
    inventory = source.ask_cli_inventory_full()
    captured = capsys.readouterr()

    assert "Редагування комори" in captured.out
    assert "Дозволені значення" in captured.out
    assert "Натисніть Enter" in captured.out
    assert "Невідоме значення" in captured.out
    assert prompts == ["eggs | яйця: ", "eggs | яйця: "]
    assert inventory["eggs"]["name"] == "яйця"
    assert inventory["eggs"]["amount"] == "none"
