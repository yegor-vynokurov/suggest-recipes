from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


def write_inventory_yaml(path: Path, inventory: dict[str, str]) -> None:
    data = {
        "amount_values": ["none", "spice", "little", "normal", "many"],
        "inventory": {
            item_id: {
                "name": item_id,
                "amount": amount,
            }
            for item_id, amount in inventory.items()
        },
    }
    path.write_text(
        yaml.safe_dump(data, allow_unicode=True, sort_keys=True),
        encoding="utf-8",
    )


def run_debug_match(recipe_id: str, inventory_path: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            "main.py",
            "debug-match",
            recipe_id,
            "--recipes",
            "data/recipes/read.yaml",
            "--inventory-mode",
            "yaml",
            "--inventory-path",
            str(inventory_path),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


def test_debug_match_cli_prints_detailed_breakdown(tmp_path: Path) -> None:
    inventory_path = tmp_path / "inventory.yaml"
    write_inventory_yaml(
        inventory_path,
        {
            "eggs": "normal",
            "smalec": "normal",
            "mayonnaise": "little",
            "vinegar": "little",
        },
    )

    result = run_debug_match("french_mayonnaise_maison", inventory_path)

    assert result.returncode == 0, result.stderr
    assert "Recipe breakdown" in result.stdout
    assert "id: french_mayonnaise_maison" in result.stdout
    assert "required_id=plant_oil" in result.stdout
    assert "match_type=missing" in result.stdout
    assert "source=-" in result.stdout
    assert "required_id=mustard" in result.stdout
    assert "missing: plant oil" in result.stdout
    assert "missing: mustard" in result.stdout
    assert "Explanations" in result.stdout


def test_debug_match_cli_reports_unknown_recipe(tmp_path: Path) -> None:
    inventory_path = tmp_path / "inventory.yaml"
    write_inventory_yaml(inventory_path, {"eggs": "normal"})

    result = run_debug_match("missing_recipe_id", inventory_path)

    assert result.returncode != 0
    combined_output = f"{result.stdout}\n{result.stderr}"
    assert "Recipe with id=missing_recipe_id was not found" in combined_output
