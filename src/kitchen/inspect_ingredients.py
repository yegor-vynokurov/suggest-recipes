from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
import re
import sys
from typing import Any

try:
    from src.kitchen import constants as cnsts
    from src.kitchen.cli_support import CliRuntime
    from src.kitchen.yaml_store import DEFAULT_YAML_STORE
except ModuleNotFoundError:
    repo_root = Path(__file__).resolve().parents[2]
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    from src.kitchen import constants as cnsts
    from src.kitchen.cli_support import CliRuntime
    from src.kitchen.yaml_store import DEFAULT_YAML_STORE

DEFAULT_RECIPES_PATH = cnsts.ING_PATH
DEFAULT_INGREDIENTS_DIR = cnsts.INGREDIENTS_DIR
DEFAULT_MERGED_PATH = cnsts.INGREDIENTS_DATA_PATH
DEFAULT_DRAFT_DIR = DEFAULT_INGREDIENTS_DIR / "_drafts"
LEGACY_CYRILLIC_RE = re.compile(r"[А-Яа-яІіЇїЄєҐґ]")


def configure_console_output() -> None:
    CliRuntime.configure_console_output()


TARGET_FILES = {
    "meat_poultry": "ingredients_meat_poultry.yaml",
    "fish_seafood": "ingredients_fish_seafood.yaml",
    "dairy_eggs": "ingredients_dairy_eggs.yaml",
    "legumes": "ingredients_legumes.yaml",
    "grains_bread": "ingredients_grains_bread.yaml",
    "vegetables_mushrooms_fruits": "ingredients_vegetables_mushrooms_fruits.yaml",
    "fats_oils": "ingredients_fats_oils.yaml",
    "nuts_seeds_sweeteners": "ingredients_nuts_seeds_sweeteners.yaml",
    "sauces_condiments": "ingredients_sauces_condiments.yaml",
    "spices_herbs": "ingredients_spices_herbs.yaml",
    "technical": "ingredients_technical.yaml",
    "prepared_components": "ingredients_prepared_components.yaml",
    "uncategorized": "ingredients_uncategorized.yaml",
}


# Ручные подсказки для украинской ветки и похожих будущих рецептов.
# Можно расширять без страха: это только инспектор, он не влияет на RecipeEngine.
def _catalog_suggestion(
    item_id: str,
    groups: list[str],
    target: str,
    *,
    fallback_name: str | None = None,
    fallback_name_uk: str | None = None,
    aliases: list[str] | None = None,
    aliases_uk: list[str] | None = None,
) -> dict[str, Any]:
    item = cnsts.INGREDIENTS.get(item_id, {})

    suggestion = {
        "name": item.get("name") or fallback_name or item_id.replace("_", " "),
        "groups": groups,
        "target": target,
        "aliases": list(item.get("aliases", []) or aliases or []),
    }

    name_uk = item.get("name_uk") or fallback_name_uk or ""
    if isinstance(name_uk, str) and name_uk.strip():
        suggestion["name_uk"] = name_uk.strip()

    aliases_uk_values = list(item.get("aliases_uk", []) or aliases_uk or [])
    if aliases_uk_values:
        suggestion["aliases_uk"] = aliases_uk_values

    return suggestion


KNOWN_SUGGESTIONS: dict[str, dict[str, Any]] = {
    # meat / pork details
    "pork_ears": _catalog_suggestion("pork_ears", ["offal", "broth_meat"], "meat_poultry"),
    "pork_tail": _catalog_suggestion("pork_tail", ["offal", "broth_meat"], "meat_poultry"),
    "pork_trotters": _catalog_suggestion("pork_trotters", ["offal", "broth_meat"], "meat_poultry"),
    "pork_shank": _catalog_suggestion("pork_shank", ["red_meat", "meat_piece", "broth_meat"], "meat_poultry"),
    "pork_hock": _catalog_suggestion(
        "pork_hock",
        ["red_meat", "meat_piece", "meat_on_bone", "broth_meat"],
        "meat_poultry",
    ),
    "pork_belly": _catalog_suggestion(
        "pork_belly",
        ["red_meat", "meat_piece", "animal_fat", "fat"],
        "meat_poultry",
    ),
    "salo": _catalog_suggestion("salo", ["animal_fat", "fat", "meat_product"], "fats_oils"),
    "pork_ribs": _catalog_suggestion(
        "pork_ribs",
        ["red_meat", "meat_piece", "meat_on_bone", "broth_meat"],
        "meat_poultry",
    ),
    "smoked_pork_ribs": _catalog_suggestion(
        "smoked_pork_ribs",
        ["meat_product", "prepared_meat", "red_meat", "meat_on_bone", "broth_meat"],
        "meat_poultry",
    ),
    "pork_chop": _catalog_suggestion("pork_chop", ["red_meat", "cutlet_meat"], "meat_poultry"),
    "beef_steak": _catalog_suggestion("beef_steak", ["red_meat", "cutlet_meat"], "meat_poultry"),
    "chicken_drumstick": _catalog_suggestion(
        "chicken_drumstick",
        ["poultry", "meat_piece", "meat_on_bone", "broth_meat"],
        "meat_poultry",
    ),
    "liver": _catalog_suggestion("liver", ["offal", "meat"], "meat_poultry"),
    "blood_sausage_base": _catalog_suggestion(
        "blood_sausage_base",
        ["sausage_product", "meat_product", "prepared_meat"],
        "meat_poultry",
    ),

    # sausage / components
    "sausage_casing": _catalog_suggestion(
        "sausage_casing",
        ["prepared_component"],
        "prepared_components",
    ),

    # grains / legumes / bread
    "millet": _catalog_suggestion("millet", ["grain"], "grains_bread"),
    "barley": _catalog_suggestion("barley", ["grain"], "grains_bread"),
    "split_peas": _catalog_suggestion("split_peas", ["pea_chickpea", "legume"], "legumes"),
    "rye_bread": _catalog_suggestion("rye_bread", ["bread_base"], "grains_bread"),

    # vegetables / greens / fruits
    "sauerkraut": _catalog_suggestion(
        "sauerkraut",
        ["cabbage_family", "pickled_vegetable", "fermented_condiment", "vegetable"],
        "vegetables_mushrooms_fruits",
    ),
    "pickled_cucumber": _catalog_suggestion(
        "pickled_cucumber",
        ["vegetable", "pickled_vegetable", "fermented_condiment", "acid_souring"],
        "vegetables_mushrooms_fruits",
    ),
    "sorrel": _catalog_suggestion("sorrel", ["leafy_green", "acid_souring"], "vegetables_mushrooms_fruits"),
    "nettle": _catalog_suggestion("nettle", ["leafy_green", "fresh_herb"], "vegetables_mushrooms_fruits"),
    "beet_greens": _catalog_suggestion("beet_greens", ["leafy_green"], "vegetables_mushrooms_fruits"),
    "cherry": _catalog_suggestion("cherry", ["fresh_fruit", "fruit"], "vegetables_mushrooms_fruits"),
    "berries": _catalog_suggestion("berries", ["fresh_fruit", "fruit", "berry"], "vegetables_mushrooms_fruits"),
    "prunes": _catalog_suggestion("prunes", ["dried_fruit_group", "fruit"], "vegetables_mushrooms_fruits"),

    # sweeteners / seeds
    "poppy_seed": _catalog_suggestion("poppy_seed", ["seed"], "nuts_seeds_sweeteners"),
    "honey": _catalog_suggestion("honey", ["sweetener"], "nuts_seeds_sweeteners"),

    # seasonings / sauces
    "horseradish": _catalog_suggestion(
        "horseradish",
        ["pungent_spice", "seasoning", "root_vegetable"],
        "spices_herbs",
    ),
    "mustard": _catalog_suggestion("mustard", ["sauce", "pungent_spice"], "sauces_condiments"),
    "bread_dumpling": _catalog_suggestion(
        "bread_dumpling",
        ["bread_base", "prepared_component"],
        "grains_bread",
    ),
    "potato_dumpling": _catalog_suggestion(
        "potato_dumpling",
        ["bread_base", "prepared_component"],
        "grains_bread",
    ),
    "rye_flour": _catalog_suggestion("rye_flour", ["flour_group"], "grains_bread"),
    "gingerbread": _catalog_suggestion("gingerbread", ["bread_base", "sweetener"], "grains_bread"),
    "marjoram": _catalog_suggestion("marjoram", ["herb"], "spices_herbs"),
    "potato_salad": _catalog_suggestion("potato_salad", ["prepared_component"], "prepared_components"),
    "sev": _catalog_suggestion(
        "sev",
        ["prepared_component", "legume"],
        "prepared_components",
        fallback_name="sev",
        fallback_name_uk="\u0441\u0435\u0432",
    ),
}



ROLE_ORDER = ["main", "required", "addition", "spice", "optional", "accepts"]
AMOUNT_ORDER = ["spice", "little", "normal", "many"]

FISH_ITEM_TOKENS = {
    "fish",
    "cod",
    "herring",
    "salmon",
    "trout",
    "anchovy",
    "mackerel",
    "sardine",
    "sardines",
    "tuna",
    "hake",
    "sole",
    "plaice",
    "pike",
    "carp",
    "catfish",
    "haddock",
    "vendace",
    "skrei",
    "roe",
    "roes",
    "milt",
}
FISH_PRODUCT_TOKENS = {"smoked", "salted", "dried", "pickled", "marinated", "fermented", "stock"}
CRUSTACEAN_TOKENS = {"shrimp", "prawn", "prawns", "langoustine", "crayfish", "crab", "lobster", "krill"}
SEAFOOD_TOKENS = CRUSTACEAN_TOKENS | {"mussel", "mussels", "clam", "clams", "scallop", "scallops", "shellfish", "squid", "octopus", "snail", "snails"}
FLATBREAD_TOKENS = {"flatbread", "lavash", "chapati", "pita", "naan", "lefse", "tortilla", "piadina", "yufka"}
BERRY_TOKENS = {
    "berry",
    "berries",
    "strawberry",
    "raspberry",
    "blueberry",
    "blueberries",
    "cranberry",
    "cranberries",
    "lingonberry",
    "lingonberries",
    "cloudberry",
    "cloudberries",
    "currant",
    "currants",
    "blackberry",
    "blackberries",
}
JAM_TOKENS = {"jam", "jelly", "marmalade", "preserve", "preserves"}
PICKLED_TOKENS = {"pickled", "marinated"}
PICKLED_VEGETABLE_TOKENS = {
    "cucumber",
    "beet",
    "cabbage",
    "cauliflower",
    "broccoli",
    "onion",
    "carrot",
    "pepper",
    "tomato",
    "vegetable",
    "vegetables",
}
PREPARED_MEAT_TOKENS = {
    "sausage",
    "sausages",
    "salami",
    "prosciutto",
    "ham",
    "bacon",
    "pancetta",
    "confit",
    "jerky",
    "pate",
    "pastrami",
    "bresaola",
    "sucuk",
    "wurst",
    "frankfurter",
}
SAUSAGE_TOKENS = {"sausage", "sausages", "salami", "sucuk", "wursts", "wurst", "frankfurter", "hotdog"}
MEAT_ON_BONE_TOKENS = {"rib", "ribs", "shank", "shanks", "drumstick", "drumsticks", "wing", "wings", "bone", "bones", "hock", "trotter", "trotters"}
POULTRY_TOKENS = {"chicken", "duck", "goose", "turkey"}
RED_MEAT_TOKENS = {"beef", "veal", "pork", "lamb", "mutton"}

GROUP_TARGET_PRIORITY: list[tuple[set[str], str]] = [
    (
        {
            "poultry",
            "red_meat",
            "meat",
            "meat_piece",
            "meat_product",
            "sausage_product",
            "prepared_meat",
            "broth_meat",
            "cutlet_meat",
            "offal",
            "minced_meat",
            "meat_on_bone",
        },
        "meat_poultry",
    ),
    (
        {
            "fish",
            "seafood",
            "crustacean",
            "fish_product",
            "marinated_fish",
            "salted_fish",
            "dried_fish",
            "smoked_fish",
        },
        "fish_seafood",
    ),
    ({"dairy", "milk_like", "cream_like", "fermented_dairy", "sour_cream_like", "egg", "cheese"}, "dairy_eggs"),
    ({"legume", "bean", "lentil", "pea_chickpea"}, "legumes"),
    ({"grain", "bread_base", "flatbread", "flour_group", "rice_group", "wheat_group", "corn_group", "base_starch", "pasta_noodle"}, "grains_bread"),
    (
        {
            "vegetable",
            "pickled_vegetable",
            "root_vegetable",
            "leafy_green",
            "nightshade_vegetable",
            "cabbage_family",
            "squash_family",
            "mushroom",
            "fruit",
            "fresh_fruit",
            "berry",
            "dried_fruit_group",
            "aromatic_vegetable",
        },
        "vegetables_mushrooms_fruits",
    ),
    ({"animal_fat", "plant_oil", "fat"}, "fats_oils"),
    ({"seed", "nuts", "sweetener"}, "nuts_seeds_sweeteners"),
    ({"sauce", "fruit_preserve", "acid_souring", "fermented_condiment", "tomato_base", "chutney_group"}, "sauces_condiments"),
    (
        {
            "seasoning",
            "spice",
            "hot_spice",
            "pungent_spice",
            "mild_spice",
            "warm_spice",
            "earthy_spice",
            "seed_spice",
            "color_spice",
            "aromatic_spice",
            "masala_mix",
            "herb",
            "fresh_herb",
            "dried_herb",
        },
        "spices_herbs",
    ),
    ({"prepared_component"}, "prepared_components"),
    ({"technical"}, "technical"),
]


@dataclass
class UsageExample:
    recipe_id: str
    field: str
    role: str
    amount: str
    related_item_id: str | None = None


@dataclass
class Usage:
    item_id: str
    roles: Counter
    recipes: set[str]
    appears_as_item: bool = False
    appears_as_accept: bool = False
    amounts: Counter = field(default_factory=Counter)
    accepted_by: Counter = field(default_factory=Counter)
    item_hits: int = 0
    accept_hits: int = 0
    examples: list[UsageExample] = field(default_factory=list)

    @property
    def priority(self) -> str:
        if self.roles.get("main"):
            return "main"
        if self.roles.get("required"):
            return "required"
        if self.roles.get("addition"):
            return "addition"
        if self.roles.get("spice"):
            return "spice"
        if self.appears_as_accept:
            return "accepts"
        return "unknown"

    @property
    def appearance(self) -> str:
        if self.appears_as_item and self.appears_as_accept:
            return "item+accepts"
        if self.appears_as_item:
            return "item"
        if self.appears_as_accept:
            return "accepts"
        return "unknown"

    def add_example(
        self,
        recipe_id: str,
        field: str,
        role: str,
        amount: str,
        related_item_id: str | None = None,
        limit: int = 6,
    ) -> None:
        if len(self.examples) >= limit:
            return

        self.examples.append(
            UsageExample(
                recipe_id=recipe_id,
                field=field,
                role=role,
                amount=amount,
                related_item_id=related_item_id,
            )
        )


@dataclass(frozen=True)
class LocalizationIssue:
    file_name: str
    section: str
    entry_id: str
    issue_type: str
    field_name: str
    value: str = ""


@dataclass
class LocalizationAuditReport:
    issues: list[LocalizationIssue]
    issue_counts: Counter = field(default_factory=Counter)
    file_counts: Counter = field(default_factory=Counter)


def _has_cyrillic(text: str) -> bool:
    return bool(LEGACY_CYRILLIC_RE.search(text))


def _has_placeholder_text(text: str) -> bool:
    return "?" in text


def _is_legacy_localized_text(text: str) -> bool:
    stripped = text.strip()
    if not stripped:
        return False
    return _has_cyrillic(stripped) or _has_placeholder_text(stripped)


def _scan_localized_entry(
    *,
    file_name: str,
    section: str,
    entry_id: str,
    entry: dict[str, Any],
    require_name_uk: bool,
) -> list[LocalizationIssue]:
    issues: list[LocalizationIssue] = []

    name_value = entry.get("name")
    if isinstance(name_value, dict):
        issues.append(
            LocalizationIssue(
                file_name=file_name,
                section=section,
                entry_id=entry_id,
                issue_type="legacy_name",
                field_name="name",
                value="localized map",
            )
        )
    elif not isinstance(name_value, str) or not name_value.strip():
        issues.append(
            LocalizationIssue(
                file_name=file_name,
                section=section,
                entry_id=entry_id,
                issue_type="missing_name",
                field_name="name",
            )
        )
    elif _is_legacy_localized_text(name_value):
        issues.append(
            LocalizationIssue(
                file_name=file_name,
                section=section,
                entry_id=entry_id,
                issue_type="legacy_name",
                field_name="name",
                value=name_value.strip(),
            )
        )

    if require_name_uk:
        name_uk_value = entry.get("name_uk")
        if not isinstance(name_uk_value, str) or not name_uk_value.strip():
            issues.append(
                LocalizationIssue(
                    file_name=file_name,
                    section=section,
                    entry_id=entry_id,
                    issue_type="missing_name_uk",
                    field_name="name_uk",
                )
            )

    comment_value = entry.get("comment")
    if isinstance(comment_value, dict):
        issues.append(
            LocalizationIssue(
                file_name=file_name,
                section=section,
                entry_id=entry_id,
                issue_type="legacy_comment",
                field_name="comment",
                value="localized map",
            )
        )
    elif isinstance(comment_value, str) and comment_value.strip() and _is_legacy_localized_text(comment_value):
        issues.append(
            LocalizationIssue(
                file_name=file_name,
                section=section,
                entry_id=entry_id,
                issue_type="legacy_comment",
                field_name="comment",
                value=comment_value.strip(),
            )
        )

    aliases_value = entry.get("aliases")
    if aliases_value is not None:
        if not isinstance(aliases_value, list):
            issues.append(
                LocalizationIssue(
                    file_name=file_name,
                    section=section,
                    entry_id=entry_id,
                    issue_type="invalid_aliases",
                    field_name="aliases",
                    value=type(aliases_value).__name__,
                )
            )
        else:
            for alias in aliases_value:
                if not isinstance(alias, str) or not alias.strip():
                    issues.append(
                        LocalizationIssue(
                            file_name=file_name,
                            section=section,
                            entry_id=entry_id,
                            issue_type="invalid_aliases",
                            field_name="aliases",
                            value=repr(alias),
                        )
                    )
                    continue

                if _is_legacy_localized_text(alias):
                    issues.append(
                        LocalizationIssue(
                            file_name=file_name,
                            section=section,
                            entry_id=entry_id,
                            issue_type="legacy_aliases",
                            field_name="aliases",
                            value=alias.strip(),
                        )
                    )

    aliases_uk_value = entry.get("aliases_uk")
    if aliases_uk_value is not None and not isinstance(aliases_uk_value, list):
        issues.append(
            LocalizationIssue(
                file_name=file_name,
                section=section,
                entry_id=entry_id,
                issue_type="invalid_aliases_uk",
                field_name="aliases_uk",
                value=type(aliases_uk_value).__name__,
            )
        )

    return issues


def audit_localized_sources(
    ingredients_dir: str | Path = DEFAULT_INGREDIENTS_DIR,
) -> LocalizationAuditReport:
    ingredients_dir = Path(ingredients_dir)
    issues: list[LocalizationIssue] = []

    categories_path = ingredients_dir / "ingredient_categories.yaml"
    categories_data = load_yaml(categories_path)
    for category_id, category in (categories_data.get("categories", {}) or {}).items():
        if not isinstance(category, dict):
            issues.append(
                LocalizationIssue(
                    file_name=categories_path.name,
                    section="categories",
                    entry_id=category_id,
                    issue_type="invalid_entry",
                    field_name="entry",
                    value=type(category).__name__,
                )
            )
            continue

        issues.extend(
            _scan_localized_entry(
                file_name=categories_path.name,
                section="categories",
                entry_id=category_id,
                entry=category,
                require_name_uk=True,
            )
        )

    for path in sorted(ingredients_dir.glob("ingredients_*.yaml")):
        if path.name == DEFAULT_MERGED_PATH.name:
            continue

        data = load_yaml(path)
        for item_id, ingredient in (data.get("ingredients", {}) or {}).items():
            if not isinstance(ingredient, dict):
                issues.append(
                    LocalizationIssue(
                        file_name=path.name,
                        section="ingredients",
                        entry_id=item_id,
                        issue_type="invalid_entry",
                        field_name="entry",
                        value=type(ingredient).__name__,
                    )
                )
                continue

            issues.extend(
                _scan_localized_entry(
                    file_name=path.name,
                    section="ingredients",
                    entry_id=item_id,
                    entry=ingredient,
                    require_name_uk=True,
                )
            )

    report = LocalizationAuditReport(issues=sorted(
        issues,
        key=lambda issue: (issue.issue_type, issue.file_name, issue.entry_id, issue.field_name),
    ))
    report.issue_counts.update(issue.issue_type for issue in report.issues)
    report.file_counts.update(issue.file_name for issue in report.issues)
    return report


def print_localization_audit_report(
    report: LocalizationAuditReport,
    *,
    example_limit: int = 24,
) -> None:
    if not report.issues:
        print("Localization audit passed: no missing name_uk or legacy localized fields.")
        return

    print("Localization audit found issues.")
    print()
    print("Issue summary:")
    for issue_type, count in sorted(report.issue_counts.items()):
        print(f"- {issue_type}: {count}")

    print()
    print("Files with issues:")
    for file_name, count in sorted(report.file_counts.items()):
        print(f"- {file_name}: {count}")

    print()
    print("Examples:")
    for issue in report.issues[:example_limit]:
        detail = f" value={issue.value!r}" if issue.value else ""
        print(
            f"- {issue.file_name}:{issue.section}.{issue.entry_id} "
            f"{issue.field_name} -> {issue.issue_type}{detail}"
        )

    remaining = len(report.issues) - example_limit
    if remaining > 0:
        print(f"... and {remaining} more.")


def load_yaml(path: str | Path) -> dict[str, Any]:
    return DEFAULT_YAML_STORE.load(path)


def save_yaml(path: str | Path, data: dict[str, Any]) -> None:
    DEFAULT_YAML_STORE.save(path, data)


def validate_ingredient_entries(ingredients: dict[str, Any], source_label: str | Path) -> None:
    errors: list[str] = []

    for item_id, item in ingredients.items():
        if not isinstance(item, dict):
            errors.append(f"{item_id}: expected dict, got {type(item).__name__}")
            continue

        if "name" not in item or "groups" not in item:
            if item_id.endswith(".yaml"):
                errors.append(
                    f"{item_id}: looks like a pasted draft/file block inside ingredients instead of an ingredient entry"
                )
            else:
                errors.append(f"{item_id}: missing required keys name/groups")
            continue

        if not isinstance(item.get("groups"), list):
            errors.append(f"{item_id}: groups must be a list")

    if errors:
        joined = "\n".join(f"- {error}" for error in errors)
        raise ValueError(f"Broken ingredients YAML in {source_label}:\n{joined}")


def load_known_ids(merged_path: str | Path) -> tuple[set[str], set[str], dict[str, Any]]:
    merged_path = Path(merged_path)
    if not merged_path.exists():
        raise FileNotFoundError(f"Не найден merged YAML ингредиентов: {merged_path}")

    data = load_yaml(merged_path)
    extra_top_level_keys = sorted(set(data) - {"metadata", "categories", "ingredients"})
    if extra_top_level_keys:
        joined = ", ".join(extra_top_level_keys)
        raise ValueError(
            f"Broken merged ingredients YAML: unexpected top-level keys in {merged_path}: {joined}. "
            f"Rebuild merged ingredients after fixing source YAML files."
        )

    ingredients = data.get("ingredients", {}) or {}
    categories = data.get("categories", {}) or {}
    validate_ingredient_entries(ingredients, merged_path)

    return set(ingredients), set(categories), data


def collect_recipe_usage(recipes_path: str | Path, include_accepts: bool = True) -> dict[str, Usage]:
    recipes_path = Path(recipes_path)
    if not recipes_path.exists():
        raise FileNotFoundError(f"Файл рецептов не найден: {recipes_path}")

    data = load_yaml(recipes_path)
    result: dict[str, Usage] = {}

    for recipe in data.get("recipes", []) or []:
        recipe_id = recipe.get("id", "<unknown_recipe>")

        for ingredient in recipe.get("ingredients", []) or []:
            item_id = ingredient.get("item")
            role = ingredient.get("role", "required")
            amount = ingredient.get("amount", "normal")

            if item_id:
                usage = result.setdefault(item_id, Usage(item_id=item_id, roles=Counter(), recipes=set()))
                usage.roles[role] += 1
                usage.amounts[amount] += 1
                usage.recipes.add(recipe_id)
                usage.appears_as_item = True
                usage.item_hits += 1
                usage.add_example(
                    recipe_id=recipe_id,
                    field="item",
                    role=role,
                    amount=amount,
                )

            if include_accepts:
                for accepted_id in ingredient.get("accepts", []) or []:
                    usage = result.setdefault(accepted_id, Usage(item_id=accepted_id, roles=Counter(), recipes=set()))
                    usage.roles["accepts"] += 1
                    usage.amounts[amount] += 1
                    usage.recipes.add(recipe_id)
                    usage.appears_as_accept = True
                    usage.accept_hits += 1
                    if item_id:
                        usage.accepted_by[item_id] += 1
                    usage.add_example(
                        recipe_id=recipe_id,
                        field="accept",
                        role=role,
                        amount=amount,
                        related_item_id=item_id,
                    )

    return result


def title_from_id(item_id: str) -> str:
    return item_id.replace("_", " ")


def item_tokens(item_id: str) -> set[str]:
    return {token for token in item_id.split("_") if token}


def singularize_token(token: str) -> str:
    if token.endswith("ies") and len(token) > 3:
        return token[:-3] + "y"
    if token.endswith("s") and len(token) > 3:
        return token[:-1]
    return token


def expanded_item_tokens(item_id: str) -> set[str]:
    tokens = item_tokens(item_id)
    expanded = set(tokens)
    for token in list(tokens):
        expanded.add(singularize_token(token))
    return expanded


def dedupe_groups(groups: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for group_id in groups:
        if not group_id or group_id in seen:
            continue
        result.append(group_id)
        seen.add(group_id)
    return result


def resolve_target_from_groups(groups: list[str]) -> str:
    group_set = set(groups)
    for known_groups, target in GROUP_TARGET_PRIORITY:
        if group_set & known_groups:
            return target
    return "uncategorized"


def build_suggestion(
    item_id: str,
    groups: list[str],
    *,
    reason: str,
    target: str | None = None,
    name: str | None = None,
    name_uk: str | None = None,
    aliases: list[str] | None = None,
    aliases_uk: list[str] | None = None,
    review: bool = True,
    confidence: str = "heuristic",
) -> dict[str, Any]:
    final_groups = dedupe_groups(groups)
    result = {
        "name": name or title_from_id(item_id),
        "groups": final_groups or ["uncategorized"],
        "target": target or resolve_target_from_groups(final_groups),
        "aliases": aliases or [],
        "review": review,
        "reason": reason,
        "confidence": confidence,
    }
    if name_uk is not None:
        result["name_uk"] = name_uk
    if aliases_uk is not None:
        result["aliases_uk"] = aliases_uk
    return result


def known_base_variants(item_id: str) -> list[tuple[str, str]]:
    variants: list[tuple[str, str]] = []

    for prefix in ("smoked", "salted", "pickled", "marinated", "dried", "fermented", "canned", "frozen", "ground"):
        prefix_text = f"{prefix}_"
        if item_id.startswith(prefix_text):
            variants.append((prefix, item_id[len(prefix_text) :]))

    for suffix, label in (
        ("_jam", "jam"),
        ("_jelly", "jam"),
        ("_preserve", "jam"),
        ("_sauce", "sauce"),
        ("_shells", "shells"),
    ):
        if item_id.endswith(suffix):
            variants.append((label, item_id[: -len(suffix)]))

    return variants


def known_item_groups(item_id: str) -> list[str]:
    item = cnsts.INGREDIENTS.get(item_id, {})
    return list(item.get("groups", []) or [])


def infer_from_known_base_item(item_id: str) -> dict[str, Any] | None:
    for variant_kind, base_id in known_base_variants(item_id):
        candidate_ids = [base_id]
        if "_" in base_id:
            tokens = base_id.split("_")
            singular_last = singularize_token(tokens[-1])
            candidate_ids.append("_".join(tokens[:-1] + [singular_last]))
        else:
            candidate_ids.append(singularize_token(base_id))

        for candidate_id in candidate_ids:
            base_groups = known_item_groups(candidate_id)
            if not base_groups:
                continue

            if variant_kind in {"jam"} and set(base_groups) & {"fruit", "fresh_fruit", "berry"}:
                return build_suggestion(
                    item_id,
                    ["sweetener", "sauce", "fruit_preserve"],
                    reason=f"derived from known base item {candidate_id} + jam/preserve suffix",
                    target="sauces_condiments",
                    confidence="derived",
                )

            if variant_kind == "shells" and set(base_groups) & {"seafood", "crustacean"}:
                return build_suggestion(
                    item_id,
                    ["seafood", "crustacean"],
                    reason=f"derived from known base item {candidate_id} + shells suffix",
                    target="fish_seafood",
                    confidence="derived",
                )

            if variant_kind in {"pickled", "marinated"}:
                if set(base_groups) & {"fish", "fish_product"}:
                    return build_suggestion(
                        item_id,
                        ["fish", "fish_product", "marinated_fish"],
                        reason=f"derived from known base item {candidate_id} + pickled/marinated prefix",
                        target="fish_seafood",
                        confidence="derived",
                    )
                if set(base_groups) & {"vegetable", "cabbage_family", "root_vegetable", "nightshade_vegetable"}:
                    return build_suggestion(
                        item_id,
                        ["vegetable", "pickled_vegetable", "fermented_condiment"],
                        reason=f"derived from known base item {candidate_id} + pickled/marinated prefix",
                        target="vegetables_mushrooms_fruits",
                        confidence="derived",
                    )

            if variant_kind == "smoked" and set(base_groups) & {"fish", "fish_product"}:
                return build_suggestion(
                    item_id,
                    ["fish", "fish_product", "smoked_fish"],
                    reason=f"derived from known base item {candidate_id} + smoked prefix",
                    target="fish_seafood",
                    confidence="derived",
                )

            if variant_kind == "salted" and set(base_groups) & {"fish", "fish_product"}:
                return build_suggestion(
                    item_id,
                    ["fish", "fish_product", "salted_fish"],
                    reason=f"derived from known base item {candidate_id} + salted prefix",
                    target="fish_seafood",
                    confidence="derived",
                )

            if variant_kind == "dried" and set(base_groups) & {"fish", "fish_product"}:
                return build_suggestion(
                    item_id,
                    ["fish", "fish_product", "dried_fish"],
                    reason=f"derived from known base item {candidate_id} + dried prefix",
                    target="fish_seafood",
                    confidence="derived",
                )

            if variant_kind == "fermented" and set(base_groups) & {"fish", "fish_product"}:
                return build_suggestion(
                    item_id,
                    ["fish", "fish_product", "fermented_condiment"],
                    reason=f"derived from known base item {candidate_id} + fermented prefix",
                    target="fish_seafood",
                    confidence="derived",
                )

    return None


def format_counter(counter: Counter, preferred_order: list[str] | None = None, limit: int | None = None) -> str:
    if not counter:
        return "-"

    items = list(counter.items())
    if preferred_order:
        order_index = {value: index for index, value in enumerate(preferred_order)}
        items.sort(key=lambda pair: (order_index.get(pair[0], len(order_index)), -pair[1], pair[0]))
    else:
        items.sort(key=lambda pair: (-pair[1], pair[0]))

    if limit is not None:
        items = items[:limit]

    return ", ".join(f"{key}:{value}" for key, value in items)


def format_examples(examples: list[UsageExample], limit: int = 3) -> str:
    preview: list[str] = []
    for example in examples[:limit]:
        if example.field == "accept":
            preview.append(
                f"accept:{example.role}/{example.amount}<-{example.related_item_id}@{example.recipe_id}"
            )
        else:
            preview.append(f"item:{example.role}/{example.amount}@{example.recipe_id}")

    if len(examples) > limit:
        preview.append(f"... +{len(examples) - limit}")

    return "; ".join(preview)


def infer_by_pattern(item_id: str, usage: Usage | None = None) -> dict[str, Any]:
    """
    Осторожная эвристика на будущее.
    Лучше ручных подсказок она быть не должна, но спасает от пустых строк.
    """
    if item_id in KNOWN_SUGGESTIONS:
        suggestion = dict(KNOWN_SUGGESTIONS[item_id])
        suggestion.setdefault("reason", "manual known suggestion")
        suggestion.setdefault("confidence", "manual")
        return suggestion

    derived = infer_from_known_base_item(item_id)
    if derived is not None:
        return derived

    if item_id.startswith("pork_"):
        tokens = expanded_item_tokens(item_id)
        groups = ["red_meat", "meat_piece"]
        if tokens & MEAT_ON_BONE_TOKENS:
            groups.append("meat_on_bone")
        if tokens & {"bone", "bones", "shank", "shanks", "hock", "ribs", "rib"}:
            groups.append("broth_meat")
        return build_suggestion(item_id, groups, reason="pork_* pattern", target="meat_poultry")

    if item_id.startswith("beef_"):
        tokens = expanded_item_tokens(item_id)
        groups = ["red_meat", "meat_piece"]
        if tokens & MEAT_ON_BONE_TOKENS:
            groups.append("meat_on_bone")
        if tokens & {"bone", "bones", "shank", "shanks"}:
            groups.append("broth_meat")
        return build_suggestion(item_id, groups, reason="beef_* pattern", target="meat_poultry")

    if item_id.startswith("chicken_"):
        tokens = expanded_item_tokens(item_id)
        groups = ["poultry", "meat_piece"]
        if tokens & MEAT_ON_BONE_TOKENS:
            groups.append("meat_on_bone")
        if tokens & {"bone", "bones", "shank", "shanks", "drumstick", "drumsticks"}:
            groups.append("broth_meat")
        return build_suggestion(item_id, groups, reason="chicken_* pattern", target="meat_poultry")

    tokens = expanded_item_tokens(item_id)

    if tokens & BERRY_TOKENS:
        return build_suggestion(
            item_id,
            ["fresh_fruit", "fruit", "berry"],
            reason="berry keyword pattern",
            target="vegetables_mushrooms_fruits",
        )

    if tokens & JAM_TOKENS:
        return build_suggestion(
            item_id,
            ["sweetener", "sauce", "fruit_preserve"],
            reason="jam/preserve keyword pattern",
            target="sauces_condiments",
        )

    if tokens & FLATBREAD_TOKENS:
        return build_suggestion(
            item_id,
            ["bread_base", "flatbread"],
            reason="flatbread keyword pattern",
            target="grains_bread",
        )

    if tokens & CRUSTACEAN_TOKENS:
        return build_suggestion(
            item_id,
            ["seafood", "crustacean"],
            reason="crustacean keyword pattern",
            target="fish_seafood",
        )

    if tokens & SEAFOOD_TOKENS:
        return build_suggestion(
            item_id,
            ["seafood"],
            reason="seafood keyword pattern",
            target="fish_seafood",
        )

    if tokens & FISH_ITEM_TOKENS:
        groups = ["fish"]
        if tokens & {"smoked"}:
            groups += ["fish_product", "smoked_fish"]
        elif tokens & {"salted"}:
            groups += ["fish_product", "salted_fish"]
        elif tokens & {"dried", "stock"}:
            groups += ["fish_product", "dried_fish"]
        elif tokens & {"pickled", "marinated"}:
            groups += ["fish_product", "marinated_fish"]
        elif tokens & {"fermented"}:
            groups += ["fish_product", "fermented_condiment"]

        return build_suggestion(
            item_id,
            groups,
            reason="fish keyword pattern",
            target="fish_seafood",
        )

    if tokens & PICKLED_TOKENS and tokens & PICKLED_VEGETABLE_TOKENS:
        return build_suggestion(
            item_id,
            ["vegetable", "pickled_vegetable", "fermented_condiment"],
            reason="pickled vegetable pattern",
            target="vegetables_mushrooms_fruits",
        )

    if tokens & PREPARED_MEAT_TOKENS or (
        tokens & {"smoked", "cured", "salted"} and tokens & (RED_MEAT_TOKENS | POULTRY_TOKENS | {"meat"})
    ):
        groups = ["meat_product", "prepared_meat"]
        if tokens & SAUSAGE_TOKENS:
            groups.insert(0, "sausage_product")
        return build_suggestion(
            item_id,
            groups,
            reason="prepared meat keyword pattern",
            target="meat_poultry",
        )

    if tokens & MEAT_ON_BONE_TOKENS:
        if tokens & POULTRY_TOKENS:
            groups = ["poultry", "meat_piece", "meat_on_bone"]
        else:
            groups = ["red_meat", "meat_piece", "meat_on_bone"]

        if tokens & {"bone", "bones", "ribs", "rib", "shank", "shanks", "hock", "drumstick", "drumsticks"}:
            groups.append("broth_meat")

        return build_suggestion(
            item_id,
            groups,
            reason="meat-on-bone keyword pattern",
            target="meat_poultry",
        )

    if "bread" in tokens or "dumpling" in tokens or item_id.endswith("_bread"):
        return build_suggestion(
            item_id,
            ["bread_base"],
            reason="bread/dumpling keyword pattern",
            target="grains_bread",
        )

    if item_id in {"millet", "barley"} or item_id.endswith("_grits") or "flour" in tokens:
        return build_suggestion(
            item_id,
            ["grain"],
            reason="grain/flour keyword pattern",
            target="grains_bread",
        )

    if tokens & {"pea", "peas", "bean", "beans", "lentil", "lentils", "chickpea", "chickpeas", "dal"}:
        return build_suggestion(
            item_id,
            ["legume"],
            reason="legume keyword pattern",
            target="legumes",
        )

    if "seed" in tokens or "seeds" in tokens:
        return build_suggestion(
            item_id,
            ["seed"],
            reason="seed keyword pattern",
            target="nuts_seeds_sweeteners",
        )

    if item_id in {"honey", "sugar", "jaggery"}:
        return build_suggestion(
            item_id,
            ["sweetener"],
            reason="sweetener keyword pattern",
            target="nuts_seeds_sweeteners",
        )

    if item_id in {"mustard", "mayonnaise"} or item_id.endswith("_sauce"):
        return build_suggestion(
            item_id,
            ["sauce"],
            reason="sauce keyword pattern",
            target="sauces_condiments",
        )

    if item_id in {"horseradish", "pepper", "chili"}:
        return build_suggestion(
            item_id,
            ["pungent_spice"],
            reason="spice keyword pattern",
            target="spices_herbs",
        )

    if usage and usage.appears_as_accept and not usage.appears_as_item:
        return build_suggestion(
            item_id,
            ["uncategorized"],
            reason="accepts-only usage; likely needs manual review before drafting",
            target="uncategorized",
            confidence="low",
        )

    return build_suggestion(
        item_id,
        ["uncategorized"],
        reason="fallback heuristic",
        target="uncategorized",
        confidence="low",
    )


def make_ingredient_yaml_entry(item_id: str, suggestion: dict[str, Any]) -> dict[str, Any]:
    raw_name = suggestion.get("name", title_from_id(item_id))
    raw_name_uk = suggestion.get("name_uk", "")
    raw_aliases = suggestion.get("aliases", []) or []
    raw_aliases_uk = suggestion.get("aliases_uk", []) or []

    aliases: list[str] = []
    aliases_uk: list[str] = []

    for alias in raw_aliases:
        if not isinstance(alias, str) or not alias.strip():
            continue

        alias = alias.strip()
        if _is_legacy_localized_text(alias):
            aliases_uk.append(alias)
        else:
            aliases.append(alias)

    for alias in raw_aliases_uk:
        if not isinstance(alias, str) or not alias.strip():
            continue
        aliases_uk.append(alias.strip())

    entry = {
        "name": raw_name,
        "groups": suggestion.get("groups", ["uncategorized"]),
        "abstract": False,
        "aliases": dedupe_groups(aliases),
        "inventory": {
            "track": True,
            "default_amount": "none",
            "hide_from_template": False,
        },
    }

    if isinstance(raw_name_uk, str) and raw_name_uk.strip():
        entry["name_uk"] = raw_name_uk.strip()

    deduped_aliases_uk = dedupe_groups(aliases_uk)
    if deduped_aliases_uk:
        entry["aliases_uk"] = deduped_aliases_uk

    if suggestion.get("review", False):
        entry["review"] = True

    return entry


def get_missing(
    recipes_path: str | Path,
    merged_path: str | Path,
    include_accepts: bool = True,
) -> tuple[dict[str, Usage], set[str], set[str]]:
    ingredient_ids, category_ids, _ = load_known_ids(merged_path)
    known_ids = ingredient_ids | category_ids

    usage = collect_recipe_usage(recipes_path, include_accepts=include_accepts)

    missing = {
        item_id: item_usage
        for item_id, item_usage in usage.items()
        if item_id not in known_ids
    }

    return missing, ingredient_ids, category_ids


def print_report(missing: dict[str, Usage]) -> None:
    if not missing:
        print("Новых ингредиентов не найдено. Всё уже есть в каталоге.")
        return

    grouped: dict[str, list[tuple[str, Usage, dict[str, Any]]]] = defaultdict(list)

    for item_id, usage in sorted(missing.items()):
        suggestion = infer_by_pattern(item_id, usage=usage)
        target = suggestion.get("target", "uncategorized")
        grouped[target].append((item_id, usage, suggestion))

    print()
    print(f"Новых item_id: {len(missing)}")
    print()

    for target in sorted(grouped):
        file_name = TARGET_FILES.get(target, "ingredients_uncategorized.yaml")
        print("=" * 80)
        print(f"{target} -> {file_name}")
        print("=" * 80)

        for item_id, usage, suggestion in grouped[target]:
            roles_text = format_counter(usage.roles, preferred_order=ROLE_ORDER)
            amounts_text = format_counter(usage.amounts, preferred_order=AMOUNT_ORDER)
            accepted_by_text = format_counter(usage.accepted_by, limit=4)
            recipes_preview = ", ".join(sorted(usage.recipes)[:4])
            if len(usage.recipes) > 4:
                recipes_preview += f", ... +{len(usage.recipes)-4}"

            print(f"- {item_id}")
            print(f"  name: {suggestion.get('name')}")
            print(f"  groups: {suggestion.get('groups')}")
            print(f"  suggestion_target: {target}")
            print(f"  confidence: {suggestion.get('confidence', 'heuristic')}")
            print(f"  suggestion_reason: {suggestion.get('reason', '-')}")
            print(f"  priority: {usage.priority}")
            print(f"  appearance: {usage.appearance} (item={usage.item_hits}, accepts={usage.accept_hits})")
            print(f"  roles: {roles_text}")
            print(f"  amounts: {amounts_text}")
            if usage.accepted_by:
                print(f"  accepted_by: {accepted_by_text}")
            if usage.examples:
                print(f"  examples: {format_examples(usage.examples)}")
            print(f"  recipes: {recipes_preview}")
            print()


def write_drafts(
    missing: dict[str, Usage],
    draft_dir: str | Path = DEFAULT_DRAFT_DIR,
) -> list[Path]:
    draft_dir = Path(draft_dir)
    if not missing:
        print("Драфты не созданы: новых ингредиентов нет.")
        return []

    grouped: dict[str, dict[str, Any]] = defaultdict(dict)

    for item_id, usage in sorted(missing.items()):
        suggestion = infer_by_pattern(item_id, usage=usage)
        target = suggestion.get("target", "uncategorized")
        entry = make_ingredient_yaml_entry(item_id, suggestion)

        comment_parts = [
            "auto-draft",
            f"priority={usage.priority}",
            f"appearance={usage.appearance}",
            f"roles={dict(usage.roles)}",
            f"amounts={dict(usage.amounts)}",
            f"target={target}",
            f"reason={suggestion.get('reason', 'heuristic')}",
        ]
        if usage.accepted_by:
            comment_parts.append(f"accepted_by={dict(usage.accepted_by.most_common(4))}")
        comment_parts.append(f"recipes={', '.join(sorted(usage.recipes)[:6])}")

        entry["comment"] = "; ".join(comment_parts)

        grouped[target][item_id] = entry

    draft_dir.mkdir(parents=True, exist_ok=True)
    for old_draft in draft_dir.glob("_draft_*.yaml"):
        old_draft.unlink()

    created: list[Path] = []
    for target, ingredients in sorted(grouped.items()):
        target_file = TARGET_FILES.get(target, "ingredients_uncategorized.yaml")
        path = draft_dir / f"_draft_{target_file}"

        data = {
            "metadata": {
                "version": "draft",
                "kind": "ingredients",
                "domain": target,
                "note": (
                    "Автоматический драфт. Проверьте name/groups/aliases, "
                    "потом перенесите entries в рабочий YAML-файл."
                ),
                "target_file": target_file,
            },
            "ingredients": ingredients,
        }

        save_yaml(path, data)

        created.append(path)

    print()
    print("Созданы draft-файлы:")
    for path in created:
        print(f"- {path}")

    return created


def normalize_final_entry(entry: dict[str, Any]) -> dict[str, Any]:
    cleaned = dict(entry)
    cleaned.pop("comment", None)
    cleaned.pop("review", None)
    return cleaned


def build_target_yaml(domain: str) -> dict[str, Any]:
    return {
        "metadata": {
            "version": "0.1",
            "kind": "ingredients",
            "domain": domain,
        },
        "ingredients": {},
    }


def rebuild_merged_ingredients(
    ingredients_dir: str | Path = DEFAULT_INGREDIENTS_DIR,
    merged_path: str | Path = DEFAULT_MERGED_PATH,
) -> tuple[Path, int, int]:
    ingredients_dir = Path(ingredients_dir)
    merged_path = Path(merged_path)

    categories_path = ingredients_dir / "ingredient_categories.yaml"
    categories = load_yaml(categories_path).get("categories", {}) or {}

    ingredients: dict[str, Any] = {}
    for path in sorted(ingredients_dir.glob("ingredients_*.yaml")):
        if path.name == merged_path.name:
            continue

        data = load_yaml(path)
        validate_ingredient_entries(data.get("ingredients", {}) or {}, path)
        for item_id, item in (data.get("ingredients", {}) or {}).items():
            if item_id in ingredients:
                raise ValueError(f"Duplicate ingredient id during merged rebuild: {item_id} in {path.name}")
            ingredients[item_id] = item

    merged_data = {
        "metadata": {
            "version": "0.1",
            "kind": "merged_ingredients",
        },
        "categories": categories,
        "ingredients": dict(sorted(ingredients.items())),
    }
    save_yaml(merged_path, merged_data)
    return merged_path, len(categories), len(ingredients)


def merge_drafts_into_ingredients(
    draft_dir: str | Path = DEFAULT_DRAFT_DIR,
    ingredients_dir: str | Path = DEFAULT_INGREDIENTS_DIR,
    merged_path: str | Path = DEFAULT_MERGED_PATH,
    delete_drafts: bool = True,
) -> dict[str, Any]:
    draft_dir = Path(draft_dir)
    ingredients_dir = Path(ingredients_dir)
    merged_path = Path(merged_path)

    if not draft_dir.exists():
        print(f"Draft-папка не найдена: {draft_dir}")
        return {
            "draft_files": [],
            "updated_targets": {},
            "merged_path": merged_path,
            "categories_count": 0,
            "ingredients_count": 0,
            "deleted_drafts": [],
        }

    draft_paths = sorted(draft_dir.glob("_draft_*.yaml"))
    if not draft_paths:
        print(f"В папке {draft_dir} нет draft-файлов для merge.")
        return {
            "draft_files": [],
            "updated_targets": {},
            "merged_path": merged_path,
            "categories_count": 0,
            "ingredients_count": 0,
            "deleted_drafts": [],
        }

    updated_targets: dict[Path, list[str]] = {}

    for draft_path in draft_paths:
        draft_data = load_yaml(draft_path)
        metadata = draft_data.get("metadata", {}) or {}
        draft_ingredients = draft_data.get("ingredients", {}) or {}

        target_file = metadata.get("target_file")
        if not target_file:
            raise ValueError(f"В draft-файле {draft_path} нет metadata.target_file.")

        domain = metadata.get("domain", "uncategorized")
        target_path = ingredients_dir / target_file

        target_data = load_yaml(target_path) if target_path.exists() else build_target_yaml(domain)
        target_metadata = target_data.setdefault("metadata", {})
        target_metadata.setdefault("version", "0.1")
        target_metadata.setdefault("kind", "ingredients")
        target_metadata.setdefault("domain", domain)

        target_ingredients = dict(target_data.get("ingredients", {}) or {})
        validate_ingredient_entries(target_ingredients, target_path)
        added_item_ids: list[str] = []

        for item_id, draft_entry in sorted(draft_ingredients.items()):
            if not isinstance(draft_entry, dict):
                raise ValueError(f"Ингредиент {item_id} в {draft_path} должен быть dict.")

            cleaned_entry = normalize_final_entry(draft_entry)

            if item_id in target_ingredients:
                existing_cleaned = normalize_final_entry(target_ingredients[item_id])
                if existing_cleaned == cleaned_entry:
                    continue

                raise ValueError(
                    f"Конфликт merge для {item_id}: уже есть в {target_path}, "
                    f"но отличается от содержимого {draft_path}."
                )

            target_ingredients[item_id] = cleaned_entry
            added_item_ids.append(item_id)

        if added_item_ids:
            target_data["ingredients"] = dict(sorted(target_ingredients.items()))
            save_yaml(target_path, target_data)
            updated_targets[target_path] = added_item_ids

    merged_path, categories_count, ingredients_count = rebuild_merged_ingredients(
        ingredients_dir=ingredients_dir,
        merged_path=merged_path,
    )

    deleted_drafts: list[Path] = []
    if delete_drafts:
        for draft_path in draft_paths:
            draft_path.unlink()
            deleted_drafts.append(draft_path)

        try:
            draft_dir.rmdir()
        except OSError:
            pass

    print()
    print("Draft merge завершён.")
    for target_path, item_ids in sorted(updated_targets.items(), key=lambda pair: str(pair[0])):
        print(f"- {target_path.name}: добавлено {len(item_ids)}")
    print(f"- merged rebuilt: {merged_path}")
    print(f"- categories: {categories_count}")
    print(f"- ingredients: {ingredients_count}")

    if delete_drafts:
        print(f"- deleted drafts: {len(deleted_drafts)}")

    return {
        "draft_files": draft_paths,
        "updated_targets": updated_targets,
        "merged_path": merged_path,
        "categories_count": categories_count,
        "ingredients_count": ingredients_count,
        "deleted_drafts": deleted_drafts,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Найти item_id из рецептов, которых ещё нет в YAML-каталоге ингредиентов."
    )

    parser.add_argument(
        "--ingredients-dir",
        default=str(DEFAULT_INGREDIENTS_DIR),
        help="Directory with source ingredient YAML files.",
    )
    parser.add_argument(
        "--recipes",
        default=str(DEFAULT_RECIPES_PATH),
        help="Файл рецептов YAML.",
    )
    parser.add_argument(
        "--merged-ingredients",
        default=str(DEFAULT_MERGED_PATH),
        help="Слитый ingredients_all_merged.yaml.",
    )
    parser.add_argument(
        "--no-accepts",
        action="store_true",
        help="Не учитывать item_id из accepts.",
    )
    parser.add_argument(
        "--write-drafts",
        action="store_true",
        help="Создать _draft_*.yaml с предложениями по новым ингредиентам.",
    )
    parser.add_argument(
        "--draft-dir",
        default=str(DEFAULT_DRAFT_DIR),
        help="Папка для draft YAML.",
    )
    parser.add_argument(
        "--audit-localization",
        action="store_true",
        help="Audit source ingredient YAML files for missing name_uk and legacy localized fields.",
    )

    return parser


def main() -> None:
    configure_console_output()
    parser = build_parser()
    args = parser.parse_args()

    if args.audit_localization:
        report = audit_localized_sources(ingredients_dir=Path(args.ingredients_dir))
        print_localization_audit_report(report)
        return

    missing, _, _ = get_missing(
        recipes_path=Path(args.recipes),
        merged_path=Path(args.merged_ingredients),
        include_accepts=not args.no_accepts,
    )

    print_report(missing)

    if args.write_drafts:
        write_drafts(missing, draft_dir=Path(args.draft_dir))


if __name__ == "__main__":
    main()
