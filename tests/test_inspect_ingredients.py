from __future__ import annotations

from collections import Counter
from pathlib import Path
import re

import yaml

from src.kitchen import constants as cnsts
from src.kitchen.inspect_ingredients import (
    LocalizationIssue,
    Usage,
    audit_localized_sources,
    collect_recipe_usage,
    infer_by_pattern,
    make_ingredient_yaml_entry,
    print_localization_audit_report,
    print_report,
    write_drafts,
)


def write_recipe_fixture(path: Path) -> None:
    data = {
        "metadata": {"version": "test", "kind": "recipes"},
        "recipes": [
            {
                "id": "demo_smoked_trout",
                "name": "Demo smoked trout",
                "ingredients": [
                    {"item": "smoked_trout", "role": "main", "amount": "normal"},
                    {
                        "item": "mustard_sauce",
                        "role": "addition",
                        "amount": "little",
                        "accepts": ["pickled_herring"],
                    },
                ],
            }
        ],
    }
    path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")


def test_collect_recipe_usage_tracks_accept_contexts_and_amounts(tmp_path: Path) -> None:
    recipes_path = tmp_path / "recipes.yaml"
    write_recipe_fixture(recipes_path)

    usage = collect_recipe_usage(recipes_path)

    smoked_trout = usage["smoked_trout"]
    pickled_herring = usage["pickled_herring"]

    assert smoked_trout.appearance == "item"
    assert smoked_trout.item_hits == 1
    assert smoked_trout.amounts["normal"] == 1
    assert smoked_trout.examples[0].field == "item"

    assert pickled_herring.appearance == "accepts"
    assert pickled_herring.accept_hits == 1
    assert pickled_herring.roles["accepts"] == 1
    assert pickled_herring.amounts["little"] == 1
    assert pickled_herring.accepted_by["mustard_sauce"] == 1
    assert pickled_herring.examples[0].related_item_id == "mustard_sauce"


def test_infer_by_pattern_uses_new_structural_heuristics() -> None:
    usage = Usage(item_id="dummy", roles=Counter(), recipes=set())

    smoked_trout = infer_by_pattern("smoked_trout", usage=usage)
    langoustine = infer_by_pattern("langoustine", usage=usage)
    tortilla = infer_by_pattern("tortilla", usage=usage)
    apricot_jam = infer_by_pattern("apricot_jam", usage=usage)
    chicken_wings = infer_by_pattern("chicken_wings", usage=usage)
    pickled_cauliflower = infer_by_pattern("pickled_cauliflower", usage=usage)
    sev = infer_by_pattern("sev", usage=usage)
    pork_ears = infer_by_pattern("pork_ears", usage=usage)

    assert smoked_trout["groups"] == ["fish", "fish_product", "smoked_fish"]
    assert smoked_trout["target"] == "fish_seafood"
    assert smoked_trout["confidence"] == "derived"

    assert langoustine["groups"] == ["seafood", "crustacean"]
    assert langoustine["target"] == "fish_seafood"

    assert tortilla["groups"] == ["bread_base", "flatbread"]
    assert tortilla["target"] == "grains_bread"

    assert apricot_jam["groups"] == ["sweetener", "sauce", "fruit_preserve"]
    assert apricot_jam["target"] == "sauces_condiments"

    assert chicken_wings["groups"] == ["poultry", "meat_piece", "meat_on_bone"]
    assert chicken_wings["target"] == "meat_poultry"

    assert pickled_cauliflower["groups"] == ["vegetable", "pickled_vegetable", "fermented_condiment"]
    assert pickled_cauliflower["target"] == "vegetables_mushrooms_fruits"

    assert sev["groups"] == ["prepared_component", "legume"]
    assert sev["target"] == "prepared_components"
    assert sev["confidence"] == "manual"

    assert pork_ears["name"] == "pork ears"
    assert pork_ears["name_uk"] == "свинячі вушка"
    assert pork_ears["aliases"] == []
    assert pork_ears["aliases_uk"] == ["свинячі вушка", "свинячі вуха"]


def test_print_report_shows_reason_accept_context_and_examples(capsys) -> None:
    usage = Usage(
        item_id="pickled_herring",
        roles=Counter({"accepts": 2}),
        recipes={"demo_a", "demo_b"},
        appears_as_accept=True,
        amounts=Counter({"little": 2}),
        accepted_by=Counter({"mustard_sauce": 2}),
        accept_hits=2,
    )
    usage.add_example("demo_a", "accept", "addition", "little", related_item_id="mustard_sauce")

    print_report({"pickled_herring": usage})
    captured = capsys.readouterr().out

    assert "suggestion_reason:" in captured
    assert "appearance: accepts" in captured
    assert "accepted_by: mustard_sauce:2" in captured
    assert "examples: accept:addition/little<-mustard_sauce@demo_a" in captured


def test_write_drafts_uses_enriched_heuristic_comment(tmp_path: Path) -> None:
    usage = Usage(
        item_id="smoked_trout",
        roles=Counter({"main": 1}),
        recipes={"demo_smoked_trout"},
        appears_as_item=True,
        amounts=Counter({"normal": 1}),
        item_hits=1,
    )

    created = write_drafts({"smoked_trout": usage}, draft_dir=tmp_path)

    assert len(created) == 1
    draft_data = yaml.safe_load(created[0].read_text(encoding="utf-8"))
    entry = draft_data["ingredients"]["smoked_trout"]

    assert entry["groups"] == ["fish", "fish_product", "smoked_fish"]
    assert "target=fish_seafood" in entry["comment"]
    assert "reason=derived from known base item trout + smoked prefix" in entry["comment"]


def test_make_ingredient_yaml_entry_moves_legacy_aliases_to_aliases_uk() -> None:
    suggestion = infer_by_pattern("horseradish")

    entry = make_ingredient_yaml_entry("horseradish", suggestion)

    assert entry["name"] == "horseradish"
    assert entry["name_uk"] == "хрін"
    assert entry["aliases"] == []
    assert entry["aliases_uk"] == ["хрін"]


def test_audit_localized_sources_finds_missing_name_uk_and_legacy_fields(tmp_path: Path) -> None:
    ingredients_dir = tmp_path / "ingredients"
    ingredients_dir.mkdir()

    categories_data = {
        "metadata": {"version": "test", "kind": "categories"},
        "categories": {
            "protein": {"name": "protein", "name_uk": "білкові продукти"},
            "meat": {"name": "мясо", "parents": ["protein"]},
        },
    }
    ingredients_data = {
        "metadata": {"version": "test", "kind": "ingredients", "domain": "meat_poultry"},
        "ingredients": {
            "beef": {
                "name": "beef",
                "groups": ["meat"],
            },
            "broth": {
                "name": "broth",
                "name_uk": "бульйон",
                "comment": "мясной бульон",
                "groups": ["protein"],
            },
            "mustard": {
                "name": "mustard",
                "name_uk": "гірчиця",
                "aliases": ["горчица"],
                "groups": ["protein"],
            },
        },
    }

    (ingredients_dir / "ingredient_categories.yaml").write_text(
        yaml.safe_dump(categories_data, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    (ingredients_dir / "ingredients_meat_poultry.yaml").write_text(
        yaml.safe_dump(ingredients_data, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )

    report = audit_localized_sources(ingredients_dir)
    issue_keys = {
        (issue.file_name, issue.entry_id, issue.issue_type, issue.field_name)
        for issue in report.issues
    }

    assert ("ingredient_categories.yaml", "meat", "legacy_name", "name") in issue_keys
    assert ("ingredient_categories.yaml", "meat", "missing_name_uk", "name_uk") in issue_keys
    assert ("ingredients_meat_poultry.yaml", "beef", "missing_name_uk", "name_uk") in issue_keys
    assert ("ingredients_meat_poultry.yaml", "broth", "legacy_comment", "comment") in issue_keys
    assert ("ingredients_meat_poultry.yaml", "mustard", "legacy_aliases", "aliases") in issue_keys


def test_print_localization_audit_report_shows_summary(capsys) -> None:
    report = type("DummyReport", (), {})()
    report.issues = [
        LocalizationIssue(
            file_name="ingredients_meat_poultry.yaml",
            section="ingredients",
            entry_id="beef",
            issue_type="missing_name_uk",
            field_name="name_uk",
        ),
        LocalizationIssue(
            file_name="ingredient_categories.yaml",
            section="categories",
            entry_id="meat",
            issue_type="legacy_name",
            field_name="name",
            value="мясо",
        ),
    ]
    report.issue_counts = Counter({"missing_name_uk": 1, "legacy_name": 1})
    report.file_counts = Counter({"ingredients_meat_poultry.yaml": 1, "ingredient_categories.yaml": 1})

    print_localization_audit_report(report)
    captured = capsys.readouterr().out

    assert "Localization audit found issues." in captured
    assert "- missing_name_uk: 1" in captured
    assert "ingredient_categories.yaml:categories.meat name -> legacy_name" in captured


def test_real_source_ingredient_files_pass_localization_audit() -> None:
    report = audit_localized_sources(cnsts.INGREDIENTS_DIR)

    assert report.issues == []


def test_known_suggestions_block_has_no_cyrillic_literals() -> None:
    source = Path("src/kitchen/inspect_ingredients.py").read_text(encoding="utf-8")
    start = source.index("KNOWN_SUGGESTIONS:")
    end = source.index("\n\n\nROLE_ORDER")
    block = source[start:end]

    assert re.search(r"[А-Яа-яІіЇїЄєҐґ]", block) is None
