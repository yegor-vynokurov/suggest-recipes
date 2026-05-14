from __future__ import annotations

from collections import Counter
from functools import lru_cache
from pathlib import Path
from typing import Any

import pytest
import yaml

from src.kitchen.constants import ALWAYS_AVAILABLE_INVENTORY, ING_PATH
from src.kitchen.parse_recipes import load_recipes_from_yaml
from src.kitchen.recipe_engine import RecipeEngine


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "match_regressions.yaml"


@lru_cache(maxsize=1)
def load_regression_fixture() -> dict[str, Any]:
    with FIXTURE_PATH.open("r", encoding="utf-8") as file:
        return yaml.safe_load(file) or {}


def build_inventory(case: dict[str, Any]) -> dict[str, str]:
    inventory = dict(ALWAYS_AVAILABLE_INVENTORY)
    inventory.update(case.get("inventory", {}) or {})
    return inventory


@pytest.fixture(scope="module")
def engine() -> RecipeEngine:
    recipes = load_recipes_from_yaml(str(ING_PATH))
    return RecipeEngine(recipes=recipes, inventory={})


def run_case(engine: RecipeEngine, case: dict[str, Any]) -> dict[str, Any]:
    match = engine.match_recipe_by_id(
        recipe_id=case["recipe_id"],
        inventory=build_inventory(case),
    )
    assert match is not None, f"Recipe {case['recipe_id']} was not found in {ING_PATH}"
    return match


def make_case_param(case: dict[str, Any]) -> Any:
    if case.get("xfail"):
        reason = case.get("known_issue", "Known regression scenario.")
        return pytest.param(
            case,
            id=case["case_id"],
            marks=pytest.mark.xfail(reason=reason, strict=False),
        )

    return pytest.param(case, id=case["case_id"])


CASES = load_regression_fixture().get("cases", [])
CASE_PARAMS = [pytest.param(case, id=case["case_id"]) for case in CASES]
TARGET_CASE_PARAMS = [make_case_param(case) for case in CASES]


def case_by_id(case_id: str) -> dict[str, Any]:
    for case in CASES:
        if case["case_id"] == case_id:
            return case

    raise KeyError(f"Unknown regression case id: {case_id}")


def find_match_item(match: dict[str, Any], required_id: str) -> dict[str, Any]:
    for item in match["matches"]:
        if item["required_id"] == required_id:
            return item

    raise KeyError(f"required_id={required_id} not found in match for {match['recipe_id']}")


def test_regression_fixture_is_not_empty() -> None:
    assert CASES, f"No regression cases were loaded from {FIXTURE_PATH}"


def test_regression_case_ids_are_unique() -> None:
    case_ids = [case["case_id"] for case in CASES]
    assert len(case_ids) == len(set(case_ids))


@pytest.mark.parametrize("case", CASE_PARAMS)
def test_regression_case_executes(case: dict[str, Any], engine: RecipeEngine) -> None:
    match = run_case(engine, case)

    assert match["recipe_id"] == case["recipe_id"]
    assert isinstance(match["status"], str)
    assert isinstance(match["score"], float)
    assert isinstance(match["explanations"], list)
    assert match["name"]


@pytest.mark.parametrize("case", TARGET_CASE_PARAMS)
def test_regression_case_target_behavior(case: dict[str, Any], engine: RecipeEngine) -> None:
    match = run_case(engine, case)
    expected = case.get("expected", {}) or {}

    if "status" in expected:
        assert match["status"] == expected["status"]

    for text in expected.get("contains_explanations", []) or []:
        assert text in match["explanations"]

    for text in expected.get("not_contains_explanations", []) or []:
        assert text not in match["explanations"]

    if "explanation_counts" in expected:
        counts = Counter(match["explanations"])
        for text, count in (expected.get("explanation_counts", {}) or {}).items():
            assert counts[text] == count


def test_mayonnaise_recipe_forbids_smalec_and_mayonnaise_substitutions(
    engine: RecipeEngine,
) -> None:
    match = run_case(engine, case_by_id("mayonnaise_oil_vs_fat"))

    plant_oil = find_match_item(match, "plant_oil")
    mustard = find_match_item(match, "mustard")

    assert plant_oil["match_type"] == "missing"
    assert plant_oil["used_id"] is None
    assert mustard["match_type"] == "missing"
    assert mustard["used_id"] is None

    assert "plant oil substituted by category: smalec" not in match["explanations"]
    assert "mustard substituted by category: mayonnaise" not in match["explanations"]


def test_deruny_does_not_treat_sour_cream_as_critical_missing(
    engine: RecipeEngine,
) -> None:
    match = run_case(engine, case_by_id("deruny_sour_cream_is_addition"))

    sour_cream = find_match_item(match, "sour_cream")

    assert sour_cream["role"] == "addition"
    assert sour_cream["match_type"] == "missing"
    assert match["status"] == "can_cook"
    assert "missing: sour cream" not in match["explanations"]

def test_aebleskiver_has_no_duplicate_milk_warning(engine: RecipeEngine) -> None:
    match = run_case(engine, case_by_id("aebleskiver_duplicate_milk_warning"))

    counts = Counter(match["explanations"])

    assert counts["have milk, but too little"] == 1


def test_aebleskiver_does_not_reuse_milk_for_buttermilk(engine: RecipeEngine) -> None:
    match = run_case(engine, case_by_id("aebleskiver_duplicate_milk_warning"))

    milk = find_match_item(match, "milk")
    buttermilk = find_match_item(match, "buttermilk")

    assert milk["used_id"] == "milk"
    assert buttermilk["match_type"] == "missing"
    assert buttermilk["used_id"] is None
    assert "buttermilk substituted by category: milk" not in match["explanations"]
