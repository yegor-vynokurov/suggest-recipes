from __future__ import annotations

from pathlib import Path
import re

from src.kitchen.ingredient_catalog import load_catalog
from src.kitchen.i18n import DEFAULT_LANG, normalize_language


# -------------------------
# Paths
# -------------------------

BASE_DIR = Path(__file__).resolve().parents[2]

DATA_PATH = BASE_DIR / "data"
RECIPES_PATH = DATA_PATH / "recipes"
INVENT_PATH = DATA_PATH / "inventory"

INGREDIENTS_DIR = INVENT_PATH / "ingredients"
INGREDIENTS_DATA_PATH = INGREDIENTS_DIR / "ingredients_all_merged.yaml"
CURRENT_INVENTORY_YAML_PATH = INVENT_PATH / "current_inventory.yaml"
CURRENT_INVENTORY_CSV_LEGACY_PATH = INVENT_PATH / "current_inventory.csv"
CURRENT_INVENTORY_CSV_EN_PATH = INVENT_PATH / "current_inventory.en.csv"
CURRENT_INVENTORY_CSV_UK_PATH = INVENT_PATH / "current_inventory.uk.csv"
CURRENT_INVENTORY_CSV_BY_LANG = {
    "en": CURRENT_INVENTORY_CSV_EN_PATH,
    "uk": CURRENT_INVENTORY_CSV_UK_PATH,
}

# Текущий файл рецептов.
# Можно менять здесь, или позже вынести в аргументы CLI.
# ING_PATH = RECIPES_PATH / "recipe_templates_pantry_v0_4.yaml"
# ING_PATH = RECIPES_PATH / "recipe_templates_turkish_v0_1.yaml"
# ING_PATH = RECIPES_PATH / "recipe_templates_indian_v0_1.yaml"
# ING_PATH = RECIPES_PATH / "recipe_templates_ukrainian_v0_1.yaml"
ING_PATH = RECIPES_PATH / "read.yaml"


# -------------------------
# Scoring constants
# -------------------------

DEFAULT_RANDOMIZE = False
DEFAULT_RANDOM_STRENGTH = 0.06

ROLE_WEIGHT = {
    "main": 5.0,
    "required": 3.0,
    "addition": 1.0,
    "spice": 0.3,
    "optional": 0.1,
}

AMOUNT_SCALE = {
    "spice": 0.5,
    "little": 1.0,
    "normal": 2.0,
    "many": 3.0,
}

FILTER_WEIGHTS = {
    "ingredient_group": 0.18,
    "cuisine": 0.12,
    "dish_type": 0.12,
    "time": 0.16,
    "method": 0.08,
}

PREFER_CATEGORY_WEIGHT = 0.18

PREFER_CATEGORY_WEIGHTS = {
    "meat": 0.18,
    "fish": 0.18,
    "legume": 0.16,
    "mushroom": 0.14,
    "grain": 0.10,
    "dairy": 0.10,
    "hot_spice": 0.06,
    "chili_spice": 0.06,
}

PREFER_CATEGORY_ROLE_MULTIPLIER = {
    "main": 1.0,
    "required": 0.75,
    "addition": 0.35,
    "spice": 0.1,
    "optional": 0.1,
}

DEFAULT_LIMITS_BY_STATUS = {
    "can_cook": 7,
    "variant": 5,
    "missing_one": 3,
    "missing_main": 2,
    "far": 1,
}

CATEGORY_MATCH_SIMILARITY = 0.85
ACCEPTED_CATEGORY_MATCH_SIMILARITY = 0.7

# Missing-status tuning.
# Эти коэффициенты влияют не на общий score рецепта,
# а на то, насколько сильно secondary missing
# (addition / spice) давят на status.
MISSING_ADDITION_PENALTY = 0.5
MISSING_SPICE_PENALTY = 0.1
MISSING_REQUIRED_SPICE_PENALTY = 0.6
BROAD_ACCEPT_CATEGORIES = {
    "fat",
    "sauce",
    "dairy",
    "protein",
    "seasoning",
}

STRICT_ACCEPT_PARENT_FALLBACK_CATEGORIES = BROAD_ACCEPT_CATEGORIES | {
    "offal",
    "liver_offal",
    "minced_meat",
    "fruit_preserve",
}

# Future substitution tuning.
# Пока это отдельные ручки для следующих шагов рефакторинга:
# - CATEGORY_DEPTH_PENALTY: штраф за замену через более общий уровень категорий
# - SAME_ITEM_REUSE_PENALTY: штраф за повторное использование одного и того же item
#   для нескольких different recipe needs
CATEGORY_DEPTH_PENALTY = 0.12
SAME_ITEM_REUSE_PENALTY = 0.2

AVOID_INGREDIENT_PENALTY = 0.25
DISLIKE_MAIN_INGREDIENT_PENALTY = 0.35
PREFER_INGREDIENT_BONUS = 0.08


# -------------------------
# Ingredient catalog from YAML
# -------------------------

CATALOG = load_catalog(INGREDIENTS_DATA_PATH)

CATEGORIES = CATALOG.categories
INGREDIENTS = CATALOG.ingredients

CYRILLIC_RE = re.compile(r"[А-Яа-яІіЇїЄєҐґ]")


def humanize_identifier(identifier: str) -> str:
    return identifier.replace("_", " ")


def inventory_csv_path_for_lang(lang: str | None = None) -> Path:
    return CURRENT_INVENTORY_CSV_BY_LANG[normalize_language(lang)]


def inventory_csv_candidates_for_lang(lang: str | None = None) -> list[Path]:
    preferred_path = inventory_csv_path_for_lang(lang)
    candidates = [preferred_path]

    if CURRENT_INVENTORY_CSV_LEGACY_PATH != preferred_path:
        candidates.append(CURRENT_INVENTORY_CSV_LEGACY_PATH)

    return candidates


def _is_english_display_text(text: str) -> bool:
    return bool(text.strip()) and CYRILLIC_RE.search(text) is None


def canonical_display_name(identifier: str) -> str:
    preferred = CATALOG.item_name(identifier, "en")

    if _is_english_display_text(preferred):
        return preferred

    return humanize_identifier(identifier)


def _catalog_display_data(identifier: str) -> dict[str, object]:
    if identifier in INGREDIENTS:
        return INGREDIENTS[identifier]
    if identifier in CATEGORIES:
        return CATEGORIES[identifier]
    return {}


def _localized_display_name(identifier: str, lang: str | None = None) -> str:
    normalized_lang = normalize_language(lang)
    fallback_name = ITEM_NAMES.get(identifier, humanize_identifier(identifier))
    data = _catalog_display_data(identifier)

    if not data:
        return fallback_name

    value = data.get("name")
    if isinstance(value, dict):
        localized = value.get(normalized_lang)
        if isinstance(localized, str) and localized.strip():
            return localized.strip()

        english = value.get(DEFAULT_LANG)
        if (
            normalized_lang == DEFAULT_LANG
            and isinstance(english, str)
            and _is_english_display_text(english)
        ):
            return english.strip()

    localized_key = f"name_{normalized_lang}"
    localized_value = data.get(localized_key)
    if isinstance(localized_value, str) and localized_value.strip():
        return localized_value.strip()

    if normalized_lang == DEFAULT_LANG:
        default_key = f"name_{DEFAULT_LANG}"
        default_value = data.get(default_key)
        if (
            isinstance(default_value, str)
            and default_value.strip()
            and _is_english_display_text(default_value)
        ):
            return default_value.strip()

    return fallback_name


ITEM_NAMES = {
    item_id: canonical_display_name(item_id)
    for item_id in INGREDIENTS
}
ITEM_NAMES.update({
    category_id: canonical_display_name(category_id)
    for category_id in CATEGORIES
})
ABSTRACT_INGREDIENTS = CATALOG.build_abstract_ingredients()
INGREDIENT_GROUPS = CATALOG.build_ingredient_groups()

ALWAYS_AVAILABLE_INVENTORY = CATALOG.build_always_available_inventory()
HIDDEN_FROM_INVENTORY_TEMPLATE = CATALOG.build_hidden_from_inventory_template()


def item_name(item_id: str, lang: str | None = None) -> str:
    if lang is None:
        return ITEM_NAMES.get(item_id, humanize_identifier(item_id))
    return _localized_display_name(item_id, lang)


def category_name(category_id: str, lang: str | None = None) -> str:
    if lang is None:
        return ITEM_NAMES.get(category_id, humanize_identifier(category_id))
    return _localized_display_name(category_id, lang)


def item_comment(item_id: str, lang: str | None = None) -> str:
    return CATALOG.item_comment(item_id, lang)


def collect_parent_categories(
    category_id: str,
    seen: set[str] | None = None,
) -> set[str]:
    return CATALOG.collect_parent_categories(category_id, seen)


def is_descendant(item_or_category_id: str, category_id: str) -> bool:
    return CATALOG.is_descendant(item_or_category_id, category_id)


def distance_to_category(
    item_or_category_id: str,
    category_id: str,
) -> int | None:
    return CATALOG.distance_to_category(item_or_category_id, category_id)


def shared_parents(
    left_id: str,
    right_id: str,
    include_self: bool = False,
) -> set[str]:
    return CATALOG.shared_parents(left_id, right_id, include_self=include_self)


# -------------------------
# Recipe facets
# -------------------------

RECIPE_FACET_LABELS = {
    "cuisine": {
        "mediterranean": {
            "en": "Mediterranean cuisine",
            "uk": "Середземноморська кухня",
        },
        "european": {
            "en": "European cuisine",
            "uk": "Європейська кухня",
        },
        "slavic": {
            "en": "Slavic cuisine",
            "uk": "Слов'янська кухня",
        },
        "caucasian": {
            "en": "Caucasian cuisine",
            "uk": "Кавказька кухня",
        },
        "asian": {
            "en": "Asian cuisine",
            "uk": "Азійська кухня",
        },
        "mexican": {
            "en": "Mexican cuisine",
            "uk": "Мексиканська кухня",
        },
        "fusion": {
            "en": "Fusion",
            "uk": "Ф'южн",
        },
        "turkish": {
            "en": "Turkish cuisine",
            "uk": "Турецька кухня",
        },
        "indian": {
            "en": "Indian cuisine",
            "uk": "Індійська кухня",
        },
        "ukrainian": {
            "en": "Ukrainian cuisine",
            "uk": "Українська кухня",
        },
        "georgian": {
            "en": "Georgian cuisine",
            "uk": "Грузинська кухня",
        },
        "italian": {
            "en": "Italian cuisine",
            "uk": "Італійська кухня",
        },
        "greek": {
            "en": "Greek cuisine",
            "uk": "Грецька кухня",
        },
        "french": {
            "en": "French cuisine",
            "uk": "Французька кухня",
        },
        "spanish": {
            "en": "Spanish cuisine",
            "uk": "Іспанська кухня",
        },
        "english": {
            "en": "English cuisine",
            "uk": "Англійська кухня",
        },
        "czech": {
            "en": "Czech cuisine",
            "uk": "Чеська кухня",
        },
        "hungarian": {
            "en": "Hungarian cuisine",
            "uk": "Угорська кухня",
        },
        "chinese": {
            "en": "Chinese cuisine",
            "uk": "Китайська кухня",
        },
        "scandinavian": {
            "en": "Scandinavian cuisine",
            "uk": "Скандинавська кухня",
        },
    },
    "dish_type": {
        "soup": {
            "en": "Soup",
            "uk": "Суп",
        },
        "main": {
            "en": "Main course",
            "uk": "Основна страва",
        },
        "salad": {
            "en": "Salad",
            "uk": "Салат",
        },
        "dessert": {
            "en": "Dessert",
            "uk": "Десерт",
        },
        "breakfast": {
            "en": "Breakfast",
            "uk": "Сніданок",
        },
        "snack": {
            "en": "Snack",
            "uk": "Перекус",
        },
        "sauce": {
            "en": "Sauce",
            "uk": "Соус",
        },
        "component": {
            "en": "Component",
            "uk": "Компонент",
        },
        "bread": {
            "en": "Bread / baking",
            "uk": "Хліб / випічка",
        },
        "drink": {
            "en": "Drink",
            "uk": "Напій",
        },
        "side": {
            "en": "Side dish",
            "uk": "Гарнір",
        },
    },
    "time": {
        "under_10": {
            "en": "under 10 minutes",
            "uk": "до 10 хвилин",
        },
        "under_30": {
            "en": "under 30 minutes",
            "uk": "до 30 хвилин",
        },
        "under_60": {
            "en": "under 1 hour",
            "uk": "до 1 години",
        },
        "over_60": {
            "en": "over 1 hour",
            "uk": "понад 1 годину",
        },
    },
    "method": {
        "boil": {
            "en": "Boil",
            "uk": "Варити",
        },
        "fry": {
            "en": "Fry",
            "uk": "Смажити",
        },
        "bake": {
            "en": "Bake",
            "uk": "Запікати",
        },
        "stew": {
            "en": "Stew",
            "uk": "Тушкувати",
        },
        "raw": {
            "en": "No heat treatment",
            "uk": "Без термічної обробки",
        },
        "mix": {
            "en": "Mix",
            "uk": "Змішувати",
        },
        "blend": {
            "en": "Blend",
            "uk": "Збивати / блендерити",
        },
        "grill": {
            "en": "Grill / open fire",
            "uk": "Гриль / відкрите вогнище",
        },
        "roast": {
            "en": "Roast / brown",
            "uk": "Обсмажувати / підрум'янювати",
        },
        "steam": {
            "en": "Steam",
            "uk": "Готувати на парі",
        },
        "ferment": {
            "en": "Ferment",
            "uk": "Ферментувати",
        },
        "temper": {
            "en": "Temper / tadka",
            "uk": "Темперувати / тадка",
        },
        "assemble": {
            "en": "Assemble",
            "uk": "Збирати",
        },
        "freeze": {
            "en": "Freeze",
            "uk": "Заморожувати",
        },
        "set": {
            "en": "Set / chill",
            "uk": "Охолоджувати / стабілізувати",
        },
        "soak": {
            "en": "Soak",
            "uk": "Замочувати",
        },
        "roll": {
            "en": "Roll",
            "uk": "Скручувати",
        },
        "knead": {
            "en": "Knead",
            "uk": "Місити",
        },
    },
}


def facet_labels(facet_name: str, lang: str | None = DEFAULT_LANG) -> dict[str, str]:
    normalized_lang = normalize_language(lang)
    facet_values = RECIPE_FACET_LABELS.get(facet_name, {})
    labels: dict[str, str] = {}

    for value_id, translations in facet_values.items():
        label = (
            translations.get(normalized_lang)
            or translations.get(DEFAULT_LANG)
            or humanize_identifier(value_id)
        )
        labels[value_id] = label

    return labels


def facet_label(
    facet_name: str,
    value_id: str,
    lang: str | None = DEFAULT_LANG,
) -> str:
    return facet_labels(facet_name, lang).get(value_id, humanize_identifier(value_id))


RECIPE_FACETS = {
    facet_name: facet_labels(facet_name)
    for facet_name in RECIPE_FACET_LABELS
}

TIME_BUCKET_MINUTES = {
    "under_10": 10,
    "under_30": 30,
    "under_60": 60,
}

TIME_BUCKET_LABELS = facet_labels("time")


FILTER_TYPE_LABELS = {
    "ingredient_group": {
        "en": "ingredient group",
        "uk": "група інгредієнтів",
    },
    "tag": {
        "en": "tag",
        "uk": "тег",
    },
    "cuisine": {
        "en": "cuisine",
        "uk": "кухня",
    },
    "dish_type": {
        "en": "dish type",
        "uk": "тип страви",
    },
    "time": {
        "en": "time",
        "uk": "час",
    },
    "method": {
        "en": "method",
        "uk": "спосіб",
    },
}


def filter_type_label(filter_type: str, lang: str | None = DEFAULT_LANG) -> str:
    normalized_lang = normalize_language(lang)
    translations = FILTER_TYPE_LABELS.get(filter_type)
    if not translations:
        return humanize_identifier(filter_type)
    return (
        translations.get(normalized_lang)
        or translations.get(DEFAULT_LANG)
        or humanize_identifier(filter_type)
    )


def filter_value_label(
    filter_type: str,
    value_id: str,
    lang: str | None = DEFAULT_LANG,
) -> str:
    if filter_type in RECIPE_FACET_LABELS:
        return facet_label(filter_type, value_id, lang)

    if filter_type == "ingredient_group":
        return category_name(value_id, lang)

    return humanize_identifier(value_id)


# -------------------------
# Filter aliases
# -------------------------

BASE_FILTER_ALIASES = {
    # ingredient groups
    "бобовые": ("ingredient_group", "legume"),
    "legume": ("ingredient_group", "legume"),
    "legumes": ("ingredient_group", "legume"),

    "мясо": ("ingredient_group", "meat"),
    "meat": ("ingredient_group", "meat"),

    "рыба": ("ingredient_group", "fish"),
    "fish": ("ingredient_group", "fish"),

    "грибы": ("ingredient_group", "mushroom"),
    "mushroom": ("ingredient_group", "mushroom"),

    "крупы": ("ingredient_group", "grain"),
    "grain": ("ingredient_group", "grain"),

    "молочное": ("ingredient_group", "dairy"),
    "молочные": ("ingredient_group", "dairy"),
    "dairy": ("ingredient_group", "dairy"),

    "острое": ("ingredient_group", "hot_spice"),
    "острые_специи": ("ingredient_group", "hot_spice"),
    "hot_spice": ("ingredient_group", "hot_spice"),
    "чили": ("ingredient_group", "chili_spice"),
    "chili": ("ingredient_group", "chili_spice"),

    # cuisine
    "средиземноморская": ("cuisine", "mediterranean"),
    "mediterranean": ("cuisine", "mediterranean"),

    "турецкая": ("cuisine", "turkish"),
    "turkish": ("cuisine", "turkish"),

    "индийская": ("cuisine", "indian"),
    "indian": ("cuisine", "indian"),

    "европейская": ("cuisine", "european"),
    "european": ("cuisine", "european"),

    "мексиканская": ("cuisine", "mexican"),
    "mexican": ("cuisine", "mexican"),

    # dish type
    "soup": ("dish_type", "soup"),
    "main": ("dish_type", "main"),
    "main_course": ("dish_type", "main"),
    "salad": ("dish_type", "salad"),
    "dessert": ("dish_type", "dessert"),
    "breakfast": ("dish_type", "breakfast"),
    "snack": ("dish_type", "snack"),
    "bread": ("dish_type", "bread"),
    "baking": ("dish_type", "bread"),
    "drink": ("dish_type", "drink"),
    "side": ("dish_type", "side"),
    "side_dish": ("dish_type", "side"),
    "component": ("dish_type", "component"),
    "sauce_dish": ("dish_type", "sauce"),

    "первое": ("dish_type", "soup"),
    "суп": ("dish_type", "soup"),
    "перша_страва": ("dish_type", "soup"),

    "второе": ("dish_type", "main"),
    "основное": ("dish_type", "main"),
    "друга_страва": ("dish_type", "main"),
    "основна_страва": ("dish_type", "main"),

    "салат": ("dish_type", "salad"),
    "десерт": ("dish_type", "dessert"),
    "сніданок": ("dish_type", "breakfast"),
    "завтрак": ("dish_type", "breakfast"),
    "перекус": ("dish_type", "snack"),
    "випічка": ("dish_type", "bread"),
    "выпечка": ("dish_type", "bread"),
    "хліб": ("dish_type", "bread"),
    "хлеб": ("dish_type", "bread"),

    # time
    "до10": ("time", "under_10"),
    "до_10": ("time", "under_10"),
    "under_10": ("time", "under_10"),

    "до30": ("time", "under_30"),
    "до_30": ("time", "under_30"),
    "до_получаса": ("time", "under_30"),
    "under_30": ("time", "under_30"),

    "до60": ("time", "under_60"),
    "до_60": ("time", "under_60"),
    "до_часа": ("time", "under_60"),
    "under_60": ("time", "under_60"),

    "больше_часа": ("time", "over_60"),
    "over_60": ("time", "over_60"),
}

FILTER_ALIASES = {
    **CATALOG.build_filter_aliases_from_categories(),
    **BASE_FILTER_ALIASES,
}


# -------------------------
# Validation
# -------------------------

def validate_constants() -> None:
    """
    Проверяет уже загруженный YAML-каталог и производные структуры.
    """
    CATALOG.validate()

    errors = []

    for category_id in CATEGORIES:
        if category_id not in INGREDIENT_GROUPS:
            errors.append(f"Категория {category_id} не попала в INGREDIENT_GROUPS.")

    for item_id, item in INGREDIENTS.items():
        for group_id in item.get("groups", []) or []:
            if group_id not in CATEGORIES:
                errors.append(
                    f"Ингредиент {item_id} ссылается на неизвестную группу {group_id}."
                )

    if errors:
        raise ValueError("Ошибки в constants.py / YAML-каталоге:\n" + "\n".join(errors))
