from __future__ import annotations

from src.kitchen.i18n import (
    CLI_TEXTS,
    DEFAULT_LANG,
    EXCEL_TEXTS,
    RECIPE_EXPLANATION_TEXTS,
    normalize_language,
    t,
)


def test_i18n_uses_expected_default_language() -> None:
    assert DEFAULT_LANG == "en"


def test_i18n_has_separate_catalogs_for_cli_excel_and_recipe_text() -> None:
    assert "cli.file_label" in CLI_TEXTS
    assert "excel.readme.title" in EXCEL_TEXTS
    assert "recipe.explanation.missing" in RECIPE_EXPLANATION_TEXTS


def test_normalize_language_falls_back_to_english() -> None:
    assert normalize_language(None) == "en"
    assert normalize_language("") == "en"
    assert normalize_language("EN") == "en"
    assert normalize_language("ru") == "en"


def test_t_returns_localized_text() -> None:
    assert t("cli.file_label", "en") == "File"
    assert t("cli.file_label", "uk") == "Файл"


def test_t_formats_recipe_explanation_templates() -> None:
    assert t("recipe.explanation.missing", "en", name="milk") == "missing: milk"
    assert t("recipe.explanation.missing", "uk", name="молоко") == "не вистачає: молоко"


def test_t_falls_back_to_english_for_unknown_language() -> None:
    assert t("cli.recipe_bundle_built", "ru") == "Recipe bundle built."


def test_t_returns_key_for_unknown_translation_key() -> None:
    assert t("unknown.translation.key", "en") == "unknown.translation.key"


def test_t_keeps_missing_placeholders_visible() -> None:
    assert t("recipe.explanation.category_substitution", "en", required="mustard") == (
        "mustard substituted by category: {used}"
    )
