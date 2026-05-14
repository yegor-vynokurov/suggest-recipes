from __future__ import annotations

from src.kitchen.constants import ING_PATH
from src.kitchen.parse_recipes import load_recipes_from_yaml


def test_runtime_reads_localized_recipe_bundle() -> None:
    recipes = load_recipes_from_yaml(str(ING_PATH))
    recipes_by_id = {recipe.id: recipe for recipe in recipes}

    cesnecka = recipes_by_id["czech_cesnecka"]
    kholodets = recipes_by_id["ukrainian_kholodets_pork_rich"]
    raspeballer = recipes_by_id["scandinavian_raspeballer"]

    assert cesnecka.name == "Czech garlic soup"
    assert cesnecka.name_uk == "Чеський часниковий суп"

    assert kholodets.name == "Jellied meat with pork legs, ears and tails"
    assert kholodets.name_uk == "Холодець зі свинячими ніжками, вухами і хвостами"
    assert kholodets.comment == (
        "Gelatin-rich pork cuts are essential for this dish; water is a system ingredient, "
        "but it should stay in the recipe."
    )
    assert kholodets.comment_uk == (
        "Желатинові частини свинини є ключовими для цієї страви; вода системна, "
        "але має залишатися в рецепті."
    )

    assert raspeballer.name == "Norwegian potato dumplings"
    assert raspeballer.name_uk == "Норвезькі картопляні галушки"
