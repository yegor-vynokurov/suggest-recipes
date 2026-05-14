from __future__ import annotations

from main import (
    bootstrap_lang_from_argv,
    build_parser,
    print_debug_match,
    print_suggestions,
    resolve_lang,
)


def test_main_parser_uses_english_by_default() -> None:
    parser = build_parser()

    args = parser.parse_args(["suggest"])

    assert args.lang == "en"
    assert resolve_lang(args) == "en"


def test_main_parser_accepts_lang_before_subcommand() -> None:
    parser = build_parser()

    args = parser.parse_args(["--lang", "uk", "suggest"])

    assert args.lang == "uk"
    assert resolve_lang(args) == "uk"


def test_main_parser_accepts_lang_after_subcommand() -> None:
    parser = build_parser()

    args = parser.parse_args(["suggest", "--lang", "uk"])

    assert args.lang == "uk"
    assert resolve_lang(args) == "uk"


def test_main_parser_exposes_lang_for_non_inventory_commands() -> None:
    parser = build_parser()

    args = parser.parse_args(["build-recipes", "--lang", "uk"])

    assert args.lang == "uk"
    assert resolve_lang(args) == "uk"


def test_main_parser_uses_language_specific_excel_default_for_init_command() -> None:
    parser = build_parser()

    args = parser.parse_args(["init-inventory-excel", "--lang", "uk"])

    assert args.lang == "uk"
    assert args.inventory_xlsx is None


def test_main_parser_uses_language_specific_excel_default_for_export_command() -> None:
    parser = build_parser()

    args = parser.parse_args(["inventory-excel-to-csv", "--lang", "uk"])

    assert args.lang == "uk"
    assert args.inventory_xlsx is None


def test_bootstrap_lang_detects_global_flag_before_building_parser() -> None:
    assert bootstrap_lang_from_argv(["--lang", "uk", "suggest"]) == "uk"
    assert bootstrap_lang_from_argv(["debug-match", "--lang", "uk"]) == "uk"
    assert bootstrap_lang_from_argv(["suggest"]) == "en"


def test_build_parser_localizes_help_text_for_ukrainian() -> None:
    parser = build_parser(lang="uk")

    help_text = parser.format_help()

    assert "Підбір страв з доступних інгредієнтів." in help_text
    assert "Мова CLI: en (типово) або uk." in help_text
    assert "Створити або оновити шаблон комори." in help_text


def test_print_suggestions_localizes_headings_and_status(capsys) -> None:
    result = {
        "suggestions": {
            "can_cook": [
                {
                    "name": "Test dish",
                    "score": 0.91,
                    "status": "can_cook",
                    "explanations": ["missing: milk"],
                    "comment": "Serve warm",
                    "comment_text": "Comment: Serve warm",
                }
            ]
        }
    }

    print_suggestions(result, lang="uk")
    output = capsys.readouterr().out

    assert "Знайдені страви" in output
    assert "МОЖНА ГОТУВАТИ" in output
    assert "оцінка=0.91" in output
    assert "статус=можна готувати" in output
    assert "Comment: Serve warm" in output


def test_print_debug_match_localizes_titles_and_status(capsys) -> None:
    match = {
        "recipe_id": "debug_recipe",
        "name": "Debug recipe",
        "status": "missing_one",
        "score": 0.5,
        "base_score": 0.6,
        "filtered_score": 0.5,
        "matches": [],
        "explanations": [],
    }

    print_debug_match(match, lang="en")
    output = capsys.readouterr().out

    assert "Recipe breakdown" in output
    assert "Status: missing one" in output
    assert "Score: 0.5 (base=0.6, filtered=0.5)" in output
    assert "Explanations" in output
    assert "- none" in output
