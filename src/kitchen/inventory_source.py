from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, Literal

import yaml

from . import constants as cnst
from .i18n import DEFAULT_LANG, normalize_language, t


InventoryMode = Literal["yaml", "csv", "cli"]

ALLOWED_AMOUNTS = ("none", "spice", "little", "normal", "many")


class InventorySource:
    """
    Единый класс для работы с кладовкой пользователя.

    Поддерживает 3 режима:
    - yaml: current_inventory.yaml
    - csv: current_inventory.<lang>.csv
    - cli: интерактивный ввод в командной строке

    На выходе всегда отдаёт dict[str, str], подходящий для RecipeEngine:
    {
        "eggs": "many",
        "flour": "little",
    }

    Ингредиенты с amount == "none" отфильтровываются.
    """

    def __init__(
        self,
        recipes_path: str,
        mode: InventoryMode = "yaml",
        inventory_path: str | None = None,
        include_accepts: bool = True,
        lang: str = DEFAULT_LANG,
    ) -> None:
        self.recipes_path = Path(recipes_path)
        self.mode = mode
        self.include_accepts = include_accepts
        self.lang = normalize_language(lang)

        if mode not in ("yaml", "csv", "cli"):
            raise ValueError(
                f"Неизвестный режим: {mode}. "
                f"Можно: yaml, csv, cli"
            )

        if inventory_path is None:
            if mode == "yaml":
                inventory_path = str(cnst.CURRENT_INVENTORY_YAML_PATH)
            elif mode == "csv":
                inventory_path = str(cnst.inventory_csv_path_for_lang(self.lang))
            else:
                inventory_path = ""

        self.inventory_path = Path(inventory_path) if inventory_path else None

    # -------------------------
    # Общие служебные методы
    # -------------------------

    def item_name(self, item_id: str) -> str:
        return cnst.item_name(item_id, self.lang)

    def resolve_existing_csv_inventory_path(self) -> Path | None:
        if self.inventory_path is None:
            return None

        if self.inventory_path.exists():
            return self.inventory_path

        preferred_path = cnst.inventory_csv_path_for_lang(self.lang)
        if self.inventory_path != preferred_path:
            return self.inventory_path

        for candidate in cnst.inventory_csv_candidates_for_lang(self.lang):
            if candidate.exists():
                return candidate

        return self.inventory_path

    def normalize_inventory_entry(
        self,
        item_id: str,
        item_data: Any,
    ) -> dict[str, str]:
        amount = "none"

        if isinstance(item_data, dict):
            amount = str(item_data.get("amount", "none") or "none").strip().lower()
        elif isinstance(item_data, str):
            amount = item_data.strip().lower() or "none"

        if amount not in ALLOWED_AMOUNTS:
            amount = "none"

        return {
            "name": self.item_name(item_id),
            "amount": amount,
        }

    def normalize_inventory_mapping(
        self,
        inventory: dict[str, Any],
    ) -> dict[str, dict[str, str]]:
        normalized: dict[str, dict[str, str]] = {}

        for raw_item_id, item_data in inventory.items():
            item_id = str(raw_item_id)
            normalized[item_id] = self.normalize_inventory_entry(item_id, item_data)

        return normalized

    def load_recipes_yaml(self) -> dict[str, Any]:
        if not self.recipes_path.exists():
            raise FileNotFoundError(f"Файл рецептов не найден: {self.recipes_path}")

        with self.recipes_path.open("r", encoding="utf-8") as file:
            data = yaml.safe_load(file)

        return data or {}

    def collect_ingredient_ids(self) -> list[str]:
        """
        Собрать все конкретные ингредиенты из файла рецептов.

        Важно:
        абстрактные категории вроде meat, grain, fat
        не попадают в CSV/YAML как заполняемые строки.

        Если рецепт использует item: meat,
        в шаблон добавляются конкретные продукты из группы meat:
        chicken_fillet, lamb, stew и т.д.
        """
        data = self.load_recipes_yaml()
        ingredient_ids = set()

        def add_item_or_group_members(item_id: str) -> None:
            if not item_id:
                return

            if self.is_abstract_ingredient(item_id):
                for concrete_id in cnst.INGREDIENT_GROUPS.get(item_id, []):
                    ingredient_ids.add(concrete_id)
            else:
                ingredient_ids.add(item_id)

        for recipe in data.get("recipes", []):
            for ingredient in recipe.get("ingredients", []):
                item_id = ingredient.get("item")
                add_item_or_group_members(item_id)

                if self.include_accepts:
                    for accepted_id in ingredient.get("accepts", []):
                        add_item_or_group_members(accepted_id)
        ingredient_ids -= cnst.HIDDEN_FROM_INVENTORY_TEMPLATE
        return sorted(ingredient_ids)
    
    
    def make_empty_inventory(self) -> dict[str, dict[str, str]]:
        """
        Создать полный список ингредиентов с amount: none.
        """
        inventory = {}

        for item_id in self.collect_ingredient_ids():
            inventory[item_id] = {
                "name": self.item_name(item_id),
                "amount": "none",
            }

        return inventory

    def validate_amount(self, amount: str) -> str:
        amount = amount.strip().lower()

        if amount not in ALLOWED_AMOUNTS:
            raise ValueError(
                f"Некорректное количество: {amount}. "
                f"Можно: {', '.join(ALLOWED_AMOUNTS)}"
            )

        return amount

    def filter_for_engine(
        self,
        full_inventory: dict[str, dict[str, str]],
    ) -> dict[str, str]:
        """
        Убрать все amount: none.

        Именно этот результат надо отдавать в RecipeEngine.
        """
        result = {}

        for item_id, item_data in full_inventory.items():
            amount = item_data.get("amount", "none")

            if amount != "none":
                result[item_id] = amount

        return result
    

    def add_always_available(
        self,
        inventory: dict[str, str],
    ) -> dict[str, str]:
        """
        Добавить системные ингредиенты, которые считаются всегда доступными.

        Например:
        water: many

        setdefault нужен, чтобы не перетирать значение,
        если оно уже почему-то было задано вручную.
        """
        result = dict(inventory)

        for item_id, amount in cnst.ALWAYS_AVAILABLE_INVENTORY.items():
            result.setdefault(item_id, amount)

        return result
    
    def is_abstract_ingredient(self, item_id: str) -> bool:
        return (
            item_id in cnst.ABSTRACT_INGREDIENTS
            or item_id in cnst.INGREDIENT_GROUPS
        )

    # -------------------------
    # YAML mode
    # -------------------------

    def load_yaml_inventory_full(self) -> dict[str, dict[str, str]]:
        if self.inventory_path is None:
            raise ValueError("Для yaml-режима нужен inventory_path.")

        if not self.inventory_path.exists():
            return self.make_empty_inventory()

        with self.inventory_path.open("r", encoding="utf-8") as file:
            data = yaml.safe_load(file)

        data = data or {}
        raw_inventory = data.get("inventory", {}) or {}
        return self.normalize_inventory_mapping(raw_inventory)

    def save_yaml_inventory_full(
        self,
        inventory: dict[str, dict[str, str]],
    ) -> None:
        if self.inventory_path is None:
            raise ValueError("Для yaml-режима нужен inventory_path.")

        normalized_inventory = self.normalize_inventory_mapping(inventory)
        data = {
            "amount_values": list(ALLOWED_AMOUNTS),
            "inventory": normalized_inventory,
        }

        with self.inventory_path.open("w", encoding="utf-8") as file:
            yaml.safe_dump(
                data,
                file,
                allow_unicode=True,
                sort_keys=True,
            )

    def sync_yaml_template(self, overwrite: bool = False) -> None:
        """
        Обновить YAML-файл списком всех ингредиентов из рецептов.

        overwrite=False сохраняет уже проставленные количества.
        overwrite=True сбрасывает всё в none.
        """
        existing = self.load_yaml_inventory_full()
        fresh = self.make_empty_inventory()

        if not overwrite:
            for item_id, item_data in fresh.items():
                if item_id in existing:
                    old_amount = existing[item_id].get("amount", "none")

                    if old_amount in ALLOWED_AMOUNTS:
                        item_data["amount"] = old_amount

        self.save_yaml_inventory_full(fresh)

    # -------------------------
    # CSV mode
    # -------------------------

    def load_csv_inventory_full(self) -> dict[str, dict[str, str]]:
        if self.inventory_path is None:
            raise ValueError("Для csv-режима нужен inventory_path.")

        csv_path = self.resolve_existing_csv_inventory_path()
        if csv_path is None or not csv_path.exists():
            return self.make_empty_inventory()

        inventory = {}

        with csv_path.open("r", encoding="utf-8", newline="") as file:
            reader = csv.DictReader(file)

            for row in reader:
                item_id = row.get("item_id", "").strip()

                if not item_id:
                    continue

                amount = row.get("amount", "none").strip().lower()

                if amount not in ALLOWED_AMOUNTS:
                    amount = "none"

                inventory[item_id] = {
                    "name": self.item_name(item_id),
                    "amount": amount,
                }

        return inventory

    def save_csv_inventory_full(
        self,
        inventory: dict[str, dict[str, str]],
    ) -> None:
        if self.inventory_path is None:
            raise ValueError("Для csv-режима нужен inventory_path.")

        self.inventory_path.parent.mkdir(parents=True, exist_ok=True)
        with self.inventory_path.open("w", encoding="utf-8", newline="") as file:
            writer = csv.DictWriter(
                file,
                fieldnames=["item_id", "name", "amount"],
            )

            writer.writeheader()

            normalized_inventory = self.normalize_inventory_mapping(inventory)

            for item_id, item_data in sorted(normalized_inventory.items()):
                writer.writerow({
                    "item_id": item_id,
                    "name": item_data["name"],
                    "amount": item_data.get("amount", "none"),
                })

    def sync_csv_template(self, overwrite: bool = False) -> None:
        """
        Обновить CSV-файл списком всех ингредиентов из рецептов.
        """
        existing = self.load_csv_inventory_full()
        fresh = self.make_empty_inventory()

        if not overwrite:
            for item_id, item_data in fresh.items():
                if item_id in existing:
                    old_amount = existing[item_id].get("amount", "none")

                    if old_amount in ALLOWED_AMOUNTS:
                        item_data["amount"] = old_amount

        self.save_csv_inventory_full(fresh)

    # -------------------------
    # CLI mode
    # -------------------------

    def ask_cli_inventory_full(self) -> dict[str, dict[str, str]]:
        """
        Интерактивно спросить пользователя о каждом ингредиенте.

        Enter оставляет none.
        """
        inventory = self.make_empty_inventory()

        print()
        print(t("cli.inventory_edit_title", self.lang))
        print("-" * 40)
        print(t("cli.inventory_allowed_amounts", self.lang))
        print(t("cli.inventory_enter_keeps_none", self.lang))
        print()

        for item_id, item_data in inventory.items():
            name = item_data["name"]

            while True:
                user_input = input(f"{item_id} | {name}: ").strip().lower()

                if not user_input:
                    amount = "none"
                    break

                if user_input in ALLOWED_AMOUNTS:
                    amount = user_input
                    break

                print(
                    t(
                        "cli.inventory_unknown_amount",
                        self.lang,
                        allowed=", ".join(ALLOWED_AMOUNTS),
                    )
                )

            inventory[item_id]["amount"] = amount

        return inventory

    # -------------------------
    # Универсальный публичный API
    # -------------------------

    def sync_template(self, overwrite: bool = False) -> None:
        """
        Создать или обновить файл инвентаря.

        Для cli-режима ничего не делает, потому что cli не хранит файл.
        """
        if self.mode == "yaml":
            self.sync_yaml_template(overwrite=overwrite)
        elif self.mode == "csv":
            self.sync_csv_template(overwrite=overwrite)
        elif self.mode == "cli":
            return

    def load_full_inventory(self) -> dict[str, dict[str, str]]:
        """
        Загрузить полный инвентарь, включая amount: none.
        """
        if self.mode == "yaml":
            self.sync_yaml_template(overwrite=False)
            return self.load_yaml_inventory_full()

        if self.mode == "csv":
            self.sync_csv_template(overwrite=False)
            return self.load_csv_inventory_full()

        if self.mode == "cli":
            return self.ask_cli_inventory_full()

        raise ValueError(f"Неизвестный режим: {self.mode}")

    def load_for_engine(self) -> dict[str, str]:
        """
        Главный метод для RecipeEngine.

        Возвращает только ингредиенты, которые есть,
        плюс системные always_available ингредиенты.
        """
        full_inventory = self.load_full_inventory()
        inventory = self.filter_for_engine(full_inventory)

        return self.add_always_available(inventory)

    def set_amount(self, item_id: str, amount: str) -> None:
        """
        Программно изменить количество одного ингредиента.

        Работает только для yaml/csv.
        Для cli-режима не имеет смысла, потому что там нет файла.
        """
        amount = self.validate_amount(amount)

        if self.mode == "cli":
            raise ValueError("set_amount не используется в cli-режиме.")

        full_inventory = self.load_full_inventory()

        if item_id not in full_inventory:
            full_inventory[item_id] = {
                "name": self.item_name(item_id),
                "amount": "none",
            }

        full_inventory[item_id]["amount"] = amount
        full_inventory[item_id]["name"] = self.item_name(item_id)

        if self.mode == "yaml":
            self.save_yaml_inventory_full(full_inventory)
        elif self.mode == "csv":
            self.save_csv_inventory_full(full_inventory)

    def set_many(self, updates: dict[str, str]) -> None:
        """
        Программно изменить сразу несколько ингредиентов.
        """
        for item_id, amount in updates.items():
            self.set_amount(item_id, amount)

    
    def require_inventory_file(self) -> None:
        """
        Проверить, что файл кладовки существует.

        Нужен для режима suggest, когда пользователь говорит:
        файл уже создан, просто используй его.
        """
        if self.mode == "cli":
            return

        if self.inventory_path is None:
            raise ValueError(
                "Для yaml/csv режима нужен путь к файлу кладовки."
            )

        if not self.inventory_path.exists():
            raise FileNotFoundError(
                f"Файл кладовки не найден: {self.inventory_path}\n"
                f"Сначала создайте его командой:\n"
                f"python main.py init-inventory "
                f"--inventory-mode {self.mode} "
                f"--inventory-path {self.inventory_path}"
            )

    def load_existing_full_inventory(self) -> dict[str, dict[str, str]]:
        """
        Загрузить уже существующий файл кладовки.

        Важно:
        этот метод НЕ создаёт шаблон.
        """
        if self.mode == "yaml":
            self.require_inventory_file()
            return self.load_yaml_inventory_full()

        if self.mode == "csv":
            self.require_inventory_file()
            return self.load_csv_inventory_full()

        if self.mode == "cli":
            return self.ask_cli_inventory_full()

        raise ValueError(f"Неизвестный режим: {self.mode}")

    def load_existing_for_engine(self) -> dict[str, str]:
        """
        Главный метод для режима suggest.

        Читает уже существующий YAML/CSV или спрашивает через CLI.
        Фильтрует amount: none.
        Добавляет системные always_available ингредиенты.
        """
        full_inventory = self.load_existing_full_inventory()
        inventory = self.filter_for_engine(full_inventory)

        return self.add_always_available(inventory)
