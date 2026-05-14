from __future__ import annotations

from pathlib import Path

import pytest

from src.kitchen.recipe_validation import validate_recipe_schema


def make_recipe_data(recipe: dict) -> dict:
    return {"recipes": [recipe]}


def test_validate_recipe_schema_accepts_valid_minimal_recipe() -> None:
    data = make_recipe_data(
        {
            "id": "valid_recipe",
            "name": "Valid recipe",
            "missing_allowed": 1,
            "ingredients": [
                {"item": "eggs", "role": "main", "amount": "normal"},
                {"item": "salt", "role": "spice", "amount": "spice"},
            ],
        }
    )

    validate_recipe_schema(data, Path("valid.yaml"))


def test_validate_recipe_schema_allows_whitelisted_broad_accepts() -> None:
    data = make_recipe_data(
        {
            "id": "valid_broad_accepts",
            "name": "Valid broad accepts",
            "ingredients": [
                {"item": "butter", "role": "required", "amount": "normal", "accepts": ["fat"]},
                {"item": "mustard", "role": "addition", "amount": "little", "accepts": ["sauce"]},
                {"item": "capers", "role": "spice", "amount": "spice", "accepts": ["seasoning"]},
            ],
        }
    )

    validate_recipe_schema(data, Path("valid_broad_accepts.yaml"))


def test_validate_recipe_schema_rejects_unknown_role() -> None:
    data = make_recipe_data(
        {
            "id": "bad_role_recipe",
            "name": "Bad role recipe",
            "ingredients": [
                {"item": "eggs", "role": "core", "amount": "normal"},
            ],
        }
    )

    with pytest.raises(ValueError, match=r"role=core"):
        validate_recipe_schema(data, Path("bad_role.yaml"))


def test_validate_recipe_schema_rejects_unknown_amount() -> None:
    data = make_recipe_data(
        {
            "id": "bad_amount_recipe",
            "name": "Bad amount recipe",
            "ingredients": [
                {"item": "eggs", "role": "main", "amount": "huge"},
            ],
        }
    )

    with pytest.raises(ValueError, match=r"amount=huge"):
        validate_recipe_schema(data, Path("bad_amount.yaml"))


def test_validate_recipe_schema_rejects_negative_missing_allowed() -> None:
    data = make_recipe_data(
        {
            "id": "bad_missing_allowed",
            "name": "Bad missing allowed",
            "missing_allowed": -1,
            "ingredients": [
                {"item": "eggs", "role": "main", "amount": "normal"},
            ],
        }
    )

    with pytest.raises(ValueError, match=r"missing_allowed должен быть >= 0"):
        validate_recipe_schema(data, Path("bad_missing_allowed.yaml"))


def test_validate_recipe_schema_rejects_non_whitelisted_broad_accepts() -> None:
    data = make_recipe_data(
        {
            "id": "bad_broad_accepts",
            "name": "Bad broad accepts",
            "ingredients": [
                {"item": "eggs", "role": "main", "amount": "normal", "accepts": ["fat"]},
                {"item": "cheese", "role": "required", "amount": "normal", "accepts": ["dairy"]},
            ],
        }
    )

    with pytest.raises(ValueError) as exc_info:
        validate_recipe_schema(data, Path("bad_broad_accepts.yaml"))

    message = str(exc_info.value)
    assert "eggs" in message
    assert "cheese" in message
    assert "fat" in message
    assert "dairy" in message
    assert "whitelist" in message


def test_validate_recipe_schema_rejects_too_broad_accepts_in_mayonnaise() -> None:
    data = make_recipe_data(
        {
            "id": "french_mayonnaise_maison",
            "name": "Mayonnaise maison",
            "missing_allowed": 1,
            "ingredients": [
                {"item": "eggs", "role": "main", "amount": "normal"},
                {
                    "item": "plant_oil",
                    "role": "required",
                    "amount": "many",
                    "accepts": ["fat"],
                },
                {
                    "item": "mustard",
                    "role": "required",
                    "amount": "little",
                    "accepts": ["sauce"],
                },
            ],
        }
    )

    with pytest.raises(ValueError) as exc_info:
        validate_recipe_schema(data, Path("bad_mayo.yaml"))

    message = str(exc_info.value)
    assert "plant_oil" in message
    assert "mustard" in message
    assert "fat" in message
    assert "sauce" in message
