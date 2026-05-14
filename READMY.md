# Recipe Picker

## English

### What this project does

This project helps you find possible dishes from the ingredients you have.

The goal is not to give a full cooking lesson.
The goal is to show:

- dish name
- main ingredients
- simple ingredient amounts: `spice`, `little`, `normal`, `many`
- a score and short notes

### Important note

Short, general, and not very detailed recipes in the output are **not a bug**.
This is a **feature**.

Why:

- recipes change from region to region
- recipes change from family to family
- recipes change from person to person

So the project gives the dish name and the main ingredient set.
Then you can search the full recipe on the internet by the dish name.

### Language

- English is the default CLI language.
- Use `--lang uk` for Ukrainian CLI messages.
- Excel files also use the selected language:
  - English: `current_inventory.en.xlsx`
  - Ukrainian: `current_inventory.uk.xlsx`

### Quick start

1. See available cuisines:

```bash
python main.py list-cuisines
```

2. Create an Excel inventory file:

```bash
python main.py init-inventory-excel
```

3. Or create the Ukrainian Excel file:

```bash
python main.py init-inventory-excel --lang uk
```

4. Open the Excel file and fill the `amount` column.

5. Convert Excel to CSV:

```bash
python main.py inventory-excel-to-csv
```

6. Get dish suggestions:

```bash
python main.py suggest --inventory-mode csv
```

7. Get Ukrainian CLI output:

```bash
python main.py suggest --inventory-mode csv --lang uk
```

### Simple examples

Only soups:

```bash
python main.py suggest --inventory-mode csv --filters soup
```

Only main dishes:

```bash
python main.py suggest --inventory-mode csv --filters main
```

Only salads:

```bash
python main.py suggest --inventory-mode csv --filters salad
```

Quick dishes, under 30 minutes:

```bash
python main.py suggest --inventory-mode csv --filters under_30
```

Very quick dishes, under 10 minutes:

```bash
python main.py suggest --inventory-mode csv --filters under_10
```

Soups under 30 minutes:

```bash
python main.py suggest --inventory-mode csv --filters soup under_30
```

Main dishes under 30 minutes:

```bash
python main.py suggest --inventory-mode csv --filters main under_30
```

Prefer meat and mushrooms:

```bash
python main.py suggest --inventory-mode csv --prefer-category meat mushroom
```

Use only some cuisines:

```bash
python main.py suggest --inventory-mode csv --cuisine ukrainian
python main.py suggest --inventory-mode csv --cuisine scandinavian
python main.py suggest --inventory-mode csv --cuisine ukrainian,turkish,indian
```

Small random mix in results:

```bash
python main.py suggest --inventory-mode csv --randomize
python main.py suggest --inventory-mode csv --randomize --random-strength 0.10
```

Ukrainian CLI output with filters:

```bash
python main.py suggest --inventory-mode csv --lang uk --filters soup under_30
```

### Other inventory modes

YAML inventory:

```bash
python main.py init-inventory --inventory-mode yaml
python main.py suggest --inventory-mode yaml
```

Quick interactive mode in terminal:

```bash
python main.py suggest --inventory-mode cli
```

Set one ingredient from CLI:

```bash
python main.py set eggs normal --inventory-mode csv
```

### Debug one recipe

If one match looks strange, inspect one recipe:

```bash
python main.py debug-match ukrainian_deruny --inventory-mode csv
```

### Work with recipe bundle

Usually you do not need this step for daily use.
It is useful when you change recipe templates.

Build the shared bundle:

```bash
python main.py build-recipes --cuisine all
```

Build only some cuisines:

```bash
python main.py build-recipes --cuisine ukrainian,turkish
```

### Work with ingredient catalog

Find missing ingredient ids:

```bash
python main.py inspect-ingredients
```

Create draft ingredient files from one recipe source:

```bash
python main.py inspect-ingredients --recipes data/recipes/recipe_templates_scandinavian_v0_1.yaml --write-drafts
```

Merge reviewed draft files:

```bash
python main.py merge-ingredient-drafts
```

---

## Українська

### Що робить цей проєкт

Цей проєкт допомагає знайти можливі страви з тих продуктів, які у вас є.

Мета не в тому, щоб дати повний кулінарний урок.
Мета в тому, щоб показати:

- назву страви
- основні інгредієнти
- прості кількості: `spice`, `little`, `normal`, `many`
- оцінку і короткі пояснення

### Важлива примітка

Короткі, загальні і не дуже детальні рецепти у видачі — **це не баг**.
Це **фіча**.

Чому:

- рецепти різняться від регіону до регіону
- рецепти різняться від родини до родини
- рецепти різняться від людини до людини

Тому проєкт дає назву страви і основний набір інгредієнтів.
Потім повний рецепт можна знайти в інтернеті за назвою страви.

### Мова

- Англійська — типова мова CLI.
- Використовуйте `--lang uk` для українських повідомлень CLI.
- Excel-файли теж залежать від мови:
  - англійський: `current_inventory.en.xlsx`
  - український: `current_inventory.uk.xlsx`

### Швидкий старт

1. Подивитися доступні кухні:

```bash
python main.py list-cuisines
```

2. Створити Excel-файл комори:

```bash
python main.py init-inventory-excel
```

3. Або створити український Excel-файл:

```bash
python main.py init-inventory-excel --lang uk
```

4. Відкрити Excel-файл і заповнити колонку `amount`.

5. Перетворити Excel у CSV:

```bash
python main.py inventory-excel-to-csv
```

6. Отримати підбір страв:

```bash
python main.py suggest --inventory-mode csv
```

7. Отримати українські повідомлення CLI:

```bash
python main.py suggest --inventory-mode csv --lang uk
```

### Прості приклади

Тільки супи:

```bash
python main.py suggest --inventory-mode csv --filters soup
```

Тільки основні страви:

```bash
python main.py suggest --inventory-mode csv --filters main
```

Тільки салати:

```bash
python main.py suggest --inventory-mode csv --filters salad
```

Швидкі страви, до 30 хвилин:

```bash
python main.py suggest --inventory-mode csv --filters under_30
```

Дуже швидкі страви, до 10 хвилин:

```bash
python main.py suggest --inventory-mode csv --filters under_10
```

Супи до 30 хвилин:

```bash
python main.py suggest --inventory-mode csv --filters soup under_30
```

Основні страви до 30 хвилин:

```bash
python main.py suggest --inventory-mode csv --filters main under_30
```

Бажано м'ясо і гриби:

```bash
python main.py suggest --inventory-mode csv --prefer-category meat mushroom
```

Тільки деякі кухні:

```bash
python main.py suggest --inventory-mode csv --cuisine ukrainian
python main.py suggest --inventory-mode csv --cuisine scandinavian
python main.py suggest --inventory-mode csv --cuisine ukrainian,turkish,indian
```

Трохи випадковості у видачі:

```bash
python main.py suggest --inventory-mode csv --randomize
python main.py suggest --inventory-mode csv --randomize --random-strength 0.10
```

Українські повідомлення CLI з фільтрами:

```bash
python main.py suggest --inventory-mode csv --lang uk --filters soup under_30
```

### Інші режими комори

YAML-комора:

```bash
python main.py init-inventory --inventory-mode yaml
python main.py suggest --inventory-mode yaml
```

Швидкий інтерактивний режим у терміналі:

```bash
python main.py suggest --inventory-mode cli
```

Змінити один інгредієнт з CLI:

```bash
python main.py set eggs normal --inventory-mode csv
```

### Перевірити один рецепт

Якщо один матч виглядає дивно, подивіться детальний розбір:

```bash
python main.py debug-match ukrainian_deruny --inventory-mode csv
```

### Робота з recipe bundle

Зазвичай цей крок не потрібний для щоденного використання.
Він корисний, коли ви змінюєте шаблони рецептів.

Зібрати спільний bundle:

```bash
python main.py build-recipes --cuisine all
```

Зібрати тільки деякі кухні:

```bash
python main.py build-recipes --cuisine ukrainian,turkish
```

### Робота з каталогом інгредієнтів

Знайти відсутні `item_id`:

```bash
python main.py inspect-ingredients
```

Створити draft-файли інгредієнтів з одного джерела рецептів:

```bash
python main.py inspect-ingredients --recipes data/recipes/recipe_templates_scandinavian_v0_1.yaml --write-drafts
```

Об'єднати перевірені draft-файли:

```bash
python main.py merge-ingredient-drafts
```
