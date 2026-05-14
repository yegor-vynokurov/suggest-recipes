import yaml
from collections import defaultdict
from constants import ING_PATH
from utils import load_yaml
import constants as cnst



def collect_ingredient_ids(path: str, include_accepts: bool = True) -> list[str]:
    data = load_yaml(path)

    ingredient_ids = set()

    for recipe in data.get("recipes", []):
        for ingredient in recipe.get("ingredients", []):
            item_id = ingredient.get("item")

            if item_id:
                ingredient_ids.add(item_id)

            if include_accepts:
                for accepted_id in ingredient.get("accepts", []):
                    ingredient_ids.add(accepted_id)
    ingredient_ids -= cnst.HIDDEN_FROM_INVENTORY_TEMPLATE
    return sorted(ingredient_ids)


# def build_ingredient_usage(path: str, include_accepts: bool = True) -> dict[str, list[str]]:
#     data = load_yaml(path)

#     usage = defaultdict(list)

#     for recipe in data.get("recipes", []):
#         recipe_id = recipe.get("id")
#         recipe_name = recipe.get("name", recipe_id)

#         for ingredient in recipe.get("ingredients", []):
#             item_id = ingredient.get("item")

#             if item_id:
#                 usage[item_id].append(recipe_name)

#             if include_accepts:
#                 for accepted_id in ingredient.get("accepts", []):
#                     usage[accepted_id].append(f"{recipe_name} / как замена")

#     return dict(usage)


if __name__ == "__main__":
    # path = "recipe_templates_pantry_v0_1.yaml"

    ingredient_ids = collect_ingredient_ids(ING_PATH)

    print("ВСЕ ИНГРЕДИЕНТЫ:")
    print("-" * 40)

    for ingredient_id in ingredient_ids:
        print(ingredient_id)

    print()
    print(f"Всего ингредиентов: {len(ingredient_ids)}")

    # build_ingredient_usage(path = ING_PATH)