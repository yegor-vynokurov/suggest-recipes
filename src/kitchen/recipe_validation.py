from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable


ALLOWED_RECIPE_ROLES = {
    "main",
    "required",
    "addition",
    "spice",
    "optional",
}

ALLOWED_RECIPE_AMOUNTS = {
    "spice",
    "little",
    "normal",
    "many",
}

# Слишком широкие категории, которые по умолчанию запрещены в accepts.
# Они должны проходить только через явный whitelist.
BROAD_ACCEPT_CATEGORIES = {
    "fat",
    "sauce",
    "dairy",
    "protein",
    "seasoning",
}

# Явные whitelist-исключения для broad categories на уровне item.
# Формат:
# item_id -> {allowed_broad_accept_category_ids}
ALLOWED_BROAD_ACCEPT_CATEGORIES_BY_ITEM: dict[str, set[str]] = {
    "bechamel": {"sauce"},
    "brown_gravy": {"sauce"},
    "butter": {"fat"},
    "capers": {"seasoning"},
    "chutney": {"sauce"},
    "coconut_oil": {"fat"},
    "duck_fat": {"fat"},
    "fish_sauce_base": {"sauce"},
    "ghee": {"fat"},
    "goose_fat": {"fat"},
    "gravy": {"sauce"},
    "ketchup": {"sauce"},
    "mayonnaise": {"sauce"},
    "mustard": {"sauce"},
    "olive_oil": {"fat"},
    "plant_oil": {"fat"},
    "rapeseed_oil": {"fat"},
    "remoulade": {"sauce"},
    "salo": {"fat"},
    "smalec": {"fat"},
    "tartar_sauce": {"sauce"},
    "white_sauce": {"sauce"},
}

# Дополнительные whitelist-исключения для отдельных recipe/item.
# Формат:
# (recipe_id, item_id) -> {allowed_broad_accept_category_ids}
ALLOWED_BROAD_ACCEPT_RULES: dict[tuple[str, str], set[str]] = {}

# Адресные blacklist-правила для уже известных проблемных мест.
# Формат:
# (recipe_id, item_id) -> {blocked_accept_category_ids}
BLOCKED_ACCEPT_RULES: dict[tuple[str, str], set[str]] = {
    ("french_mayonnaise_maison", "plant_oil"): {"fat"},
    ("french_mayonnaise_maison", "mustard"): {"sauce"},
}


def allowed_broad_accept_categories(recipe_id: str, item_id: str) -> set[str]:
    allowed = set(ALLOWED_BROAD_ACCEPT_CATEGORIES_BY_ITEM.get(item_id, set()))
    allowed.update(ALLOWED_BROAD_ACCEPT_RULES.get((recipe_id, item_id), set()))
    return allowed


def find_recipe_validation_issues(
    data: dict[str, Any],
    blocked_categories: Iterable[str] = BROAD_ACCEPT_CATEGORIES,
    allowed_roles: Iterable[str] = ALLOWED_RECIPE_ROLES,
    allowed_amounts: Iterable[str] = ALLOWED_RECIPE_AMOUNTS,
) -> list[str]:
    blocked = set(blocked_categories)
    roles = set(allowed_roles)
    amounts = set(allowed_amounts)
    issues: list[str] = []

    for recipe in data.get("recipes", []) or []:
        recipe_id = recipe.get("id", "<missing id>")
        missing_allowed = recipe.get("missing_allowed", 0)

        if not isinstance(missing_allowed, int):
            issues.append(
                f"{recipe_id}: missing_allowed должен быть int, получено {type(missing_allowed).__name__}."
            )
        elif missing_allowed < 0:
            issues.append(
                f"{recipe_id}: missing_allowed должен быть >= 0, получено {missing_allowed}."
            )

        ingredients = recipe.get("ingredients", []) or []
        if not isinstance(ingredients, list):
            issues.append(f"{recipe_id}: ingredients должен быть list.")
            continue

        for ingredient in ingredients:
            if not isinstance(ingredient, dict):
                issues.append(f"{recipe_id}: ingredient entry должен быть dict.")
                continue

            item_id = ingredient.get("item", "<missing item>")
            role = ingredient.get("role")
            amount = ingredient.get("amount", "normal")
            accepts = ingredient.get("accepts", []) or []

            if role not in roles:
                allowed = ", ".join(sorted(roles))
                issues.append(
                    f"{recipe_id}: item {item_id} использует неизвестную role={role}. "
                    f"Допустимо: {allowed}."
                )

            if amount not in amounts:
                allowed = ", ".join(sorted(amounts))
                issues.append(
                    f"{recipe_id}: item {item_id} использует неизвестный amount={amount}. "
                    f"Допустимо: {allowed}."
                )

            if not isinstance(accepts, list):
                issues.append(f"{recipe_id}: item {item_id} поле accepts должно быть list.")
                continue

            blocked_for_item = BLOCKED_ACCEPT_RULES.get((recipe_id, item_id), set())
            allowed_broad_for_item = allowed_broad_accept_categories(
                recipe_id=recipe_id,
                item_id=item_id,
            )

            for accepted_id in accepts:
                if accepted_id in blocked_for_item:
                    issues.append(
                        f"{recipe_id}: item {item_id} не должен использовать слишком широкую категорию "
                        f"{accepted_id} в accepts для этого рецепта."
                    )
                    continue

                if accepted_id in blocked and accepted_id not in allowed_broad_for_item:
                    issues.append(
                        f"{recipe_id}: item {item_id} использует слишком широкую категорию {accepted_id} "
                        f"в accepts без явного whitelist-разрешения."
                    )

    return issues


def find_disallowed_accept_category_issues(
    data: dict[str, Any],
    blocked_categories: Iterable[str] = BROAD_ACCEPT_CATEGORIES,
) -> list[str]:
    return find_recipe_validation_issues(
        data=data,
        blocked_categories=blocked_categories,
    )


def validate_recipe_schema(
    data: dict[str, Any],
    path: str | Path,
    blocked_categories: Iterable[str] = BROAD_ACCEPT_CATEGORIES,
    allowed_roles: Iterable[str] = ALLOWED_RECIPE_ROLES,
    allowed_amounts: Iterable[str] = ALLOWED_RECIPE_AMOUNTS,
) -> None:
    issues = find_recipe_validation_issues(
        data=data,
        blocked_categories=blocked_categories,
        allowed_roles=allowed_roles,
        allowed_amounts=allowed_amounts,
    )

    if not issues:
        return

    path = Path(path)
    message = "\n".join(issues)
    raise ValueError(
        f"В файле рецептов {path} найдены ошибки схемы рецептов:\n{message}"
    )


def validate_accept_categories(
    data: dict[str, Any],
    path: str | Path,
    blocked_categories: Iterable[str] = BROAD_ACCEPT_CATEGORIES,
) -> None:
    validate_recipe_schema(
        data=data,
        path=path,
        blocked_categories=blocked_categories,
    )
