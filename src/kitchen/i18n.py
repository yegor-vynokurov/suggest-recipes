from __future__ import annotations

from typing import Literal, cast


Language = Literal["en", "uk"]

DEFAULT_LANG: Language = "en"
SUPPORTED_LANGUAGES: tuple[Language, ...] = ("en", "uk")


CLI_TEXTS: dict[str, dict[Language, str]] = {
    "cli.app_description": {
        "en": "Pick dishes from available ingredients.",
        "uk": "Підбір страв з доступних інгредієнтів.",
    },
    "cli.language_help": {
        "en": "CLI language: en (default) or uk.",
        "uk": "Мова CLI: en (типово) або uk.",
    },
    "cli.found_dishes_title": {
        "en": "Found dishes",
        "uk": "Знайдені страви",
    },
    "cli.comment_label": {
        "en": "Comment",
        "uk": "Коментар",
    },
    "cli.debug_recipe_title": {
        "en": "Recipe breakdown",
        "uk": "Розбір рецепта",
    },
    "cli.debug_ingredients_title": {
        "en": "Ingredients",
        "uk": "Інгредієнти",
    },
    "cli.debug_explanations_title": {
        "en": "Explanations",
        "uk": "Пояснення",
    },
    "cli.none": {
        "en": "none",
        "uk": "немає",
    },
    "cli.file_label": {
        "en": "File",
        "uk": "Файл",
    },
    "cli.id_label": {
        "en": "id",
        "uk": "id",
    },
    "cli.name_label": {
        "en": "name",
        "uk": "назва",
    },
    "cli.mode_label": {
        "en": "Mode",
        "uk": "Режим",
    },
    "cli.status_label": {
        "en": "Status",
        "uk": "Статус",
    },
    "cli.status_short_label": {
        "en": "status",
        "uk": "статус",
    },
    "cli.score_label": {
        "en": "Score",
        "uk": "Оцінка",
    },
    "cli.score_short_label": {
        "en": "score",
        "uk": "оцінка",
    },
    "cli.sources_label": {
        "en": "Sources",
        "uk": "Джерела",
    },
    "cli.cuisines_label": {
        "en": "Cuisines",
        "uk": "Кухні",
    },
    "cli.recipe_count_label": {
        "en": "Recipes",
        "uk": "Рецепти",
    },
    "cli.available_cuisines_title": {
        "en": "Available cuisines",
        "uk": "Доступні кухні",
    },
    "cli.recipe_collection_app_description": {
        "en": "Build data/recipes/read.yaml from recipe files for the selected cuisine.",
        "uk": "Зібрати data/recipes/read.yaml з файлів рецептів для вибраної кухні.",
    },
    "cli.recipe_bundle_built": {
        "en": "Recipe bundle built.",
        "uk": "Пакет рецептів зібрано.",
    },
    "cli.inventory_template_ready": {
        "en": "Inventory template ready.",
        "uk": "Шаблон комори готовий.",
    },
    "cli.inventory_excel_ready": {
        "en": "Inventory Excel template ready.",
        "uk": "Excel-шаблон комори готовий.",
    },
    "cli.inventory_csv_ready": {
        "en": "Inventory CSV ready.",
        "uk": "CSV комори готовий.",
    },
    "cli.open_file_and_fill_amounts": {
        "en": "Open the file, fill in amounts, then run:",
        "uk": "Відкрийте файл, заповніть кількості, потім запустіть:",
    },
    "cli.excel_followup_title": {
        "en": "Next you can run:",
        "uk": "Далі можна запустити:",
    },
    "cli.inventory_edit_title": {
        "en": "Inventory editing",
        "uk": "Редагування комори",
    },
    "cli.accepts_label": {
        "en": "accepts",
        "uk": "допускає",
    },
    "cli.warning_label": {
        "en": "warning",
        "uk": "попередження",
    },
    "cli.note_label": {
        "en": "note",
        "uk": "примітка",
    },
    "cli.inventory_allowed_amounts": {
        "en": "Allowed values: none, spice, little, normal, many",
        "uk": "Дозволені значення: none, spice, little, normal, many",
    },
    "cli.inventory_enter_keeps_none": {
        "en": "Press Enter to keep none",
        "uk": "Натисніть Enter, щоб залишити none",
    },
    "cli.inventory_unknown_amount": {
        "en": "Unknown value. Allowed: {allowed}",
        "uk": "Невідоме значення. Дозволено: {allowed}",
    },
    "cli.openpyxl_required": {
        "en": "Excel commands require the openpyxl package. Install it and try again.",
        "uk": "Для Excel-команд потрібен пакет openpyxl. Встановіть його та спробуйте ще раз.",
    },
    "cli.list_not_found": {
        "en": "No items found.",
        "uk": "Нічого не знайдено.",
    },
    "cli.no_cuisines_found": {
        "en": "No cuisines found.",
        "uk": "Кухні не знайдено.",
    },
    "cli.score_details": {
        "en": "{score} (base={base}, filtered={filtered})",
        "uk": "{score} (база={base}, після фільтрів={filtered})",
    },
    "cli.recipe_not_found": {
        "en": "Recipe with id={recipe_id} was not found in {recipes}.",
        "uk": "Рецепт з id={recipe_id} не знайдено в {recipes}.",
    },
    "cli.saved_amount": {
        "en": "Saved: {item_id} = {amount}",
        "uk": "Збережено: {item_id} = {amount}",
    },
    "cli.recipes_dir_not_found": {
        "en": "Recipes directory was not found: {recipes_dir}",
        "uk": "Теку рецептів не знайдено: {recipes_dir}",
    },
    "cli.no_recipe_files_for_cuisines": {
        "en": "No recipe files were found for selected cuisines: {selected}. Available: {available}",
        "uk": "Не знайдено файлів рецептів для вибраних кухонь: {selected}. Доступно: {available}",
    },
    "cli.recipe_without_id_in_file": {
        "en": "File {file_name} contains a recipe without id.",
        "uk": "У файлі {file_name} є рецепт без id.",
    },
    "cli.duplicate_recipe_ids": {
        "en": "Duplicate recipe.id values in recipe files:\n{text}",
        "uk": "Дублі recipe.id у файлах рецептів:\n{text}",
    },
    "cli.copy_single_requires_one_cuisine": {
        "en": "copy_single_recipe_file works only for one specific cuisine.",
        "uk": "copy_single_recipe_file працює лише для однієї конкретної кухні.",
    },
    "cli.copy_single_expected_one_file": {
        "en": "For cuisine {cuisine} found files: {files}. Use build_recipe_bundle.",
        "uk": "Для кухні {cuisine} знайдено файли: {files}. Використовуйте build_recipe_bundle.",
    },
    "cli.help.recipes": {
        "en": "Path to the YAML file with recipes.",
        "uk": "Шлях до YAML-файлу з рецептами.",
    },
    "cli.help.inventory_mode": {
        "en": "Inventory input mode: yaml, csv or cli.",
        "uk": "Режим введення комори: yaml, csv або cli.",
    },
    "cli.help.inventory_path": {
        "en": "Path to the inventory file for yaml/csv mode.",
        "uk": "Шлях до файлу комори для режиму yaml/csv.",
    },
    "cli.help.init_inventory_command": {
        "en": "Create or update the inventory template.",
        "uk": "Створити або оновити шаблон комори.",
    },
    "cli.help.overwrite": {
        "en": "Reset all amounts to none.",
        "uk": "Скинути всі кількості в none.",
    },
    "cli.help.inspect_ingredients_command": {
        "en": "Show recipe ingredients that are missing from the YAML catalog.",
        "uk": "Показати інгредієнти з рецептів, яких немає в YAML-каталозі.",
    },
    "cli.help.merged_ingredients": {
        "en": "Path to ingredients_all_merged.yaml.",
        "uk": "Шлях до ingredients_all_merged.yaml.",
    },
    "cli.help.no_accepts": {
        "en": "Do not include item_id values from accepts.",
        "uk": "Не враховувати item_id з accepts.",
    },
    "cli.help.write_drafts": {
        "en": "Create draft YAML files with suggestions.",
        "uk": "Створити draft YAML-файли з пропозиціями.",
    },
    "cli.help.draft_dir": {
        "en": "Directory for draft YAML files.",
        "uk": "Тека для draft YAML-файлів.",
    },
    "cli.help.merge_drafts_command": {
        "en": "Move reviewed draft YAML files into working ingredients YAML files.",
        "uk": "Перенести перевірені draft YAML-файли в робочі ingredients YAML.",
    },
    "cli.help.merge_drafts_draft_dir": {
        "en": "Directory with _draft_*.yaml files.",
        "uk": "Тека з файлами _draft_*.yaml.",
    },
    "cli.help.merge_drafts_ingredients_dir": {
        "en": "Directory with working ingredients_*.yaml files.",
        "uk": "Тека з робочими файлами ingredients_*.yaml.",
    },
    "cli.help.merge_drafts_merged_ingredients": {
        "en": "Where to rebuild the merged ingredients YAML.",
        "uk": "Куди пересобрати merged ingredients YAML.",
    },
    "cli.help.keep_drafts": {
        "en": "Do not delete draft files after a successful merge.",
        "uk": "Не видаляти draft-файли після успішного merge.",
    },
    "cli.help.init_inventory_excel_command": {
        "en": "Create an Excel inventory template by ingredient groups.",
        "uk": "Створити Excel-шаблон комори за групами інгредієнтів.",
    },
    "cli.help.ingredients_dir": {
        "en": "Directory with ingredients_*.yaml files.",
        "uk": "Тека з файлами ingredients_*.yaml.",
    },
    "cli.help.audit_localization": {
        "en": "Audit source ingredient YAML files for missing name_uk and legacy localized fields.",
        "uk": "Перевірити source ingredients YAML на відсутній name_uk і застарілі локалізовані поля.",
    },
    "cli.help.inventory_xlsx_output": {
        "en": "Where to save the inventory Excel file.",
        "uk": "Куди зберегти Excel-файл комори.",
    },
    "cli.help.existing_csv": {
        "en": "Existing current_inventory.<lang>.csv to preserve already filled amounts.",
        "uk": "Наявний current_inventory.<lang>.csv, щоб зберегти вже заповнені кількості.",
    },
    "cli.help.inventory_excel_to_csv_command": {
        "en": "Convert inventory Excel files into current_inventory.<lang>.csv files.",
        "uk": "Перетворити Excel-файли комори на current_inventory.<lang>.csv.",
    },
    "cli.help.inventory_xlsx_input": {
        "en": "Filled inventory Excel file. If omitted, exports all existing language-specific Excel files.",
        "uk": "Заповнений Excel-файл комори. Якщо не вказано, експортує всі наявні мовні Excel-файли.",
    },
    "cli.help.inventory_csv_output": {
        "en": "Where to save current_inventory.<lang>.csv.",
        "uk": "Куди зберегти current_inventory.<lang>.csv.",
    },
    "cli.help.only_existing": {
        "en": "Write only rows where amount != none.",
        "uk": "Записати лише рядки, де amount != none.",
    },
    "cli.help.build_recipes_command": {
        "en": "Build the shared data/recipes/read.yaml bundle for the selected cuisine.",
        "uk": "Зібрати спільний data/recipes/read.yaml для вибраної кухні.",
    },
    "cli.help.cuisines_option": {
        "en": "all, turkish, indian, ukrainian or a comma-separated list like turkish,indian",
        "uk": "all, turkish, indian, ukrainian або список через кому, наприклад turkish,indian",
    },
    "cli.help.recipes_dir": {
        "en": "Directory with recipe_templates_*.yaml files.",
        "uk": "Тека з файлами recipe_templates_*.yaml.",
    },
    "cli.help.output": {
        "en": "Where to save the shared recipe bundle.",
        "uk": "Куди зберегти спільний файл рецептів.",
    },
    "cli.help.no_pantry": {
        "en": "Do not include pantry recipes when a specific cuisine is selected.",
        "uk": "Не додавати pantry-рецепти, коли вибрано конкретну кухню.",
    },
    "cli.help.allow_duplicate_ids": {
        "en": "Do not fail on duplicate recipe.id values; skip duplicates instead.",
        "uk": "Не падати на дублікатах recipe.id, а пропускати повтори.",
    },
    "cli.help.list_cuisines_command": {
        "en": "Show cuisines available in data/recipes.",
        "uk": "Показати кухні, доступні в data/recipes.",
    },
    "cli.help.suggest_command": {
        "en": "Suggest dishes from an already filled inventory.",
        "uk": "Підібрати страви за вже заповненою коморою.",
    },
    "cli.help.limit": {
        "en": "How many dishes to show in each group.",
        "uk": "Скільки страв показувати в кожній групі.",
    },
    "cli.help.filters": {
        "en": "Ranking filters: legume, up_to_half_hour, mediterranean, salad, soup and so on.",
        "uk": "Фільтри ранжування: legume, up_to_half_hour, mediterranean, salad, soup тощо.",
    },
    "cli.help.prefer_category": {
        "en": "Preferred ingredient categories: meat, fish, legume, mushroom, grain, dairy and so on.",
        "uk": "Бажані категорії інгредієнтів: meat, fish, legume, mushroom, grain, dairy тощо.",
    },
    "cli.help.randomize": {
        "en": "Slightly shuffle results inside groups.",
        "uk": "Злегка перемішувати результати всередині груп.",
    },
    "cli.help.random_strength": {
        "en": "Shuffle strength. Examples: 0.03, 0.06, 0.10.",
        "uk": "Сила перемішування. Наприклад: 0.03, 0.06, 0.10.",
    },
    "cli.help.seed": {
        "en": "Seed for reproducible shuffling.",
        "uk": "Seed для відтворюваного перемішування.",
    },
    "cli.help.suggest_cuisines": {
        "en": "Before suggest, rebuild read.yaml for cuisine: all, ukrainian, turkish, indian or a list.",
        "uk": "Перед suggest пересобрати read.yaml для кухні: all, ukrainian, turkish, indian або списку.",
    },
    "cli.help.debug_match_command": {
        "en": "Show a detailed breakdown for a single recipe match.",
        "uk": "Показати детальний розбір підбору одного рецепта.",
    },
    "cli.help.recipe_id": {
        "en": "Recipe ID, for example french_mayonnaise_maison.",
        "uk": "ID рецепта, наприклад french_mayonnaise_maison.",
    },
    "cli.help.debug_cuisines": {
        "en": "Before debug-match, rebuild read.yaml for cuisine: all, ukrainian, turkish, indian or a list.",
        "uk": "Перед debug-match пересобрати read.yaml для кухні: all, ukrainian, turkish, indian або списку.",
    },
    "cli.help.set_command": {
        "en": "Change the amount for one ingredient.",
        "uk": "Змінити кількість одного інгредієнта.",
    },
    "cli.help.item_id": {
        "en": "Ingredient ID, for example beans or eggs.",
        "uk": "ID інгредієнта, наприклад beans або eggs.",
    },
    "cli.help.amount": {
        "en": "Ingredient amount.",
        "uk": "Кількість інгредієнта.",
    },
}


EXCEL_TEXTS: dict[str, dict[Language, str]] = {
    "excel.message.inventory_excel_ready": {
        "en": "Inventory Excel template ready",
        "uk": "Excel-шаблон комори готовий",
    },
    "excel.message.product_sheet_count": {
        "en": "Product sheets",
        "uk": "Аркушів із продуктами",
    },
    "excel.message.manual_fill_ingredient_count": {
        "en": "Ingredients to fill in manually",
        "uk": "Інгредієнтів для ручного заповнення",
    },
    "excel.message.inventory_csv_ready": {
        "en": "Inventory CSV ready",
        "uk": "CSV комори готовий",
    },
    "excel.message.rows_written": {
        "en": "Rows written",
        "uk": "Рядків записано",
    },
    "excel.error.ingredients_dir_not_found": {
        "en": "Ingredients directory was not found: {path}",
        "uk": "Теку з інгредієнтами не знайдено: {path}",
    },
    "excel.error.no_visible_ingredients": {
        "en": "No visible ingredients were found for the Excel template in {path}.",
        "uk": "У теці {path} не знайдено видимих інгредієнтів для Excel-шаблону.",
    },
    "excel.error.inventory_excel_not_found": {
        "en": "Inventory Excel file was not found: {path}",
        "uk": "Excel-файл комори не знайдено: {path}",
    },
    "excel.error.no_inventory_excels_found": {
        "en": "No inventory Excel files were found. Checked: {checked}",
        "uk": "Не знайдено Excel-файлів комори. Перевірено: {checked}",
    },
    "excel.sheet.readme": {
        "en": "README",
        "uk": "Інструкція",
    },
    "excel.domain.ingredients_meat_poultry": {
        "en": "Meat_Poultry",
        "uk": "М'ясо_птиця",
    },
    "excel.domain.ingredients_fish_seafood": {
        "en": "Fish_Seafood",
        "uk": "Риба_морепродукти",
    },
    "excel.domain.ingredients_dairy_eggs": {
        "en": "Dairy_Eggs",
        "uk": "Молочне_яйця",
    },
    "excel.domain.ingredients_legumes": {
        "en": "Legumes",
        "uk": "Бобові",
    },
    "excel.domain.ingredients_grains_bread": {
        "en": "Grains_Bread",
        "uk": "Крупи_хліб",
    },
    "excel.domain.ingredients_vegetables_mushrooms_fruits": {
        "en": "Vegetables_Mushrooms_Fruits",
        "uk": "Овочі_гриби_фрукти",
    },
    "excel.domain.ingredients_fats_oils": {
        "en": "Fats_Oils",
        "uk": "Жири_олії",
    },
    "excel.domain.ingredients_nuts_seeds_sweeteners": {
        "en": "Nuts_Seeds_Sweets",
        "uk": "Горіхи_насіння_солодке",
    },
    "excel.domain.ingredients_sauces_condiments": {
        "en": "Sauces_Condiments",
        "uk": "Соуси_приправи",
    },
    "excel.domain.ingredients_spices_herbs": {
        "en": "Spices_Herbs",
        "uk": "Спеції_трави",
    },
    "excel.domain.ingredients_technical": {
        "en": "Technical",
        "uk": "Технічне",
    },
    "excel.domain.ingredients_prepared_components": {
        "en": "Prepared_Components",
        "uk": "Готові_компоненти",
    },
    "excel.header.amount": {
        "en": "amount",
        "uk": "кількість",
    },
    "excel.header.item_id": {
        "en": "item_id",
        "uk": "item_id",
    },
    "excel.header.name": {
        "en": "name",
        "uk": "назва",
    },
    "excel.header.groups": {
        "en": "groups",
        "uk": "групи",
    },
    "excel.header.aliases": {
        "en": "aliases",
        "uk": "аліаси",
    },
    "excel.header.source_file": {
        "en": "source_file",
        "uk": "джерело",
    },
    "excel.header.review": {
        "en": "review",
        "uk": "перевірити",
    },
    "excel.header.comment": {
        "en": "comment",
        "uk": "коментар",
    },
    "excel.readme.title": {
        "en": "Inventory template",
        "uk": "Шаблон комори",
    },
    "excel.readme.line_1": {
        "en": "1. Fill the amount column with one of: none, spice, little, normal, many.",
        "uk": "1. Заповніть колонку amount одним зі значень: none, spice, little, normal, many.",
    },
    "excel.readme.line_2": {
        "en": "2. Name, groups, aliases, source_file and comment are reference columns.",
        "uk": "2. Колонки name, groups, aliases, source_file та comment є довідковими.",
    },
    "excel.readme.line_3": {
        "en": "3. Do not change item_id: the program uses it to identify the ingredient.",
        "uk": "3. Не змінюйте item_id: програма використовує його для визначення інгредієнта.",
    },
    "excel.readme.line_4": {
        "en": "4. Water and abstract categories are hidden and added by the program automatically.",
        "uk": "4. Вода й абстрактні категорії приховані та додаються програмою автоматично.",
    },
    "excel.readme.amount_values_title": {
        "en": "Amount values:",
        "uk": "Значення amount:",
    },
    "excel.validation.amount_error": {
        "en": "Choose one of: none, spice, little, normal, many.",
        "uk": "Оберіть одне зі значень: none, spice, little, normal, many.",
    },
    "excel.validation.amount_error_title": {
        "en": "Invalid amount",
        "uk": "Некоректна кількість",
    },
    "excel.validation.amount_prompt": {
        "en": "none = absent; spice = spice-level; little = little; normal = normal; many = many",
        "uk": "none = немає; spice = як спеція; little = мало; normal = нормально; many = багато",
    },
    "excel.validation.amount_prompt_title": {
        "en": "Amount",
        "uk": "Кількість",
    },
}


RECIPE_EXPLANATION_TEXTS: dict[str, dict[Language, str]] = {
    "recipe.status.can_cook": {
        "en": "can cook",
        "uk": "можна готувати",
    },
    "recipe.status.variant": {
        "en": "variant",
        "uk": "варіант",
    },
    "recipe.status.missing_one": {
        "en": "missing one",
        "uk": "бракує одного",
    },
    "recipe.status.missing_main": {
        "en": "missing main",
        "uk": "бракує основного",
    },
    "recipe.status.far": {
        "en": "far",
        "uk": "далеко",
    },
    "recipe.explanation.missing": {
        "en": "missing: {name}",
        "uk": "не вистачає: {name}",
    },
    "recipe.explanation.category_substitution": {
        "en": "{required} substituted by category: {used}",
        "uk": "{required} замінено категорією: {used}",
    },
    "recipe.explanation.accepted_item_substitution": {
        "en": "{required} substituted by accepted item: {used}",
        "uk": "{required} замінено допустимим інгредієнтом: {used}",
    },
    "recipe.explanation.parent_category_substitution": {
        "en": "{required} substituted via parent category: {used}",
        "uk": "{required} замінено через батьківську категорію: {used}",
    },
    "recipe.explanation.direct_match": {
        "en": "{required} matched directly: {used}",
        "uk": "{required} збігся напряму: {used}",
    },
    "recipe.explanation.quantity_warning": {
        "en": "have {name}, but too little",
        "uk": "є {name}, але замало",
    },
    "recipe.explanation.comment_label": {
        "en": "Comment: {comment}",
        "uk": "Коментар: {comment}",
    },
    "recipe.explanation.filter_match": {
        "en": "matches filter: {filter}={value}",
        "uk": "підходить під фільтр: {filter}={value}",
    },
    "recipe.explanation.filter_penalty": {
        "en": "filter penalty: {filter}={value}",
        "uk": "штраф за фільтр: {filter}={value}",
    },
    "recipe.explanation.preference_bonus": {
        "en": "bonus for preferred category: {category}",
        "uk": "бонус за бажану категорію: {category}",
    },
}


TRANSLATIONS: dict[str, dict[Language, str]] = (
    CLI_TEXTS
    | EXCEL_TEXTS
    | RECIPE_EXPLANATION_TEXTS
)


class _SafeFormatDict(dict[str, object]):
    def __missing__(self, key: str) -> str:
        return "{" + key + "}"


def normalize_language(lang: str | None) -> Language:
    if not lang:
        return DEFAULT_LANG

    candidate = lang.strip().lower()
    if candidate in SUPPORTED_LANGUAGES:
        return cast(Language, candidate)

    return DEFAULT_LANG


def t(key: str, lang: str | None = DEFAULT_LANG, **kwargs: object) -> str:
    translations = TRANSLATIONS.get(key)
    if translations is None:
        return key

    normalized_lang = normalize_language(lang)
    template = translations.get(normalized_lang) or translations.get(DEFAULT_LANG) or key
    return template.format_map(_SafeFormatDict(kwargs))


__all__ = [
    "CLI_TEXTS",
    "DEFAULT_LANG",
    "EXCEL_TEXTS",
    "Language",
    "RECIPE_EXPLANATION_TEXTS",
    "SUPPORTED_LANGUAGES",
    "TRANSLATIONS",
    "normalize_language",
    "t",
]
