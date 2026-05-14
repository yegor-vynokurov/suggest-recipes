from __future__ import annotations

import argparse
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from src.kitchen import constants as cnst
from src.kitchen.cli_support import CliRuntime
from src.kitchen.i18n import DEFAULT_LANG, SUPPORTED_LANGUAGES, normalize_language
from src.kitchen.recipe_validation import validate_accept_categories
from src.kitchen.yaml_store import DEFAULT_YAML_STORE, YamlStore


DEFAULT_RECIPES_DIR = Path("data/recipes")
DEFAULT_OUTPUT_PATH = DEFAULT_RECIPES_DIR / "read.yaml"

SKIP_FILENAMES = {
    "read.yaml",
    "read.yml",
}


@dataclass
class RecipeBundleService:
    recipes_dir: Path = DEFAULT_RECIPES_DIR
    output_path: Path = DEFAULT_OUTPUT_PATH
    lang: str = DEFAULT_LANG
    yaml_store: YamlStore = field(default_factory=lambda: DEFAULT_YAML_STORE)

    def __post_init__(self) -> None:
        self.recipes_dir = Path(self.recipes_dir)
        self.output_path = Path(self.output_path)
        self.runtime = CliRuntime(self.lang)

    @staticmethod
    def normalize_cuisine_list(value: str | list[str] | None) -> list[str]:
        if value is None:
            return ["all"]

        if isinstance(value, str):
            parts = value.split(",")
        else:
            parts = []
            for item in value:
                parts.extend(str(item).split(","))

        result = [
            part.strip().lower()
            for part in parts
            if part and part.strip()
        ]

        return result or ["all"]

    def cli_text(self, key: str, **kwargs: object) -> str:
        return self.runtime.text(key, **kwargs)

    def cuisine_label(self, cuisine_id: str) -> str:
        return self.runtime.cuisine_label(cuisine_id)

    def load_yaml(self, path: Path) -> dict[str, Any]:
        return self.yaml_store.load(path)

    def save_yaml(self, path: Path, data: dict[str, Any]) -> None:
        self.yaml_store.save(path, data)

    def discover_recipe_files(self) -> list[Path]:
        files: list[Path] = []

        for pattern in ("recipe_templates_*.yaml", "recipe_templates_*.yml"):
            for path in self.recipes_dir.glob(pattern):
                if path.name in SKIP_FILENAMES:
                    continue
                files.append(path)

        return sorted(set(files))

    @staticmethod
    def primary_cuisine_from_recipe_file(path: Path) -> str:
        stem = path.stem
        if stem.startswith("recipe_templates_"):
            rest = stem.removeprefix("recipe_templates_")
            cuisine_guess = rest.split("_v")[0].lower()
            if cuisine_guess:
                return cuisine_guess
        return path.stem.lower()

    def cuisines_from_recipe_file(self, path: Path) -> set[str]:
        data = self.load_yaml(path)
        result: set[str] = set()

        metadata_cuisines = data.get("metadata", {}).get("cuisines", {})
        if isinstance(metadata_cuisines, dict):
            result.update(str(key).lower() for key in metadata_cuisines.keys())

        for recipe in data.get("recipes", []) or []:
            cuisine_values = recipe.get("facets", {}).get("cuisine", [])

            if isinstance(cuisine_values, str):
                cuisine_values = [cuisine_values]

            for cuisine in cuisine_values:
                result.add(str(cuisine).lower())

        stem = path.stem
        if stem.startswith("recipe_templates_"):
            rest = stem.removeprefix("recipe_templates_")
            cuisine_guess = rest.split("_v")[0].lower()
            if cuisine_guess:
                result.add(cuisine_guess)

        return result

    def list_available_cuisines(self) -> dict[str, list[str]]:
        result: dict[str, list[str]] = {}

        for path in self.discover_recipe_files():
            cuisine = self.primary_cuisine_from_recipe_file(path)
            result.setdefault(cuisine, []).append(path.name)

        return {
            cuisine: sorted(files)
            for cuisine, files in sorted(result.items())
        }

    def should_include_file(
        self,
        path: Path,
        selected_cuisines: list[str],
        include_pantry: bool = True,
    ) -> bool:
        if "all" in selected_cuisines:
            return True

        file_cuisines = {self.primary_cuisine_from_recipe_file(path)}

        if include_pantry and "pantry" in file_cuisines:
            return True

        return bool(file_cuisines & set(selected_cuisines))

    @staticmethod
    def recipe_matches_selected_cuisine(
        recipe: dict[str, Any],
        selected_cuisines: list[str],
        include_pantry: bool = True,
    ) -> bool:
        if "all" in selected_cuisines:
            return True

        cuisine_values = recipe.get("facets", {}).get("cuisine", [])

        if isinstance(cuisine_values, str):
            cuisine_values = [cuisine_values]

        recipe_cuisines = {
            str(value).lower()
            for value in cuisine_values
        }

        if include_pantry and ("pantry" in recipe_cuisines or not recipe_cuisines):
            return True

        return bool(recipe_cuisines & set(selected_cuisines))

    def collect_source_metadata(self, source_files: list[Path]) -> dict[str, Any]:
        cuisines: dict[str, str] = {}

        for path in source_files:
            data = self.load_yaml(path)
            metadata_cuisines = data.get("metadata", {}).get("cuisines", {})

            if isinstance(metadata_cuisines, dict):
                cuisines.update(metadata_cuisines)

            for cuisine in self.cuisines_from_recipe_file(path):
                cuisines.setdefault(cuisine, cuisine)

        return {
            "source_files": [path.name for path in source_files],
            "cuisines": dict(sorted(cuisines.items())),
        }

    def _selected_source_files(
        self,
        cuisines: str | list[str] | None,
        include_pantry: bool,
    ) -> tuple[list[str], list[Path]]:
        selected_cuisines = self.normalize_cuisine_list(cuisines)

        if not self.recipes_dir.exists():
            raise FileNotFoundError(
                self.cli_text("recipes_dir_not_found", recipes_dir=self.recipes_dir)
            )

        source_files = [
            path
            for path in self.discover_recipe_files()
            if self.should_include_file(
                path,
                selected_cuisines=selected_cuisines,
                include_pantry=include_pantry,
            )
        ]

        if not source_files:
            available = self.list_available_cuisines()
            raise ValueError(
                self.cli_text(
                    "no_recipe_files_for_cuisines",
                    selected=selected_cuisines,
                    available=sorted(available),
                )
            )

        return selected_cuisines, source_files

    def build_bundle(
        self,
        cuisines: str | list[str] | None = "all",
        include_pantry: bool = True,
        fail_on_duplicate_ids: bool = True,
        output_path: Path | None = None,
    ) -> dict[str, Any]:
        selected_cuisines, source_files = self._selected_source_files(cuisines, include_pantry)
        bundle_output = Path(output_path) if output_path is not None else self.output_path

        recipes: list[dict[str, Any]] = []
        seen_ids: dict[str, str] = {}
        duplicate_ids: list[str] = []

        for path in source_files:
            data = self.load_yaml(path)
            validate_accept_categories(data, path)

            for recipe in data.get("recipes", []) or []:
                if not self.recipe_matches_selected_cuisine(
                    recipe,
                    selected_cuisines=selected_cuisines,
                    include_pantry=include_pantry,
                ):
                    continue

                recipe_id = recipe.get("id")

                if not recipe_id:
                    raise ValueError(
                        self.cli_text("recipe_without_id_in_file", file_name=path.name)
                    )

                if recipe_id in seen_ids:
                    duplicate_ids.append(f"{recipe_id}: {seen_ids[recipe_id]} + {path.name}")
                    continue

                seen_ids[recipe_id] = path.name

                copied_recipe = dict(recipe)
                copied_recipe.setdefault("source_file", path.name)
                recipes.append(copied_recipe)

        if duplicate_ids and fail_on_duplicate_ids:
            text = "\n".join(duplicate_ids)
            raise ValueError(self.cli_text("duplicate_recipe_ids", text=text))

        source_metadata = self.collect_source_metadata(source_files)
        bundle = {
            "metadata": {
                "version": "read",
                "kind": "recipe_bundle",
                "purpose": "Generated recipe bundle for RecipeEngine.",
                "selected_cuisines": selected_cuisines,
                "include_pantry": include_pantry,
                "source_files": source_metadata["source_files"],
                "cuisines": source_metadata["cuisines"],
                "recipe_count": len(recipes),
                "note": "Generated file. Do not edit manually; edit source recipe_templates_*.yaml instead.",
            },
            "recipes": recipes,
        }
        self.save_yaml(bundle_output, bundle)

        return {
            "output_path": str(bundle_output),
            "selected_cuisines": selected_cuisines,
            "include_pantry": include_pantry,
            "source_files": [str(path) for path in source_files],
            "recipe_count": len(recipes),
            "duplicates_skipped": duplicate_ids,
        }

    def copy_single_cuisine_file(
        self,
        cuisine: str,
        include_pantry: bool = False,
        output_path: Path | None = None,
    ) -> dict[str, Any]:
        selected = self.normalize_cuisine_list(cuisine)
        target_output = Path(output_path) if output_path is not None else self.output_path

        if len(selected) != 1 or selected[0] == "all":
            raise ValueError(self.cli_text("copy_single_requires_one_cuisine"))

        files = [
            path
            for path in self.discover_recipe_files()
            if self.should_include_file(path, selected, include_pantry=include_pantry)
        ]
        cuisine_files = [
            path
            for path in files
            if selected[0] in self.cuisines_from_recipe_file(path)
        ]

        if len(cuisine_files) != 1:
            raise ValueError(
                self.cli_text(
                    "copy_single_expected_one_file",
                    cuisine=selected[0],
                    files=[p.name for p in cuisine_files],
                )
            )

        target_output.parent.mkdir(parents=True, exist_ok=True)
        validate_accept_categories(self.load_yaml(cuisine_files[0]), cuisine_files[0])
        shutil.copyfile(cuisine_files[0], target_output)

        return {
            "output_path": str(target_output),
            "source_files": [str(cuisine_files[0])],
            "selected_cuisines": selected,
            "copied": True,
        }


def bootstrap_lang_from_argv(argv: list[str] | None = None) -> str:
    return CliRuntime.bootstrap_lang_from_argv(argv)


def cli_text(key: str, lang: str | None = DEFAULT_LANG, **kwargs: object) -> str:
    return CliRuntime(lang).text(key, **kwargs)


def cuisine_label(cuisine_id: str, lang: str | None = DEFAULT_LANG) -> str:
    return CliRuntime(lang).cuisine_label(cuisine_id)


def configure_console_output() -> None:
    CliRuntime.configure_console_output()


def normalize_cuisine_list(value: str | list[str] | None) -> list[str]:
    return RecipeBundleService.normalize_cuisine_list(value)


def list_available_cuisines(recipes_dir: Path = DEFAULT_RECIPES_DIR) -> dict[str, list[str]]:
    return RecipeBundleService(recipes_dir=recipes_dir).list_available_cuisines()


def build_recipe_bundle(
    cuisines: str | list[str] | None = "all",
    recipes_dir: Path = DEFAULT_RECIPES_DIR,
    output_path: Path = DEFAULT_OUTPUT_PATH,
    include_pantry: bool = True,
    fail_on_duplicate_ids: bool = True,
    lang: str | None = DEFAULT_LANG,
) -> dict[str, Any]:
    service = RecipeBundleService(
        recipes_dir=recipes_dir,
        output_path=output_path,
        lang=normalize_language(lang),
    )
    return service.build_bundle(
        cuisines=cuisines,
        include_pantry=include_pantry,
        fail_on_duplicate_ids=fail_on_duplicate_ids,
    )


def copy_single_recipe_file(
    cuisine: str,
    recipes_dir: Path = DEFAULT_RECIPES_DIR,
    output_path: Path = DEFAULT_OUTPUT_PATH,
    include_pantry: bool = False,
    lang: str | None = DEFAULT_LANG,
) -> dict[str, Any]:
    service = RecipeBundleService(
        recipes_dir=recipes_dir,
        output_path=output_path,
        lang=normalize_language(lang),
    )
    return service.copy_single_cuisine_file(
        cuisine=cuisine,
        include_pantry=include_pantry,
        output_path=output_path,
    )


def build_parser(lang: str | None = DEFAULT_LANG) -> argparse.ArgumentParser:
    runtime = CliRuntime(lang or DEFAULT_LANG)

    root_language_parent = argparse.ArgumentParser(add_help=False)
    root_language_parent.add_argument(
        "--lang",
        choices=SUPPORTED_LANGUAGES,
        default=DEFAULT_LANG,
        help=runtime.text("language_help"),
    )

    subcommand_language_parent = argparse.ArgumentParser(add_help=False)
    subcommand_language_parent.add_argument(
        "--lang",
        choices=SUPPORTED_LANGUAGES,
        default=argparse.SUPPRESS,
        help=runtime.text("language_help"),
    )

    parser = argparse.ArgumentParser(
        description=runtime.text("recipe_collection_app_description"),
        parents=[root_language_parent],
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    build_command_parser = subparsers.add_parser(
        "build",
        help=runtime.text("help.build_recipes_command"),
        parents=[subcommand_language_parent],
    )
    build_command_parser.add_argument(
        "--cuisine",
        "--cuisines",
        dest="cuisines",
        default="all",
        help=runtime.text("help.cuisines_option"),
    )
    build_command_parser.add_argument(
        "--recipes-dir",
        default=str(DEFAULT_RECIPES_DIR),
        help=runtime.text("help.recipes_dir"),
    )
    build_command_parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT_PATH),
        help=runtime.text("help.output"),
    )
    build_command_parser.add_argument(
        "--no-pantry",
        action="store_true",
        help=runtime.text("help.no_pantry"),
    )
    build_command_parser.add_argument(
        "--allow-duplicate-ids",
        action="store_true",
        help=runtime.text("help.allow_duplicate_ids"),
    )

    list_parser = subparsers.add_parser(
        "list",
        help=runtime.text("help.list_cuisines_command"),
        parents=[subcommand_language_parent],
    )
    list_parser.add_argument(
        "--recipes-dir",
        default=str(DEFAULT_RECIPES_DIR),
        help=runtime.text("help.recipes_dir"),
    )

    return parser


def main() -> None:
    configure_console_output()
    parser = build_parser(lang=bootstrap_lang_from_argv())
    args = parser.parse_args()
    args.lang = normalize_language(getattr(args, "lang", DEFAULT_LANG))

    service = RecipeBundleService(
        recipes_dir=Path(getattr(args, "recipes_dir", DEFAULT_RECIPES_DIR)),
        output_path=Path(getattr(args, "output", DEFAULT_OUTPUT_PATH)),
        lang=args.lang,
    )

    if args.command == "list":
        available = service.list_available_cuisines()

        if not available:
            print(service.cli_text("no_cuisines_found"))
            return

        print(f"{service.cli_text('available_cuisines_title')}:")
        for cuisine in available:
            print(f"- {service.cuisine_label(cuisine)}")
        return

    result = service.build_bundle(
        cuisines=args.cuisines,
        include_pantry=not args.no_pantry,
        fail_on_duplicate_ids=not args.allow_duplicate_ids,
    )

    print(service.cli_text("recipe_bundle_built"))
    print(
        f"{service.cli_text('cuisines_label')}: "
        f"{', '.join(service.cuisine_label(cuisine) for cuisine in result['selected_cuisines'])}"
    )
    print(f"{service.cli_text('recipe_count_label')}: {result['recipe_count']}")
    print(f"{service.cli_text('file_label')}: {result['output_path']}")
    print(f"{service.cli_text('sources_label')}:")
    for source in result["source_files"]:
        print(f"- {source}")


if __name__ == "__main__":
    main()
