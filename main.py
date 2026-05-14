from __future__ import annotations

import argparse
import os

from src.kitchen import constants as cnst
from src.kitchen.cli_support import CliRuntime
from src.kitchen.constants import ING_PATH, INVENT_PATH, RECIPES_PATH
from src.kitchen.i18n import DEFAULT_LANG, SUPPORTED_LANGUAGES, normalize_language
from src.kitchen.inspect_ingredients import (
    audit_localized_sources,
    get_missing,
    merge_drafts_into_ingredients,
    print_localization_audit_report,
    print_report,
    write_drafts,
)
from src.kitchen.inventory_source import InventorySource
from src.kitchen.parse_recipes import load_recipes_from_yaml
from src.kitchen.recipe_collection import build_recipe_bundle, list_available_cuisines
from src.kitchen.recipe_engine import RecipeEngine
from src.kitchen.utils import load_yaml


def resolve_lang(args) -> str:
    return normalize_language(getattr(args, "lang", DEFAULT_LANG))


def bootstrap_lang_from_argv(argv: list[str] | None = None) -> str:
    return CliRuntime.bootstrap_lang_from_argv(argv)


def cli_text(key: str, lang: str | None = DEFAULT_LANG, **kwargs: object) -> str:
    return CliRuntime(lang).text(key, **kwargs)


def status_text(status: str, lang: str | None = DEFAULT_LANG) -> str:
    return CliRuntime(lang).recipe_status(status)


def cuisine_label(cuisine_id: str, lang: str | None = DEFAULT_LANG) -> str:
    return CliRuntime(lang).cuisine_label(cuisine_id)


def configure_console_output() -> None:
    CliRuntime.configure_console_output()


class KitchenCLIApp:
    def __init__(self, lang: str = DEFAULT_LANG) -> None:
        self.runtime = CliRuntime(lang)

    def runtime_for(self, args=None, lang: str | None = None) -> CliRuntime:
        if args is not None:
            return CliRuntime(resolve_lang(args))
        return CliRuntime(lang or self.runtime.lang)

    @staticmethod
    def format_debug_source(match_item: dict) -> str:
        source_id = match_item.get("source_id")
        if not source_id:
            return "-"

        relation = match_item.get("source_relation") or "source"
        source_kind = match_item.get("source_kind") or "unknown"
        source_name = match_item.get("source_name") or source_id
        return f"{relation}/{source_kind}: {source_id} ({source_name})"

    def load_inventory_excel_tools(self, lang: str | None = None):
        runtime = self.runtime_for(lang=lang)
        try:
            from src.kitchen.inventory_excel import (
                export_all_default_inventory_excels_to_csv,
                export_excel_to_current_inventory_csv,
                make_inventory_excel,
            )
        except ModuleNotFoundError as exc:
            if exc.name == "openpyxl":
                raise SystemExit(runtime.text("openpyxl_required")) from exc
            raise

        return make_inventory_excel, export_excel_to_current_inventory_csv, export_all_default_inventory_excels_to_csv

    def print_suggestions(self, result: dict, lang: str | None = None) -> None:
        runtime = self.runtime_for(lang=lang)
        print()
        print(runtime.text("found_dishes_title"))
        print("=" * 40)

        for group_name, matches in result["suggestions"].items():
            if not matches:
                continue

            print()
            print(runtime.recipe_status(group_name).upper())
            print("-" * 40)

            for match in matches:
                print(
                    f"{match['name']} | "
                    f"{runtime.text('score_short_label')}={match['score']} | "
                    f"{runtime.text('status_short_label')}={runtime.recipe_status(match['status'])}"
                )

                for explanation in match["explanations"]:
                    print(f"  - {explanation}")

                if match["comment"]:
                    comment_text = match.get("comment_text")
                    if comment_text:
                        print(f"  {comment_text}")
                    else:
                        print(f"  {runtime.text('comment_label')}: {match['comment']}")

    def print_debug_match(self, match: dict, lang: str | None = None) -> None:
        runtime = self.runtime_for(lang=lang)
        print()
        print(runtime.text("debug_recipe_title"))
        print("=" * 40)
        print(f"{runtime.text('id_label')}: {match['recipe_id']}")
        print(f"{runtime.text('name_label')}: {match['name']}")
        print(f"{runtime.text('status_label')}: {runtime.recipe_status(match['status'])}")
        print(
            f"{runtime.text('score_label')}: "
            f"{runtime.text('score_details', score=match['score'], base=match['base_score'], filtered=match['filtered_score'])}"
        )

        print()
        print(runtime.text("debug_ingredients_title"))
        print("-" * 40)

        for item in match["matches"]:
            used_id = item["used_id"] or "-"
            used_amount = item["available_amount"] or "-"
            accepts = ", ".join(item.get("accepts", [])) or "-"

            print(
                f"- required_id={item['required_id']} "
                f"| role={item['role']} "
                f"| need_amount={item['required_amount']} "
                f"| used_id={used_id} "
                f"| used_amount={used_amount} "
                f"| match_type={item['match_type']} "
                f"| score={item['score']}/{item['max_score']} "
                f"| source={self.format_debug_source(item)}"
            )
            print(f"  {runtime.text('accepts_label')}={accepts}")

            if item["quantity_warning"]:
                print(f"  {runtime.text('warning_label')}={item['quantity_warning']}")

            if item["note"]:
                print(f"  {runtime.text('note_label')}={item['note']}")

        print()
        print(runtime.text("debug_explanations_title"))
        print("-" * 40)

        if not match["explanations"]:
            print(f"- {runtime.text('none')}")
            return

        for explanation in match["explanations"]:
            print(f"- {explanation}")

    def make_inventory_source(self, args, lang: str | None = None) -> InventorySource:
        runtime = self.runtime_for(args=args if lang is None else None, lang=lang)
        inventory_path = args.inventory_path

        if inventory_path is None:
            if args.inventory_mode == "yaml":
                inventory_path = str(cnst.CURRENT_INVENTORY_YAML_PATH)
            elif args.inventory_mode == "csv":
                inventory_path = str(cnst.inventory_csv_path_for_lang(runtime.lang))

        return InventorySource(
            recipes_path=args.recipes,
            mode=args.inventory_mode,
            inventory_path=inventory_path,
            lang=runtime.lang,
        )

    def command_build_recipes(self, args) -> None:
        runtime = self.runtime_for(args=args)
        result = build_recipe_bundle(
            cuisines=args.cuisines,
            recipes_dir=args.recipes_dir,
            output_path=args.output,
            include_pantry=not args.no_pantry,
            fail_on_duplicate_ids=not args.allow_duplicate_ids,
            lang=runtime.lang,
        )

        print()
        print(runtime.text("recipe_bundle_built"))
        print(
            f"{runtime.text('cuisines_label')}: "
            f"{', '.join(runtime.cuisine_label(cuisine) for cuisine in result['selected_cuisines'])}"
        )
        print(f"{runtime.text('recipe_count_label')}: {result['recipe_count']}")
        print(f"{runtime.text('file_label')}: {result['output_path']}")

        print()
        print(f"{runtime.text('sources_label')}:")
        for source in result["source_files"]:
            print(f"- {source}")

    def command_list_cuisines(self, args) -> None:
        runtime = self.runtime_for(args=args)
        available = list_available_cuisines(args.recipes_dir)

        print()
        print(f"{runtime.text('available_cuisines_title')}:")
        for cuisine in available:
            print(f"- {runtime.cuisine_label(cuisine)}")

    def command_init_inventory(self, args) -> None:
        runtime = self.runtime_for(args=args)
        inventory_source = self.make_inventory_source(args, lang=runtime.lang)
        inventory_source.sync_template(overwrite=args.overwrite)

        print()
        print(runtime.text("inventory_template_ready"))
        print(f"{runtime.text('mode_label')}: {args.inventory_mode}")

        if args.inventory_path:
            print(f"{runtime.text('file_label')}: {args.inventory_path}")

        print()
        print(runtime.text("open_file_and_fill_amounts"))
        print(
            f"python main.py suggest "
            f"--inventory-mode {args.inventory_mode} "
            f"--inventory-path {args.inventory_path}"
        )

    def command_init_inventory_excel(self, args) -> None:
        runtime = self.runtime_for(args=args)
        make_inventory_excel, _, _ = self.load_inventory_excel_tools(runtime.lang)

        args.inventory_xlsx = make_inventory_excel(
            ingredients_dir=args.ingredients_dir,
            inventory_xlsx=args.inventory_xlsx,
            existing_csv=args.existing_csv,
            lang=runtime.lang,
            verbose=False,
        )

        print()
        print(runtime.text("inventory_excel_ready"))
        print(f"{runtime.text('file_label')}: {args.inventory_xlsx}")
        print()
        print(runtime.text("open_file_and_fill_amounts"))
        print("python main.py inventory-excel-to-csv")
        print("python main.py suggest --inventory-mode csv")

    def command_inventory_excel_to_csv(self, args) -> None:
        runtime = self.runtime_for(args=args)
        _, export_excel_to_current_inventory_csv, export_all_default_inventory_excels_to_csv = self.load_inventory_excel_tools(runtime.lang)

        if args.inventory_xlsx or args.inventory_csv:
            args.inventory_csv = export_excel_to_current_inventory_csv(
                inventory_xlsx=args.inventory_xlsx,
                inventory_csv=args.inventory_csv,
                include_none=not args.only_existing,
                lang=runtime.lang,
                verbose=False,
            )

            print()
            print(runtime.text("inventory_csv_ready"))
            print(f"{runtime.text('file_label')}: {args.inventory_csv}")
        else:
            exported = export_all_default_inventory_excels_to_csv(
                include_none=not args.only_existing,
                output_lang=runtime.lang,
                verbose=False,
            )

            print()
            print(runtime.text("inventory_csv_ready"))
            for lang, path in exported.items():
                print(f"- {lang}: {path}")

        print()
        print(runtime.text("excel_followup_title"))
        print("python main.py suggest --inventory-mode csv")

    def command_inspect_ingredients(self, args) -> None:
        if getattr(args, "audit_localization", False):
            report = audit_localized_sources(ingredients_dir=args.ingredients_dir)
            print_localization_audit_report(report)
            return

        missing, _, _ = get_missing(
            recipes_path=args.recipes,
            merged_path=args.merged_ingredients,
            include_accepts=not args.no_accepts,
        )

        print_report(missing)

        if args.write_drafts:
            write_drafts(
                missing,
                draft_dir=args.draft_dir,
            )

    @staticmethod
    def command_merge_ingredient_drafts(args) -> None:
        merge_drafts_into_ingredients(
            draft_dir=args.draft_dir,
            ingredients_dir=args.ingredients_dir,
            merged_path=args.merged_ingredients,
            delete_drafts=not args.keep_drafts,
        )

    def _maybe_rebuild_recipes_for_cuisines(self, args) -> None:
        if not args.cuisines:
            return

        build_recipe_bundle(
            cuisines=args.cuisines,
            recipes_dir=RECIPES_PATH,
            output_path=os.path.join(RECIPES_PATH, "read.yaml"),
            include_pantry=True,
            lang=resolve_lang(args),
        )
        args.recipes = os.path.join(RECIPES_PATH, "read.yaml")

    def command_suggest(self, args) -> None:
        runtime = self.runtime_for(args=args)
        self._maybe_rebuild_recipes_for_cuisines(args)

        inventory_source = self.make_inventory_source(args, lang=runtime.lang)
        recipes = load_recipes_from_yaml(args.recipes)
        inventory = inventory_source.load_existing_for_engine()
        inventory.update(cnst.ALWAYS_AVAILABLE_INVENTORY)

        engine = RecipeEngine(
            recipes=recipes,
            inventory=inventory,
            lang=runtime.lang,
        )

        result = engine.suggest(
            limit_per_group=args.limit,
            filters=args.filters,
            prefer_categories=args.prefer_category,
            randomize=args.randomize,
            random_strength=args.random_strength,
            seed=args.seed,
        )

        self.print_suggestions(result, lang=runtime.lang)

    def command_debug_match(self, args) -> None:
        runtime = self.runtime_for(args=args)
        self._maybe_rebuild_recipes_for_cuisines(args)

        inventory_source = self.make_inventory_source(args, lang=runtime.lang)
        recipes = load_recipes_from_yaml(args.recipes)
        inventory = inventory_source.load_existing_for_engine()

        engine = RecipeEngine(
            recipes=recipes,
            inventory=inventory,
            lang=runtime.lang,
        )

        match = engine.match_recipe_by_id(
            recipe_id=args.recipe_id,
            inventory=inventory,
        )

        if match is None:
            raise SystemExit(
                runtime.text(
                    "recipe_not_found",
                    recipe_id=args.recipe_id,
                    recipes=args.recipes,
                )
            )

        self.print_debug_match(match, lang=runtime.lang)

    def command_set_amount(self, args) -> None:
        runtime = self.runtime_for(args=args)
        inventory_source = self.make_inventory_source(args, lang=runtime.lang)

        inventory_source.set_amount(
            item_id=args.item_id,
            amount=args.amount,
        )

        print(runtime.text("saved_amount", item_id=args.item_id, amount=args.amount))

    def build_parser(self) -> argparse.ArgumentParser:
        parser_lang = self.runtime.lang

        root_language_parent = argparse.ArgumentParser(add_help=False)
        root_language_parent.add_argument(
            "--lang",
            choices=SUPPORTED_LANGUAGES,
            default=DEFAULT_LANG,
            help=self.runtime.text("language_help"),
        )

        subcommand_language_parent = argparse.ArgumentParser(add_help=False)
        subcommand_language_parent.add_argument(
            "--lang",
            choices=SUPPORTED_LANGUAGES,
            default=argparse.SUPPRESS,
            help=self.runtime.text("language_help"),
        )

        parser = argparse.ArgumentParser(
            description=self.runtime.text("app_description"),
            parents=[root_language_parent],
        )

        subparsers = parser.add_subparsers(
            dest="command",
            required=True,
        )

        def add_command_parser(*args, **kwargs):
            kwargs.setdefault("parents", [subcommand_language_parent])
            return subparsers.add_parser(*args, **kwargs)

        def add_common_args(command_parser):
            command_parser.add_argument(
                "--recipes",
                default=ING_PATH,
                help=self.runtime.text("help.recipes"),
            )
            command_parser.add_argument(
                "--inventory-mode",
                choices=["yaml", "csv", "cli"],
                default="yaml",
                help=self.runtime.text("help.inventory_mode"),
            )
            command_parser.add_argument(
                "--inventory-path",
                default=None,
                help=self.runtime.text("help.inventory_path"),
            )

        init_parser = add_command_parser(
            "init-inventory",
            help=self.runtime.text("help.init_inventory_command"),
        )
        add_common_args(init_parser)
        init_parser.add_argument(
            "--overwrite",
            action="store_true",
            help=self.runtime.text("help.overwrite"),
        )
        init_parser.set_defaults(func=self.command_init_inventory)

        inspect_parser = add_command_parser(
            "inspect-ingredients",
            help=self.runtime.text("help.inspect_ingredients_command"),
        )
        add_common_args(inspect_parser)
        inspect_parser.add_argument(
            "--merged-ingredients",
            default=os.path.join(INVENT_PATH, "ingredients", "ingredients_all_merged.yaml"),
            help=self.runtime.text("help.merged_ingredients"),
        )
        inspect_parser.add_argument(
            "--no-accepts",
            action="store_true",
            help=self.runtime.text("help.no_accepts"),
        )
        inspect_parser.add_argument(
            "--write-drafts",
            action="store_true",
            help=self.runtime.text("help.write_drafts"),
        )
        inspect_parser.add_argument(
            "--draft-dir",
            default=os.path.join(INVENT_PATH, "ingredients", "_drafts"),
            help=self.runtime.text("help.draft_dir"),
        )
        inspect_parser.add_argument(
            "--ingredients-dir",
            default=os.path.join(INVENT_PATH, "ingredients"),
            help=self.runtime.text("help.ingredients_dir"),
        )
        inspect_parser.add_argument(
            "--audit-localization",
            action="store_true",
            help=self.runtime.text("help.audit_localization"),
        )
        inspect_parser.set_defaults(func=self.command_inspect_ingredients)

        merge_drafts_parser = add_command_parser(
            "merge-ingredient-drafts",
            help=self.runtime.text("help.merge_drafts_command"),
        )
        merge_drafts_parser.add_argument(
            "--draft-dir",
            default=os.path.join(INVENT_PATH, "ingredients", "_drafts"),
            help=self.runtime.text("help.merge_drafts_draft_dir"),
        )
        merge_drafts_parser.add_argument(
            "--ingredients-dir",
            default=os.path.join(INVENT_PATH, "ingredients"),
            help=self.runtime.text("help.merge_drafts_ingredients_dir"),
        )
        merge_drafts_parser.add_argument(
            "--merged-ingredients",
            default=os.path.join(INVENT_PATH, "ingredients", "ingredients_all_merged.yaml"),
            help=self.runtime.text("help.merge_drafts_merged_ingredients"),
        )
        merge_drafts_parser.add_argument(
            "--keep-drafts",
            action="store_true",
            help=self.runtime.text("help.keep_drafts"),
        )
        merge_drafts_parser.set_defaults(func=self.command_merge_ingredient_drafts)

        init_excel_parser = add_command_parser(
            "init-inventory-excel",
            help=self.runtime.text("help.init_inventory_excel_command"),
        )
        init_excel_parser.add_argument(
            "--ingredients-dir",
            default=os.path.join(INVENT_PATH, "ingredients"),
            help=self.runtime.text("help.ingredients_dir"),
        )
        init_excel_parser.add_argument(
            "--inventory-xlsx",
            default=None,
            help=self.runtime.text("help.inventory_xlsx_output"),
        )
        init_excel_parser.add_argument(
            "--existing-csv",
            default=None,
            help=self.runtime.text("help.existing_csv"),
        )
        init_excel_parser.set_defaults(func=self.command_init_inventory_excel)

        excel_to_csv_parser = add_command_parser(
            "inventory-excel-to-csv",
            help=self.runtime.text("help.inventory_excel_to_csv_command"),
        )
        excel_to_csv_parser.add_argument(
            "--inventory-xlsx",
            default=None,
            help=self.runtime.text("help.inventory_xlsx_input"),
        )
        excel_to_csv_parser.add_argument(
            "--inventory-csv",
            default=None,
            help=self.runtime.text("help.inventory_csv_output"),
        )
        excel_to_csv_parser.add_argument(
            "--only-existing",
            action="store_true",
            help=self.runtime.text("help.only_existing"),
        )
        excel_to_csv_parser.set_defaults(func=self.command_inventory_excel_to_csv)

        build_recipes_parser = add_command_parser(
            "build-recipes",
            help=self.runtime.text("help.build_recipes_command"),
        )
        build_recipes_parser.add_argument(
            "--cuisine",
            "--cuisines",
            dest="cuisines",
            default="all",
            help=self.runtime.text("help.cuisines_option"),
        )
        build_recipes_parser.add_argument(
            "--recipes-dir",
            default=RECIPES_PATH,
            help=self.runtime.text("help.recipes_dir"),
        )
        build_recipes_parser.add_argument(
            "--output",
            default=os.path.join(RECIPES_PATH, "read.yaml"),
            help=self.runtime.text("help.output"),
        )
        build_recipes_parser.add_argument(
            "--no-pantry",
            action="store_true",
            help=self.runtime.text("help.no_pantry"),
        )
        build_recipes_parser.add_argument(
            "--allow-duplicate-ids",
            action="store_true",
            help=self.runtime.text("help.allow_duplicate_ids"),
        )
        build_recipes_parser.set_defaults(func=self.command_build_recipes)

        list_cuisines_parser = add_command_parser(
            "list-cuisines",
            help=self.runtime.text("help.list_cuisines_command"),
        )
        list_cuisines_parser.add_argument(
            "--recipes-dir",
            default=RECIPES_PATH,
            help=self.runtime.text("help.recipes_dir"),
        )
        list_cuisines_parser.set_defaults(func=self.command_list_cuisines)

        suggest_parser = add_command_parser(
            "suggest",
            help=self.runtime.text("help.suggest_command"),
        )
        add_common_args(suggest_parser)
        suggest_parser.add_argument(
            "--limit",
            type=int,
            default=10,
            help=self.runtime.text("help.limit"),
        )
        suggest_parser.add_argument(
            "--filters",
            nargs="*",
            default=[],
            help=self.runtime.text("help.filters"),
        )
        suggest_parser.add_argument(
            "--prefer-category",
            nargs="*",
            default=[],
            help=self.runtime.text("help.prefer_category"),
        )
        suggest_parser.add_argument(
            "--randomize",
            action="store_true",
            help=self.runtime.text("help.randomize"),
        )
        suggest_parser.add_argument(
            "--random-strength",
            type=float,
            default=0.06,
            help=self.runtime.text("help.random_strength"),
        )
        suggest_parser.add_argument(
            "--seed",
            type=int,
            default=None,
            help=self.runtime.text("help.seed"),
        )
        suggest_parser.add_argument(
            "--cuisine",
            "--cuisines",
            dest="cuisines",
            default=None,
            help=self.runtime.text("help.suggest_cuisines"),
        )
        suggest_parser.set_defaults(func=self.command_suggest)

        debug_match_parser = add_command_parser(
            "debug-match",
            help=self.runtime.text("help.debug_match_command"),
        )
        add_common_args(debug_match_parser)
        debug_match_parser.add_argument(
            "recipe_id",
            help=self.runtime.text("help.recipe_id"),
        )
        debug_match_parser.add_argument(
            "--cuisine",
            "--cuisines",
            dest="cuisines",
            default=None,
            help=self.runtime.text("help.debug_cuisines"),
        )
        debug_match_parser.set_defaults(func=self.command_debug_match)

        set_parser = add_command_parser(
            "set",
            help=self.runtime.text("help.set_command"),
        )
        add_common_args(set_parser)
        set_parser.add_argument(
            "item_id",
            help=self.runtime.text("help.item_id"),
        )
        set_parser.add_argument(
            "amount",
            choices=["none", "spice", "little", "normal", "many"],
            help=self.runtime.text("help.amount"),
        )
        set_parser.set_defaults(func=self.command_set_amount)

        return parser


def print_suggestions(result: dict, lang: str | None = DEFAULT_LANG) -> None:
    KitchenCLIApp(lang or DEFAULT_LANG).print_suggestions(result, lang=lang)


def print_debug_match(match: dict, lang: str | None = DEFAULT_LANG) -> None:
    KitchenCLIApp(lang or DEFAULT_LANG).print_debug_match(match, lang=lang)


def make_inventory_source(args, lang: str | None = DEFAULT_LANG) -> InventorySource:
    return KitchenCLIApp(lang or DEFAULT_LANG).make_inventory_source(args, lang=lang)


def build_parser(lang: str | None = DEFAULT_LANG) -> argparse.ArgumentParser:
    return KitchenCLIApp(lang or DEFAULT_LANG).build_parser()


def collect_recipe_item_ids(
    recipes_data: dict,
    include_accepts: bool = True,
) -> set[str]:
    result = set()

    for recipe in recipes_data.get("recipes", []):
        for ingredient in recipe.get("ingredients", []):
            item_id = ingredient.get("item")

            if item_id:
                result.add(item_id)

            if include_accepts:
                for accepted_id in ingredient.get("accepts", []):
                    result.add(accepted_id)

    return result


def find_unknown_recipe_items(recipe_item_ids: set[str]) -> set[str]:
    known_ids = set(cnst.INGREDIENTS.keys()) | set(cnst.CATEGORIES.keys())
    return recipe_item_ids - known_ids


def humanize_id(item_id: str) -> str:
    return item_id.replace("_", " ")


def guess_groups(item_id: str) -> list[str]:
    guesses = []

    if item_id.startswith("ground_"):
        guesses.extend(["minced_meat", "meat"])

    if "sausage" in item_id:
        guesses.extend(["sausage_product", "meat_product"])

    if any(word in item_id for word in ["herring", "mackerel", "tuna", "hake", "capelin", "salmon", "fish"]):
        guesses.append("fish")

    if any(word in item_id for word in ["tomato", "salsa"]):
        guesses.extend(["tomato_base", "vegetable", "sauce"])

    if item_id in {"bread", "breadcrumbs", "lavash", "flatbread", "flour", "tortilla", "naan"}:
        guesses.append("bread_base")

    if item_id in {"pasta", "noodle", "rice", "bulgur", "corn", "oats"}:
        guesses.append("grain")

    if item_id in {"beans", "chickpea", "lentil", "peas", "pea"}:
        guesses.append("legume")

    if item_id in {"yogurt", "milk", "cream", "cheese", "cottage_cheese", "hard_cheese"}:
        guesses.append("dairy")

    if item_id in {"eggplant", "okra", "leek", "dill", "avocado", "apple", "berry", "fruit"}:
        guesses.append("vegetable")

    if item_id in {"mayonnaise", "bechamel_sauce", "soy_sauce"}:
        guesses.append("sauce")

    return sorted(set(guesses))


def print_ingredient_stubs(unknown_ids: set[str]) -> None:
    print()
    print("Заготовки для INGREDIENTS:")
    print("-" * 40)

    for item_id in sorted(unknown_ids):
        groups = guess_groups(item_id)

        print(f'"{item_id}": {{')
        print(f'    "name": "{humanize_id(item_id)}",')
        print(f'    "groups": {groups},')
        print("},")
        print()


def command_inspect_ingredients_legacy(args) -> None:
    recipes_data = load_yaml(args.recipes)
    recipe_item_ids = collect_recipe_item_ids(
        recipes_data=recipes_data,
        include_accepts=not args.no_accepts,
    )
    unknown_ids = find_unknown_recipe_items(recipe_item_ids)

    print()
    print("Проверка ингредиентов")
    print("=" * 40)
    print(f"Файл рецептов: {args.recipes}")
    print(f"Всего item_id в рецептах: {len(recipe_item_ids)}")
    print(f"Известно в constants.py: {len(recipe_item_ids - unknown_ids)}")
    print(f"Неизвестно: {len(unknown_ids)}")

    if not unknown_ids:
        print()
        print("Все ингредиенты и категории из рецептов известны.")
        return

    print()
    print("Неизвестные item_id:")
    print("-" * 40)

    for item_id in sorted(unknown_ids):
        print(f"- {item_id}")

    print_ingredient_stubs(unknown_ids)


def main() -> None:
    configure_console_output()
    cnst.validate_constants()
    app = KitchenCLIApp(lang=bootstrap_lang_from_argv())
    parser = app.build_parser()
    args = parser.parse_args()
    args.lang = resolve_lang(args)
    args.func(args)


if __name__ == "__main__":
    main()
