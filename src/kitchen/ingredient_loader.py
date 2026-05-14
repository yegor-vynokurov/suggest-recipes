from pathlib import Path
import yaml

def load_ingredient_yaml(path):
    path = Path(path)
    with path.open("r", encoding="utf-8") as file:
        return yaml.safe_load(file) or {}

def build_constants_from_ingredients(data):
    ingredients = data.get("ingredients", {})
    categories = data.get("categories", {})

    item_names = {item_id: item.get("name", item_id) for item_id, item in ingredients.items()}

    ingredient_groups = {}
    for item_id, item in ingredients.items():
        for group_id in item.get("groups", []):
            ingredient_groups.setdefault(group_id, []).append(item_id)
    ingredient_groups = {k: sorted(set(v)) for k, v in ingredient_groups.items()}

    abstract_ingredients = {
        item_id for item_id, item in ingredients.items()
        if item.get("abstract") or item.get("inventory", {}).get("hide_from_template")
    }

    always_available_inventory = {
        item_id: item.get("inventory", {}).get("default_amount", "many")
        for item_id, item in ingredients.items()
        if item.get("inventory", {}).get("always_available")
    }

    hidden_from_inventory_template = {
        item_id for item_id, item in ingredients.items()
        if item.get("inventory", {}).get("hide_from_template")
    }

    return {
        "CATEGORIES": categories,
        "INGREDIENTS": ingredients,
        "ITEM_NAMES": item_names,
        "INGREDIENT_GROUPS": ingredient_groups,
        "ABSTRACT_INGREDIENTS": abstract_ingredients,
        "ALWAYS_AVAILABLE_INVENTORY": always_available_inventory,
        "HIDDEN_FROM_INVENTORY_TEMPLATE": hidden_from_inventory_template,
    }

if __name__ == "__main__":
    data = load_ingredient_yaml("data/inventory/ingredients/ingredients_all_merged.yaml")
    constants = build_constants_from_ingredients(data)
    for key, value in constants.items():
        print(key, len(value) if hasattr(value, "__len__") else value)
    print("ALWAYS_AVAILABLE_INVENTORY:", constants["ALWAYS_AVAILABLE_INVENTORY"])
