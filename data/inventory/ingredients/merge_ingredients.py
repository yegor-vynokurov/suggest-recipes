from pathlib import Path
import yaml

BASE = Path(__file__).resolve().parent
ing_path = 'data/inventory'
# OUT = BASE / ing_path / "ingredients_all_merged.yaml"
OUT = BASE / "ingredients_all_merged.yaml"

def load_yaml(path):
    with path.open("r", encoding="utf-8") as file:
        return yaml.safe_load(file) or {}

def main():
    categories = load_yaml(BASE / "ingredient_categories.yaml").get("categories", {})
    ingredients = {}
    for path in sorted(BASE.glob("ingredients_*.yaml")):
        if path.name == "ingredients_all_merged.yaml":
            continue
        data = load_yaml(path)
        for item_id, item in data.get("ingredients", {}).items():
            if item_id in ingredients:
                raise ValueError(f"Duplicate ingredient id: {item_id} in {path.name}")
            ingredients[item_id] = item
    merged = {"metadata": {"version": "0.1", "kind": "merged_ingredients"}, "categories": categories, "ingredients": dict(sorted(ingredients.items()))}
    with OUT.open("w", encoding="utf-8") as file:
        yaml.safe_dump(merged, file, allow_unicode=True, sort_keys=False, width=120)
    print(f"Saved {OUT}")
    print(f"categories: {len(categories)}")
    print(f"ingredients: {len(ingredients)}")

if __name__ == "__main__":
    main()
