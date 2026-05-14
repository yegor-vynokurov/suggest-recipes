# ingredients_yaml_v0_1

Это разнесённая по YAML версия ингредиентных констант.

## Основные файлы

- `ingredient_categories.yaml` — дерево/граф категорий.
- `ingredients_*.yaml` — отдельные группы ингредиентов.
- `ingredients_all_merged.yaml` — слитый файл для программы.
- `merge_ingredients.py` — пересобирает merged-файл.
- `ingredient_loader.py` — пример, как получить `ITEM_NAMES`, `INGREDIENT_GROUPS`, `ALWAYS_AVAILABLE_INVENTORY`.

## Вода

`water` считается всегда доступной:

```yaml
water:
  inventory:
    track: false
    always_available: true
    default_amount: many
    hide_from_template: true
```

Поэтому её не нужно показывать в CSV-шаблоне, но нужно добавлять в inventory перед запуском RecipeEngine.

## Специи

Специи разделены на:
- `hot_spice`
- `chili_spice`
- `pungent_spice`
- `mild_spice`
- `warm_spice`
- `earthy_spice`
- `seed_spice`
- `color_spice`
- `aromatic_spice`
- `masala_mix`
- `herb`
- `acid_souring`

Один ингредиент может быть в нескольких группах.
