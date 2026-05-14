from typing import Any
import random

import src.kitchen.constants as cnst
from src.kitchen.construct import Recipe, Need
from src.kitchen.i18n import DEFAULT_LANG, normalize_language, t


class RecipeEngine:
    """
    Движок подбора блюд.

    Он хранит:
    - список рецептов;
    - текущий список продуктов пользователя;
    - логику сравнения рецептов с продуктами.

    Важно:
    этот класс ничего не знает про Telegram.
    Он возвращает структурированные dict-результаты.
    """

    def __init__(
        self,
        recipes: list[Recipe],
        inventory: dict[str, str] | None = None,
        limit_per_group: int = 10,
        limits_by_status: dict[str, int] | None = None,
        lang: str = DEFAULT_LANG,
    ) -> None:
        self.recipes = recipes
        self.inventory = dict(inventory) if inventory else {}
        self.limit_per_group = limit_per_group
        self.lang = normalize_language(lang)
        self.limits_by_status = self.build_limits_by_status(
        limits_by_status=limits_by_status,
        fallback_limit=limit_per_group,
    )

    def set_inventory(self, inventory: dict[str, str]) -> None:
        """
        Полностью заменить текущую кладовку пользователя.
        """
        self.inventory = dict(inventory)

    def get_inventory(self) -> dict[str, str]:
        """
        Вернуть копию текущей кладовки.
        """
        return dict(self.inventory)

    def clear_inventory(self) -> None:
        """
        Очистить текущую кладовку.
        """
        self.inventory.clear()

    def add_item(self, item_id: str, amount: str = "normal") -> None:
        """
        Добавить один ингредиент или обновить его количество.

        Пример:
        engine.add_item("eggs", "many")
        """
        self.inventory[item_id] = amount

    def add_items(self, items: dict[str, str]) -> None:
        """
        Добавить сразу несколько ингредиентов.

        Пример:
        engine.add_items({
            "eggs": "many",
            "milk": "little",
        })
        """
        self.inventory.update(items)

    def remove_item(self, item_id: str) -> None:
        """
        Удалить ингредиент из кладовки.
        Если такого ингредиента нет, ошибки не будет.
        """
        self.inventory.pop(item_id, None)

    def item_name(self, item_id: str) -> str:
        """
        Получить человеческое название ингредиента.
        """
        return cnst.item_name(item_id, self.lang)

    def recipe_display_name(self, recipe: Recipe) -> str:
        """
        Вернуть отображаемое имя рецепта для текущего языка.

        Для украинского режима показываем пару:
        original / українська назва
        """
        original_name = (recipe.name or "").strip()
        localized_name = (recipe.name_uk or "").strip()

        if self.lang == "uk" and original_name and localized_name and localized_name != original_name:
            return f"{original_name} / {localized_name}"

        if self.lang == "uk" and localized_name:
            return localized_name

        return original_name or localized_name

    def recipe_explanation(self, key: str, **kwargs: object) -> str:
        return t(f"recipe.explanation.{key}", self.lang, **kwargs)

    def format_missing_explanation(self, item_name: str) -> str:
        return self.recipe_explanation("missing", name=item_name)

    def format_category_substitution(self, required_name: str, used_name: str) -> str:
        return self.recipe_explanation(
            "category_substitution",
            required=required_name,
            used=used_name,
        )

    def format_accepted_item_substitution(self, required_name: str, used_name: str) -> str:
        return self.recipe_explanation(
            "accepted_item_substitution",
            required=required_name,
            used=used_name,
        )

    def format_quantity_warning(self, item_name: str) -> str:
        return self.recipe_explanation("quantity_warning", name=item_name)

    def format_comment_label(self, comment: str) -> str:
        return self.recipe_explanation("comment_label", comment=comment)

    def filter_type_label(self, filter_type: str) -> str:
        return cnst.filter_type_label(filter_type, self.lang)

    def filter_value_label(self, filter_type: str, value: str) -> str:
        return cnst.filter_value_label(filter_type, value, self.lang)

    def format_filter_match_explanation(self, filter_type: str, value: str) -> str:
        return self.recipe_explanation(
            "filter_match",
            filter=self.filter_type_label(filter_type),
            value=self.filter_value_label(filter_type, value),
        )

    def format_filter_penalty_explanation(self, filter_type: str, value: str) -> str:
        return self.recipe_explanation(
            "filter_penalty",
            filter=self.filter_type_label(filter_type),
            value=self.filter_value_label(filter_type, value),
        )

    def format_preference_bonus_explanation(self, category_id: str) -> str:
        return self.recipe_explanation(
            "preference_bonus",
            category=cnst.category_name(category_id, self.lang),
        )

    def amount_factor(self, available_amount: str, needed_amount: str) -> float:
        """
        Сравнить количество имеющегося ингредиента с нужным количеством.

        Возвращает число от 0 до 1.
        """
        available = cnst.AMOUNT_SCALE.get(available_amount, 2.0)
        needed = cnst.AMOUNT_SCALE.get(needed_amount, 2.0)

        if needed <= 0:
            return 1.0

        return min(1.0, available / needed)

    def amount_value(self, amount: str | None) -> float:
        """
        Перевести amount-ярлык в числовую шкалу для локального расхода.
        """
        if not amount:
            return 0.0

        return float(cnst.AMOUNT_SCALE.get(amount, 2.0))

    def amount_factor_from_value(self, available_value: float, needed_amount: str) -> float:
        """
        Сравнить остаток ингредиента в числовом виде с нужным количеством.
        """
        needed = self.amount_value(needed_amount)

        if needed <= 0:
            return 1.0

        return min(1.0, max(0.0, available_value) / needed)

    def remaining_amount_value(
        self,
        item_id: str,
        inventory: dict[str, str],
        reservations: dict[str, float] | None = None,
    ) -> float:
        """
        Посчитать, сколько количества ещё осталось после локальных резерваций.
        """
        if item_id not in inventory:
            return 0.0

        reserved_amount = 0.0
        if reservations:
            reserved_amount = reservations.get(item_id, 0.0)

        available_value = self.amount_value(inventory[item_id])
        return max(0.0, available_value - reserved_amount)

    def should_warn_about_quantity(
        self,
        available_amount: str | None,
        available_value: float,
        needed_amount: str,
    ) -> bool:
        """
        Показать предупреждение, если ингредиент уже на грани или его не хватает.
        """
        if not available_amount:
            return False

        if available_amount == "little":
            return True

        return self.amount_factor_from_value(available_value, needed_amount) < 1.0

    def reserve_match_item(
        self,
        match_item: dict[str, Any],
        inventory: dict[str, str],
        reservations: dict[str, float],
    ) -> None:
        """
        Зарезервировать количество уже использованного ингредиента
        на время матчинга одного рецепта.
        """
        used_id = match_item.get("used_id")
        if not used_id:
            return

        remaining_value = self.remaining_amount_value(
            item_id=used_id,
            inventory=inventory,
            reservations=reservations,
        )
        if remaining_value <= 0:
            return

        needed_value = self.amount_value(match_item.get("required_amount"))
        if needed_value <= 0:
            return

        reservations[used_id] = round(
            reservations.get(used_id, 0.0) + min(remaining_value, needed_value),
            4,
        )

    def get_role_weight(self, role: str) -> float:
        """
        Получить вес роли ингредиента.

        Например:
        main важнее, чем spice.
        """
        if role not in cnst.ROLE_WEIGHT:
            raise ValueError(f"Неизвестная роль ингредиента: {role}")

        return cnst.ROLE_WEIGHT[role]
    
    def build_limits_by_status(
        self,
        limits_by_status: dict[str, int] | None = None,
        fallback_limit: int | None = None,
    ) -> dict[str, int]:
        """
        Собрать лимиты по статусам.

        Приоритет:
        1. пользовательские limits_by_status;
        2. DEFAULT_LIMITS_BY_STATUS;
        3. fallback_limit для неизвестных статусов.
        """
        default_limits = dict(cnst.DEFAULT_LIMITS_BY_STATUS)

        if limits_by_status:
            default_limits.update(limits_by_status)

        if fallback_limit is not None:
            for status in ("can_cook", "variant", "missing_one", "missing_main", "far"):
                default_limits.setdefault(status, fallback_limit)

        return default_limits
    
    def randomized_sort_key(
        self,
        match: dict[str, Any],
        random_strength: float,
    ) -> float:
        """
        Возвращает score с небольшим случайным шумом.

        Это нужно, чтобы выдача не была каждый раз одинаковой,
        но хорошие рецепты всё равно оставались в верхней части.
        """
        noise = random.uniform(-random_strength, random_strength)
        return match["score"] + noise
    
    def explicit_category_candidates(self, candidate_id: str) -> list[str]:
        """
        Собрать явные категории, которые стоят за item/category-кандидатом.

        Для category-кандидата используем саму категорию.
        Для abstract ingredient, который не является category, берём его прямые
        groups как "узкие" категории.
        """
        categories: list[str] = []

        if candidate_id in cnst.CATEGORIES:
            return [candidate_id]

        ingredient = cnst.INGREDIENTS.get(candidate_id, {})
        if candidate_id in cnst.ABSTRACT_INGREDIENTS:
            for group_id in ingredient.get("groups", []) or []:
                if group_id == "abstract_ingredient":
                    continue

                if group_id in cnst.CATEGORIES and group_id not in categories:
                    categories.append(group_id)

        return categories

    def groups_outside_category_family(
        self,
        item_id: str,
        category_id: str,
    ) -> set[str]:
        """
        Вернуть группы item, которые не принадлежат семейству category_id.

        Это помогает не терять "смысл" конкретного ингредиента, когда recipe
        разрешает замену через широкую accepts-категорию вроде fat или sauce.
        """
        ingredient = cnst.INGREDIENTS.get(item_id, {})
        outside_groups: set[str] = set()

        for group_id in ingredient.get("groups", []) or []:
            if group_id == category_id:
                continue

            if cnst.is_descendant(group_id, category_id):
                continue

            if cnst.is_descendant(category_id, group_id):
                continue

            outside_groups.add(group_id)

        return outside_groups

    def item_has_compatible_group_family(
        self,
        item_id: str,
        group_ids: set[str],
    ) -> bool:
        """
        Проверить, что item сохраняет хотя бы одну дополнительную group-family.
        """
        if not group_ids:
            return True

        used_groups = set(cnst.INGREDIENTS.get(item_id, {}).get("groups", []) or [])
        if not used_groups:
            return False

        for group_id in group_ids:
            for used_group in used_groups:
                if used_group == group_id:
                    return True

                if cnst.is_descendant(used_group, group_id):
                    return True

                if cnst.is_descendant(group_id, used_group):
                    return True

        return False

    def is_accept_category_match_compatible(
        self,
        need: Need,
        used_id: str,
        accepted_category_id: str,
    ) -> bool:
        """
        Замена через accepts-категорию должна сохранять хотя бы один
        дополнительный смысловой признак исходного ингредиента, если он есть.

        Примеры:
        - mustard -> mayonnaise через sauce: нет, потому что теряется pungent_spice
        - salo -> butter через fat: нет, потому что теряется meat_product
        - butter -> plant_oil через fat: да, у butter нет дополнительных групп
          вне семейства fat, которые recipe явно пытался сохранить
        """
        if need.item in cnst.ABSTRACT_INGREDIENTS:
            return True

        outside_groups = self.groups_outside_category_family(
            item_id=need.item,
            category_id=accepted_category_id,
        )

        if not outside_groups:
            return True

        return self.item_has_compatible_group_family(
            item_id=used_id,
            group_ids=outside_groups,
        )

    def collect_category_fallbacks(self, category_id: str) -> list[tuple[str, int]]:
        """
        Вернуть категорию и её родителей с глубиной из graph utilities каталога.
        """
        if category_id not in cnst.CATEGORIES:
            return []

        fallback_ids = {category_id}
        fallback_ids.update(cnst.collect_parent_categories(category_id))

        result: list[tuple[str, int]] = []
        for fallback_id in fallback_ids:
            distance = cnst.distance_to_category(category_id, fallback_id)
            if distance is None:
                continue

            result.append((fallback_id, distance))

        return sorted(
            result,
            key=lambda item: (item[1], 0 if item[0] == category_id else 1, item[0]),
        )

    def find_best_member_in_category(
        self,
        category_id: str,
        inventory: dict[str, str],
        needed_amount: str,
        reservations: dict[str, float] | None = None,
    ) -> dict[str, Any] | None:
        """
        Найти лучший конкретный ингредиент внутри одной конкретной категории.
        """
        members = cnst.INGREDIENT_GROUPS.get(category_id, [])

        best_match = None
        best_factor = 0.0
        best_remaining_value = 0.0

        for member_id in members:
            if member_id not in inventory:
                continue

            available_amount = inventory[member_id]
            remaining_value = self.remaining_amount_value(
                item_id=member_id,
                inventory=inventory,
                reservations=reservations,
            )
            if remaining_value <= 0:
                continue

            factor = self.amount_factor_from_value(remaining_value, needed_amount)

            if (
                best_match is None
                or factor > best_factor
                or (factor == best_factor and remaining_value > best_remaining_value)
            ):
                best_match = {
                    "used_id": member_id,
                    "used_name": self.item_name(member_id),
                    "available_amount": available_amount,
                    "available_amount_value": round(remaining_value, 4),
                    "quantity_factor": factor,
                }
                best_factor = factor
                best_remaining_value = remaining_value

        return best_match

    def find_category_match(
        self,
        need: Need,
        inventory: dict[str, str],
        reservations: dict[str, float] | None = None,
    ) -> dict[str, Any] | None:
        """
        Ранжированный поиск по категориям:
        explicit narrow category -> direct parent category with depth penalty.

        Parent fallback держим узким:
        - только один шаг вверх;
        - только для категорий из accepts, а не для required item напрямую.
        """
        role_weight = self.get_role_weight(need.role)
        category_searches_by_depth: dict[int, list[dict[str, Any]]] = {}

        explicit_candidates = [("item", need.item)] + [
            ("accepts", accepted_id) for accepted_id in need.accepts
        ]

        for relation, candidate_id in explicit_candidates:
            match_type = "category_match" if relation == "item" else "accepted_category_match"
            base_similarity = (
                cnst.CATEGORY_MATCH_SIMILARITY
                if relation == "item"
                else cnst.ACCEPTED_CATEGORY_MATCH_SIMILARITY
            )

            for explicit_category_id in self.explicit_category_candidates(candidate_id):
                for search_category_id, depth in self.collect_category_fallbacks(explicit_category_id):
                    if depth > 0 and relation != "accepts":
                        continue

                    if (
                        relation == "accepts"
                        and explicit_category_id in cnst.STRICT_ACCEPT_PARENT_FALLBACK_CATEGORIES
                        and depth > 0
                    ):
                        continue

                    if depth > 1:
                        continue

                    if search_category_id in {"ingredient", "abstract_ingredient"}:
                        continue

                    category_searches_by_depth.setdefault(depth, []).append(
                        {
                            "origin_id": candidate_id,
                            "origin_name": self.item_name(candidate_id),
                            "relation": relation,
                            "match_type": match_type,
                            "explicit_category_id": explicit_category_id,
                            "search_category_id": search_category_id,
                            "depth": depth,
                            "base_similarity": base_similarity,
                        }
                    )

        for depth in sorted(category_searches_by_depth):
            best_result = None
            best_score = -1.0
            best_factor = -1.0
            best_remaining_value = -1.0

            for search in category_searches_by_depth[depth]:
                category_match = self.find_best_member_in_category(
                    category_id=search["search_category_id"],
                    inventory=inventory,
                    needed_amount=need.amount,
                    reservations=reservations,
                )
                if category_match is None:
                    continue

                if search["relation"] == "accepts":
                    if (
                        search["explicit_category_id"] in cnst.BROAD_ACCEPT_CATEGORIES
                        and not self.is_accept_category_match_compatible(
                            need=need,
                            used_id=category_match["used_id"],
                            accepted_category_id=search["explicit_category_id"],
                        )
                    ):
                        continue

                similarity = max(
                    0.0,
                    search["base_similarity"] - depth * cnst.CATEGORY_DEPTH_PENALTY,
                )
                if similarity <= 0:
                    continue

                factor = category_match["quantity_factor"]
                score = role_weight * similarity * factor

                if (
                    best_result is None
                    or score > best_score
                    or (score == best_score and factor > best_factor)
                    or (
                        score == best_score
                        and factor == best_factor
                        and category_match["available_amount_value"] > best_remaining_value
                    )
                ):
                    quantity_warning = None
                    if self.should_warn_about_quantity(
                        available_amount=category_match["available_amount"],
                        available_value=category_match["available_amount_value"],
                        needed_amount=need.amount,
                    ):
                        quantity_warning = self.format_quantity_warning(
                            category_match["used_name"]
                        )

                    best_result = {
                        "required_id": need.item,
                        "required_name": self.item_name(need.item),
                        "required_amount": need.amount,
                        "accepts": list(need.accepts),
                        "used_id": category_match["used_id"],
                        "used_name": category_match["used_name"],
                        "available_amount": category_match["available_amount"],
                        "available_amount_value": category_match["available_amount_value"],
                        "role": need.role,
                        "match_type": search["match_type"],
                        "source_id": search["search_category_id"],
                        "source_name": self.item_name(search["search_category_id"]),
                        "source_relation": search["relation"],
                        "source_kind": "category" if depth == 0 else "parent_category",
                        "source_depth": depth,
                        "source_origin_id": search["origin_id"],
                        "source_origin_name": search["origin_name"],
                        "score": round(score, 2),
                        "max_score": role_weight,
                        "quantity_factor": round(factor, 2),
                        "quantity_warning": quantity_warning,
                        "note": need.note,
                    }
                    best_score = score
                    best_factor = factor
                    best_remaining_value = category_match["available_amount_value"]

            if best_result is not None:
                return best_result

        return None

    def minor_missing_weight(self, item: dict[str, Any]) -> float:
        """
        Насколько missing второстепенного ингредиента должен влиять на status.

        main / required здесь не считаем:
        они обрабатываются как первичные missing отдельно.
        """
        role = item.get("role")
        amount = item.get("required_amount", "normal")

        base_weight = {
            "addition": cnst.MISSING_ADDITION_PENALTY,
            "spice": cnst.MISSING_SPICE_PENALTY,
            "optional": 0.0,
        }.get(role, 0.0)

        amount_multiplier = {
            "spice": 0.5,
            "little": 0.75,
            "normal": 1.0,
            "many": 1.0,
        }.get(amount, 1.0)

        return round(base_weight * amount_multiplier, 4)

    def analyze_missing_items(
        self,
        recipe: Recipe,
        missing: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """
        Разделяет missing на:
        - primary: main / required
        - tolerated minor: addition / spice / optional, которые укладываются в missing_allowed
        - critical minor: второстепенные, которые уже вышли за лимит missing_allowed
        """
        primary_missing: list[dict[str, Any]] = []
        main_missing: list[dict[str, Any]] = []
        soft_required_missing: list[tuple[dict[str, Any], float]] = []
        minor_candidates: list[tuple[dict[str, Any], float]] = []

        for item in missing:
            role = item.get("role")
            amount = item.get("required_amount", "normal")

            if role == "main":
                main_missing.append(item)
                primary_missing.append(item)
                continue

            if role == "required":
                if amount == "spice":
                    soft_required_missing.append(
                        (item, cnst.MISSING_REQUIRED_SPICE_PENALTY)
                    )
                    continue

                primary_missing.append(item)
                continue

            minor_candidates.append((item, self.minor_missing_weight(item)))

        remaining_minor_budget = float(max(recipe.missing_allowed, 0))
        critical_minor_missing: list[dict[str, Any]] = []
        tolerated_minor_missing: list[dict[str, Any]] = []

        for item, weight in sorted(
            minor_candidates,
            key=lambda pair: pair[1],
            reverse=True,
        ):
            if weight <= 0:
                tolerated_minor_missing.append(item)
                continue

            if remaining_minor_budget >= weight:
                remaining_minor_budget -= weight
                tolerated_minor_missing.append(item)
                continue

            critical_minor_missing.append(item)

        blocking_missing_score = (
            float(len(primary_missing))
            + sum(weight for _, weight in soft_required_missing)
            + sum(self.minor_missing_weight(item) for item in critical_minor_missing)
        )

        return {
            "main_missing": main_missing,
            "primary_missing": primary_missing,
            "soft_required_missing": [item for item, _ in soft_required_missing],
            "critical_minor_missing": critical_minor_missing,
            "tolerated_minor_missing": tolerated_minor_missing,
            "critical_missing": primary_missing + [item for item, _ in soft_required_missing] + critical_minor_missing,
            "blocking_missing_score": round(blocking_missing_score, 4),
            "remaining_minor_budget": round(remaining_minor_budget, 4),
        }

    def match_need(
        self,
        need: Need,
        inventory: dict[str, str] | None = None,
        reservations: dict[str, float] | None = None,
        ) -> dict[str, Any]:
        """
        Сравнить один нужный ингредиент рецепта с кладовкой.

        Умеет:
        - точное совпадение: rice -> rice
        - явный вариант: lamb -> chicken_fillet через accepts
        - категориальное совпадение: meat -> chicken_fillet
        """

        current_inventory = inventory if inventory is not None else self.inventory

        role_weight = self.get_role_weight(need.role)

        # 1. Точное совпадение нужного item.
        if need.item in current_inventory:
            available_amount = current_inventory[need.item]
            available_value = self.remaining_amount_value(
                item_id=need.item,
                inventory=current_inventory,
                reservations=reservations,
            )
            if available_value > 0:
                factor = self.amount_factor_from_value(available_value, need.amount)
                quantity_warning = None
                if self.should_warn_about_quantity(
                    available_amount=available_amount,
                    available_value=available_value,
                    needed_amount=need.amount,
                ):
                    quantity_warning = self.format_quantity_warning(
                        self.item_name(need.item)
                    )

                return {
                    "required_id": need.item,
                    "required_name": self.item_name(need.item),
                    "required_amount": need.amount,
                    "accepts": list(need.accepts),
                    "used_id": need.item,
                    "used_name": self.item_name(need.item),
                    "available_amount": available_amount,
                    "available_amount_value": round(available_value, 4),
                    "role": need.role,
                    "match_type": "exact",
                    "source_id": need.item,
                    "source_name": self.item_name(need.item),
                    "source_relation": "item",
                    "source_kind": "ingredient",
                    "source_depth": 0,
                    "score": round(role_weight * factor, 2),
                    "max_score": role_weight,
                    "quantity_factor": round(factor, 2),
                    "quantity_warning": quantity_warning,
                    "note": need.note,
                }

        # 2. Явные ingredient accepts: они важнее любого category fallback.
        best_accept_item_match = None
        best_accept_item_score = -1.0
        best_accept_item_factor = -1.0
        best_accept_item_remaining = -1.0

        for candidate in need.accepts:
            if candidate not in current_inventory:
                continue

            available_amount = current_inventory[candidate]
            available_value = self.remaining_amount_value(
                item_id=candidate,
                inventory=current_inventory,
                reservations=reservations,
            )
            if available_value <= 0:
                continue

            factor = self.amount_factor_from_value(available_value, need.amount)
            score = role_weight * 0.75 * factor

            if (
                best_accept_item_match is None
                or score > best_accept_item_score
                or (score == best_accept_item_score and factor > best_accept_item_factor)
                or (
                    score == best_accept_item_score
                    and factor == best_accept_item_factor
                    and available_value > best_accept_item_remaining
                )
            ):
                quantity_warning = None
                if self.should_warn_about_quantity(
                    available_amount=available_amount,
                    available_value=available_value,
                    needed_amount=need.amount,
                ):
                    quantity_warning = self.format_quantity_warning(
                        self.item_name(candidate)
                    )

                best_accept_item_match = {
                    "required_id": need.item,
                    "required_name": self.item_name(need.item),
                    "required_amount": need.amount,
                    "accepts": list(need.accepts),
                    "used_id": candidate,
                    "used_name": self.item_name(candidate),
                    "available_amount": available_amount,
                    "available_amount_value": round(available_value, 4),
                    "role": need.role,
                    "match_type": "accepted_variant",
                    "source_id": candidate,
                    "source_name": self.item_name(candidate),
                    "source_relation": "accepts",
                    "source_kind": "ingredient",
                    "source_depth": 0,
                    "score": round(score, 2),
                    "max_score": role_weight,
                    "quantity_factor": round(factor, 2),
                    "quantity_warning": quantity_warning,
                    "note": need.note,
                }
                best_accept_item_score = score
                best_accept_item_factor = factor
                best_accept_item_remaining = available_value

        if best_accept_item_match is not None:
            return best_accept_item_match

        # 3. Явные категории, затем подъём к родителям с растущим штрафом.
        category_match = self.find_category_match(
            need=need,
            inventory=current_inventory,
            reservations=reservations,
        )
        if category_match is not None:
            return category_match

        return {
            "required_id": need.item,
            "required_name": self.item_name(need.item),
            "required_amount": need.amount,
            "accepts": list(need.accepts),
            "used_id": None,
            "used_name": None,
            "available_amount": None,
            "available_amount_value": 0.0,
            "role": need.role,
            "match_type": "missing",
            "source_id": None,
            "source_name": None,
            "source_relation": None,
            "source_kind": None,
            "source_depth": None,
            "score": 0.0,
            "max_score": role_weight,
            "quantity_factor": 0.0,
            "quantity_warning": None,
            "note": need.note,
        }
    
    
    
    def match_recipe(
        self,
        recipe: Recipe,
        inventory: dict[str, str] | None = None,
        filters: list[tuple[str, str]] | None = None,
        prefer_categories: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Сравнить один рецепт с текущей кладовкой.

        Можно передать inventory отдельно.
        Тогда метод не изменит внутреннюю кладовку engine.
        """

        current_inventory = inventory if inventory is not None else self.inventory

        matches = []
        missing = []
        reservations: dict[str, float] = {}

        total_score = 0.0
        max_score = 0.0

        for need in recipe.ingredients:
            result = self.match_need(
                need,
                current_inventory,
                reservations=reservations,
            )

            matches.append(result)
            total_score += result["score"]
            max_score += result["max_score"]

            if result["used_id"]:
                self.reserve_match_item(
                    match_item=result,
                    inventory=current_inventory,
                    reservations=reservations,
                )

            if result["match_type"] == "missing":
                missing.append(result)

        normalized_score = total_score / max_score if max_score else 0.0

        missing_analysis = self.analyze_missing_items(
            recipe=recipe,
            missing=missing,
        )

        missing_main = missing_analysis["main_missing"]
        critical_missing = missing_analysis["critical_missing"]
        tolerated_missing = missing_analysis["tolerated_minor_missing"]
        blocking_missing_score = missing_analysis["blocking_missing_score"]

        warnings = [
            item for item in matches
            if item["quantity_warning"]
        ]

        base_score = normalized_score

        filtered_score, filter_explanations = self.apply_filter_score(
            recipe=recipe,
            base_score=base_score,
            filters=filters or [],
        )

        final_score, preference_explanations = self.apply_preference_score(
            recipe=recipe,
            base_score=filtered_score,
            prefer_categories=prefer_categories or [],
        )

        if missing_main:
            status = "missing_main"
        elif blocking_missing_score < 0.25:
            if final_score >= 0.85:
                status = "can_cook"
            elif final_score >= 0.65:
                status = "variant"
            else:
                status = "far"
        elif blocking_missing_score <= 1.25:
            status = "missing_one"
        elif blocking_missing_score > 1.25:
            status = "far"
        else:
            status = "far"

        

        explanations = []
        seen_match_explanations: set[tuple[str | None, str | None, str]] = set()
        seen_warning_explanations: set[tuple[str | None, str]] = set()

        def append_match_explanation(item: dict[str, Any], text: str) -> None:
            key = (
                item["required_id"],
                item["used_id"],
                item["match_type"],
            )

            if key in seen_match_explanations:
                return

            seen_match_explanations.add(key)
            explanations.append(text)

        def append_quantity_warning(item: dict[str, Any]) -> None:
            warning = item["quantity_warning"]

            if not warning:
                return

            key = (item["used_id"], warning)
            if key in seen_warning_explanations:
                return

            seen_warning_explanations.add(key)
            explanations.append(warning)

        for item in matches:
            if item["match_type"] == "accepted_variant":
                append_match_explanation(
                    item,
                    self.format_accepted_item_substitution(
                        item["required_name"],
                        item["used_name"],
                    )
                )

            if item["match_type"] == "category_match":
                append_match_explanation(
                    item,
                    self.format_category_substitution(
                        item["required_name"],
                        item["used_name"],
                    )
                )

            if item["match_type"] == "accepted_category_match":
                append_match_explanation(
                    item,
                    self.format_category_substitution(
                        item["required_name"],
                        item["used_name"],
                    )
                )

            append_quantity_warning(item)

        for item in critical_missing:
            if item["role"] in ("main", "required", "addition"):
                explanations.append(
                    self.format_missing_explanation(item["required_name"])
                )

        explanations.extend(filter_explanations)
        explanations.extend(preference_explanations)

        return {
                "recipe_id": recipe.id,
                "name": self.recipe_display_name(recipe),
                "score": round(final_score, 2),
                "base_score": round(base_score, 2),
                "filtered_score": round(filtered_score, 2),
                "status": status,
                "comment": recipe.comment,
                "comment_text": (
                    self.format_comment_label(recipe.comment)
                    if recipe.comment
                    else ""
                ),
                "matches": matches,
                "missing": missing,
                "critical_missing": critical_missing,
                "tolerated_missing": tolerated_missing,
                "missing_allowed": recipe.missing_allowed,
                "blocking_missing_score": round(blocking_missing_score, 2),
                "warnings": warnings,
                "explanations": explanations,
                "facets": recipe.facets,
                "tags": recipe.tags,
            }
    
    def normalize_filters(self, filters: list[str] | None) -> list[tuple[str, str]]:
        if not filters:
            return []

        normalized = []

        for raw_filter in filters:
            key = raw_filter.strip().lower()

            if key in cnst.FILTER_ALIASES:
                normalized.append(cnst.FILTER_ALIASES[key])
            else:
                # запасной вариант:
                # если фильтр совпадает с категорией ингредиентов
                if key in cnst.CATEGORIES:
                    normalized.append(("ingredient_group", key))
                else:
                    normalized.append(("tag", key))

        return normalized
    
    def recipe_ingredient_ids(self, recipe: Recipe) -> set[str]:
        ids = set()

        for need in recipe.ingredients:
            ids.add(need.item)
            ids.update(need.accepts)

        return ids
    
    def recipe_time_matches(self, recipe_time: str | None, requested_time: str) -> bool:
        """
        Проверяет соответствие фильтру времени.

        Пример:
        recipe_time = "under_10"
        requested_time = "under_30"
        => True

        recipe_time = "under_60"
        requested_time = "under_30"
        => False
        """
        if not recipe_time:
            return False

        if recipe_time == requested_time:
            return True

        # "больше часа" — отдельная категория.
        # Не считаем, что under_10 подходит под over_60.
        if requested_time == "over_60":
            return recipe_time == "over_60"

        if recipe_time == "over_60":
            return False

        recipe_minutes = cnst.TIME_BUCKET_MINUTES.get(recipe_time)
        requested_minutes = cnst.TIME_BUCKET_MINUTES.get(requested_time)

        if recipe_minutes is None or requested_minutes is None:
            return False

        return recipe_minutes <= requested_minutes


    def recipe_has_ingredient_group(self, recipe: Recipe, group_id: str) -> bool:
        recipe_items = self.recipe_ingredient_ids(recipe)

        # Если рецепт прямо содержит item: legume
        if group_id in recipe_items:
            return True

        group_members = set(cnst.INGREDIENT_GROUPS.get(group_id, []))

        # Если рецепт содержит beans / red_lentils / canned_peas
        if recipe_items & group_members:
            return True

        # Если рецепт уже помечен тегом legume
        if group_id in recipe.tags:
            return True

        return False
    
    def normalize_prefer_categories(
        self,
        prefer_categories: list[str] | None,
    ) -> list[str]:
        """
        Нормализует preferred categories.

        Например:
        мясо -> meat
        бобовые -> legume
        mushroom -> mushroom
        """
        if not prefer_categories:
            return []

        normalized = []

        for raw_value in prefer_categories:
            key = raw_value.strip().lower()

            if key in cnst.FILTER_ALIASES:
                filter_type, value = cnst.FILTER_ALIASES[key]

                if filter_type == "ingredient_group":
                    normalized.append(value)
                    continue

            if key in cnst.CATEGORIES:
                normalized.append(key)
                continue

            # запасной вариант: если пользователь ввёл неизвестное,
            # пока пропускаем, чтобы не ломать программу
            # можно позже сделать warning
            continue

        return sorted(set(normalized))
    
    def ingredient_belongs_to_category(self, item_id: str, category_id: str) -> bool:
        """
        Проверяет, относится ли item_id к category_id.

        Работает и для:
        - прямой категории: item_id == category_id
        - конкретного ингредиента внутри категории
        """
        return cnst.is_descendant(item_id, category_id)


    def need_matches_category(self, need: Need, category_id: str) -> bool:
        """
        Проверяет, связан ли один Need с категорией.
        Учитывает item и accepts.
        """
        if self.ingredient_belongs_to_category(need.item, category_id):
            return True

        for accepted_id in need.accepts:
            if self.ingredient_belongs_to_category(accepted_id, category_id):
                return True

        return False


    def recipe_category_strength(self, recipe: Recipe, category_id: str) -> float:
        """
        Возвращает силу связи рецепта с категорией от 0 до 1.

        main      -> сильная связь
        required  -> средняя
        addition  -> слабая
        tag       -> слабая, если ингредиенты не поймали
        """
        best_strength = 0.0

        for need in recipe.ingredients:
            if not self.need_matches_category(need, category_id):
                continue

            role_multiplier = cnst.PREFER_CATEGORY_ROLE_MULTIPLIER.get(
                need.role,
                0.0,
            )

            best_strength = max(best_strength, role_multiplier)

        # Если в ингредиентах не нашли, но тег есть,
        # всё равно даём слабую связь.
        if best_strength == 0.0 and category_id in recipe.tags:
            best_strength = 0.3

        return best_strength
    
    def apply_preference_score(
        self,
        recipe: Recipe,
        base_score: float,
        prefer_categories: list[str],
    ) -> tuple[float, list[str]]:
        """
        Повышает score за preferred categories.

        Важно:
        не штрафует за отсутствие категории.
        """
        if not prefer_categories:
            return base_score, []

        score = base_score
        explanations = []

        for category_id in prefer_categories:
            strength = self.recipe_category_strength(recipe, category_id)

            if strength <= 0:
                continue

            weight = cnst.PREFER_CATEGORY_WEIGHTS.get(
                category_id,
                cnst.PREFER_CATEGORY_WEIGHT,
            )

            bonus = weight * strength
            score += bonus

            explanations.append(
                self.format_preference_bonus_explanation(category_id)
            )

        score = max(0.0, min(1.0, score))

        return score, explanations


    def recipe_matches_filter(self, recipe: Recipe, filter_type: str, value: str) -> bool:
        if filter_type == "ingredient_group":
            return self.recipe_has_ingredient_group(recipe, value)

        if filter_type == "tag":
            return value in recipe.tags

        facets = recipe.facets or {}

        if filter_type == "cuisine":
            return value in facets.get("cuisine", [])

        if filter_type == "dish_type":
            return value in facets.get("dish_type", [])

        if filter_type == "method":
            return value in facets.get("method", [])

        if filter_type == "time":
            return self.recipe_time_matches(
                recipe_time=facets.get("time"),
                requested_time=value,
            )

        return False
    
    def apply_filter_score(
        self,
        recipe: Recipe,
        base_score: float,
        filters: list[tuple[str, str]],
    ) -> tuple[float, list[str]]:
        """
        Возвращает:
        - новый score
        - объяснения фильтров
        """
        if not filters:
            return base_score, []

        score = base_score
        explanations = []

        for filter_type, value in filters:
            weight = cnst.FILTER_WEIGHTS.get(filter_type, 0.08)

            if self.recipe_matches_filter(recipe, filter_type, value):
                bonus = weight
                score += bonus
                explanations.append(
                    self.format_filter_match_explanation(filter_type, value)
                )
            else:
                penalty = weight
                score -= penalty
                explanations.append(
                    self.format_filter_penalty_explanation(filter_type, value)
                )

        score = max(0.0, min(1.0, score))

        return score, explanations

    def suggest(
        self,
        inventory: dict[str, str] | None = None,
        recipes: list[Recipe] | None = None,
        limit_per_group: int | None = None,
        limits_by_status: dict[str, int] | None = None,
        filters: list[str] | None = None,
        prefer_categories: list[str] | None = None,
        randomize: bool = False,
        random_strength: float = 0.06,
        seed: int | None = None,
    ) -> dict[str, Any]:
        """
        Подобрать блюда.

        Если inventory не передан, используется внутренняя кладовка.
        Если recipes не передан, используется внутренний список рецептов.

        Это основной метод, который потом будет удобно вызывать из Telegram.
        """

        current_inventory = inventory if inventory is not None else self.inventory
        current_recipes = recipes if recipes is not None else self.recipes
        current_limit = (
            limit_per_group
            if limit_per_group is not None
            else self.limit_per_group
        )

        current_limits_by_status = self.build_limits_by_status(
            limits_by_status=limits_by_status or self.limits_by_status,
            fallback_limit=current_limit,
        )

        normalized_filters = self.normalize_filters(filters)
        normalized_prefer_categories = self.normalize_prefer_categories(
            prefer_categories
        )

        all_matches = [
        self.match_recipe(
            recipe=recipe,
            inventory=current_inventory,
            filters=normalized_filters,
            prefer_categories=normalized_prefer_categories,
        )
        for recipe in current_recipes
        ]

        # all_matches.sort(key=lambda item: item["score"], reverse=True)

        result = {
            "can_cook": [],
            "variant": [],
            "missing_one": [],
            "missing_main": [],
            "far": [],
        }


        for match in all_matches:
            result[match["status"]].append(match)

        if seed is not None:
            random.seed(seed)

        for key, matches in result.items():
            if randomize:
                for match in matches:
                    match["sort_score"] = round(
                        self.randomized_sort_key(match, random_strength),
                        4,
                    )

                matches.sort(key=lambda item: item["sort_score"], reverse=True)
            else:
                for match in matches:
                    match["sort_score"] = match["score"]

                matches.sort(key=lambda item: item["score"], reverse=True)

            status_limit = current_limits_by_status.get(key, current_limit)

            if status_limit <= 0:
                result[key] = []
            else:
                result[key] = matches[:status_limit]

        return {
            "inventory": dict(current_inventory),
            "filters": normalized_filters,
            "prefer_categories": normalized_prefer_categories,
            "suggestions": result,
        }

    def find_recipe_by_id(self, recipe_id: str) -> Recipe | None:
        """
        Найти рецепт по id.
        """
        for recipe in self.recipes:
            if recipe.id == recipe_id:
                return recipe

        return None

    def match_recipe_by_id(
        self,
        recipe_id: str,
        inventory: dict[str, str] | None = None,
    ) -> dict[str, Any] | None:
        """
        Сравнить конкретный рецепт с кладовкой по его id.
        """
        recipe = self.find_recipe_by_id(recipe_id)

        if recipe is None:
            return None

        return self.match_recipe(recipe, inventory)
