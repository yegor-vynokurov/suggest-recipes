from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from .i18n import DEFAULT_LANG, normalize_language


@dataclass(frozen=True)
class IngredientCatalog:
    """
    Runtime-каталог ингредиентов.

    Он загружается из YAML и даёт программе те же структуры,
    которые раньше вручную жили в constants.py:
    CATEGORIES, INGREDIENTS, ITEM_NAMES, INGREDIENT_GROUPS и т.д.
    """

    categories: dict[str, dict[str, Any]]
    ingredients: dict[str, dict[str, Any]]

    @classmethod
    def from_yaml(cls, path: str | Path) -> "IngredientCatalog":
        path = Path(path)

        if not path.exists():
            raise FileNotFoundError(
                f"Файл ингредиентов не найден: {path}. "
                f"Ожидался merged YAML, например data/inventory/ingredients/ingredients_all_merged.yaml"
            )

        with path.open("r", encoding="utf-8") as file:
            data = yaml.safe_load(file) or {}

        categories = data.get("categories", {}) or {}
        ingredients = data.get("ingredients", {}) or {}

        catalog = cls(
            categories=categories,
            ingredients=ingredients,
        )
        catalog.validate()

        return catalog

    def _localized_text(
        self,
        data: dict[str, Any],
        field: str,
        fallback: str,
        lang: str | None = DEFAULT_LANG,
    ) -> str:
        normalized_lang = normalize_language(lang)
        value = data.get(field)

        if isinstance(value, dict):
            localized = value.get(normalized_lang) or value.get(DEFAULT_LANG)
            if isinstance(localized, str) and localized.strip():
                return localized.strip()

        localized_key = f"{field}_{normalized_lang}"
        localized_value = data.get(localized_key)
        if isinstance(localized_value, str) and localized_value.strip():
            return localized_value.strip()

        default_key = f"{field}_{DEFAULT_LANG}"
        default_value = data.get(default_key)
        if isinstance(default_value, str) and default_value.strip():
            return default_value.strip()

        if isinstance(value, str) and value.strip():
            return value.strip()

        return fallback

    def category_name(self, category_id: str, lang: str | None = DEFAULT_LANG) -> str:
        category = self.categories.get(category_id)
        if category:
            return self._localized_text(category, "name", category_id, lang)
        return category_id

    def item_name(self, item_id: str, lang: str | None = DEFAULT_LANG) -> str:
        item = self.ingredients.get(item_id)
        if item:
            return self._localized_text(item, "name", item_id, lang)

        category = self.categories.get(item_id)
        if category:
            return self._localized_text(category, "name", item_id, lang)

        return item_id

    def item_comment(self, item_id: str, lang: str | None = DEFAULT_LANG) -> str:
        item = self.ingredients.get(item_id)
        if item:
            return self._localized_text(item, "comment", item_id, lang)
        return item_id

    def build_item_names(self) -> dict[str, str]:
        """
        Человекочитаемые имена и для ингредиентов, и для категорий.
        """
        result: dict[str, str] = {}

        for item_id in self.ingredients:
            result[item_id] = self.item_name(item_id)

        for category_id in self.categories:
            result[category_id] = self.category_name(category_id)

        return result

    def collect_parent_categories(
        self,
        category_id: str,
        seen: set[str] | None = None,
    ) -> set[str]:
        """
        Поднимается вверх по графу категорий.

        Например:
        sausage_product -> meat_product -> meat -> protein
        """
        if seen is None:
            seen = set()

        category = self.categories.get(category_id, {})
        parents = category.get("parents", []) or []

        for parent_id in parents:
            if parent_id in seen:
                continue

            seen.add(parent_id)
            self.collect_parent_categories(parent_id, seen)

        return seen

    def _direct_category_ids(self, item_or_category_id: str) -> set[str]:
        """
        Вернуть "точки входа" в граф категорий для category/item id.

        Для category это сама категория.
        Для ingredient это его прямые groups.
        """
        if item_or_category_id in self.categories:
            return {item_or_category_id}

        category_ids: set[str] = set()

        item = self.ingredients.get(item_or_category_id, {})
        for group_id in item.get("groups", []) or []:
            if group_id == "abstract_ingredient":
                continue

            if group_id in self.categories:
                category_ids.add(group_id)

        return category_ids

    def _ancestor_distances(self, category_id: str) -> dict[str, int]:
        """
        Вернуть минимальную глубину подъёма от категории до каждого её предка.
        """
        if category_id not in self.categories:
            return {}

        queue: deque[tuple[str, int]] = deque([(category_id, 0)])
        distances: dict[str, int] = {category_id: 0}

        while queue:
            current_category, depth = queue.popleft()
            parents = self.categories.get(current_category, {}).get("parents", []) or []

            for parent_id in parents:
                next_depth = depth + 1
                previous_depth = distances.get(parent_id)

                if previous_depth is not None and previous_depth <= next_depth:
                    continue

                distances[parent_id] = next_depth
                queue.append((parent_id, next_depth))

        return distances

    def is_descendant(self, item_or_category_id: str, category_id: str) -> bool:
        """
        Проверить, относится ли item/category к category_id через граф категорий.
        """
        return self.distance_to_category(item_or_category_id, category_id) is not None

    def distance_to_category(
        self,
        item_or_category_id: str,
        category_id: str,
    ) -> int | None:
        """
        Вернуть минимальную глубину подъёма до category_id.

        Примеры:
        - milk -> dairy == 0, потому что dairy есть в direct groups
        - fermented_dairy -> dairy == 1
        - milk_like -> protein == 2
        """
        if category_id not in self.categories:
            return None

        best_distance: int | None = None

        for start_category_id in self._direct_category_ids(item_or_category_id):
            distance = self._ancestor_distances(start_category_id).get(category_id)
            if distance is None:
                continue

            if best_distance is None or distance < best_distance:
                best_distance = distance

        return best_distance

    def shared_parents(
        self,
        left_id: str,
        right_id: str,
        include_self: bool = False,
    ) -> set[str]:
        """
        Найти общие родительские категории для двух item/category id.
        """

        def related_categories(item_or_category_id: str) -> set[str]:
            result: set[str] = set()

            for start_category_id in self._direct_category_ids(item_or_category_id):
                for related_category_id, distance in self._ancestor_distances(start_category_id).items():
                    if not include_self and distance == 0:
                        continue

                    result.add(related_category_id)

            return result

        return related_categories(left_id) & related_categories(right_id)

    def build_abstract_ingredients(self) -> set[str]:
        """
        Что не надо просить у пользователя как обычный продукт.

        Сюда попадают:
        - все категории;
        - ingredients с abstract: true;
        - ingredients, скрытые из inventory template.
        """
        result = set(self.categories.keys())

        for item_id, item in self.ingredients.items():
            inventory = item.get("inventory", {}) or {}

            if item.get("abstract") or inventory.get("hide_from_template"):
                result.add(item_id)

        return result

    def build_ingredient_groups(self) -> dict[str, list[str]]:
        """
        Собирает обратный индекс: группа -> ингредиенты.

        Если ингредиент входит в chili_spice,
        а chili_spice входит в hot_spice,
        то ингредиент попадёт и в chili_spice, и в hot_spice.
        """
        groups: dict[str, set[str]] = {
            category_id: set()
            for category_id in self.categories
        }

        for item_id, item in self.ingredients.items():
            direct_groups = item.get("groups", []) or []

            for group_id in direct_groups:
                groups.setdefault(group_id, set())
                groups[group_id].add(item_id)

                for parent_id in self.collect_parent_categories(group_id):
                    groups.setdefault(parent_id, set())
                    groups[parent_id].add(item_id)

        return {
            group_id: sorted(item_ids)
            for group_id, item_ids in groups.items()
        }

    def build_always_available_inventory(self) -> dict[str, str]:
        """
        Например: water -> many.

        Это будет автоматически добавляться в inventory перед подбором рецептов.
        """
        result: dict[str, str] = {}

        for item_id, item in self.ingredients.items():
            inventory = item.get("inventory", {}) or {}

            if inventory.get("always_available"):
                result[item_id] = inventory.get("default_amount", "many")

        return result

    def build_hidden_from_inventory_template(self) -> set[str]:
        """
        Что не должно попадать в CSV/Excel-шаблон кладовки.
        """
        result: set[str] = set()

        for item_id, item in self.ingredients.items():
            inventory = item.get("inventory", {}) or {}

            if item.get("abstract") or inventory.get("hide_from_template"):
                result.add(item_id)

        return result

    def build_filter_aliases_from_categories(self) -> dict[str, tuple[str, str]]:
        """
        Автоматические алиасы для фильтров по ingredient_group.

        Например:
        "бобовые" -> ("ingredient_group", "legume")
        "legume" -> ("ingredient_group", "legume")
        """
        aliases: dict[str, tuple[str, str]] = {}

        for category_id, category in self.categories.items():
            aliases[category_id] = ("ingredient_group", category_id)

            name = category.get("name")
            if name:
                aliases[name.lower()] = ("ingredient_group", category_id)

        return aliases

    def validate(self) -> None:
        errors: list[str] = []

        for category_id, category in self.categories.items():
            if not isinstance(category, dict):
                errors.append(f"Категория {category_id} должна быть dict.")
                continue

            if "name" not in category:
                errors.append(f"У категории {category_id} нет поля name.")

            parents = category.get("parents", [])
            if parents is None:
                parents = []

            if not isinstance(parents, list):
                errors.append(f"У категории {category_id} parents должен быть list.")

            for parent_id in parents:
                if parent_id not in self.categories:
                    errors.append(
                        f"Категория {category_id} ссылается на неизвестного родителя {parent_id}."
                    )

        for item_id, item in self.ingredients.items():
            if not isinstance(item, dict):
                errors.append(f"Ингредиент {item_id} должен быть dict.")
                continue

            if "name" not in item:
                errors.append(f"У ингредиента {item_id} нет поля name.")

            groups = item.get("groups", [])
            if groups is None:
                groups = []

            if not isinstance(groups, list):
                errors.append(f"У ингредиента {item_id} groups должен быть list.")

            for group_id in groups:
                if group_id not in self.categories:
                    errors.append(
                        f"Ингредиент {item_id} ссылается на неизвестную группу {group_id}."
                    )

        if errors:
            message = "\n".join(errors)
            raise ValueError(f"Ошибки в YAML-каталоге ингредиентов:\n{message}")


def load_catalog(path: str | Path) -> IngredientCatalog:
    return IngredientCatalog.from_yaml(path)
