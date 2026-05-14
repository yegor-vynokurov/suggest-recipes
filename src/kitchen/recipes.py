import src.kitchen.constants as cnst
from src.kitchen.construct import Recipe, Need

RECIPES = [
    Recipe(
        id="fried_eggs",
        name="Яичница",
        ingredients=[
            Need("eggs", "main", "normal"),
            Need("butter", "required", "little", accepts=["smalec"]),
            Need("black_pepper", "spice", "spice"),
        ],
    ),

    Recipe(
        id="omelette",
        name="Омлет",
        ingredients=[
            Need("eggs", "main", "normal"),
            Need("milk", "required", "little"),
            Need("butter", "required", "little", accepts=["smalec"]),
            Need("black_pepper", "spice", "spice"),
        ],
    ),

    Recipe(
        id="omelette_with_cheese",
        name="Омлет с сыром",
        ingredients=[
            Need("eggs", "main", "normal"),
            Need("milk", "required", "little"),
            Need("hard_cheese", "addition", "little"),
            Need("butter", "required", "little", accepts=["smalec"]),
        ],
    ),

    Recipe(
        id="fried_eggs_with_sausage",
        name="Яичница с варёной колбасой",
        ingredients=[
            Need("eggs", "main", "normal"),
            Need("boiled_sausage", "addition", "little"),
            Need("butter", "required", "little", accepts=["smalec"]),
        ],
    ),

    Recipe(
        id="fried_eggs_with_zeltz",
        name="Яичница с зельцем",
        ingredients=[
            Need("eggs", "main", "normal"),
            Need("zeltz", "addition", "little"),
            Need("butter", "required", "little", accepts=["smalec"]),
        ],
    ),

    Recipe(
        id="cabbage_pea_salad",
        name="Салат: молодая капуста, зелень, горошек, сметана",
        ingredients=[
            Need("young_cabbage", "main", "normal"),
            Need("canned_peas", "required", "normal"),
            Need("sour_cream", "required", "little"),
            Need("greens", "addition", "little"),
            Need("black_pepper", "spice", "spice"),
        ],
    ),

    Recipe(
        id="pelmeni_sour_cream",
        name="Пельмени со сметаной",
        ingredients=[
            Need("pelmeni", "main", "normal"),
            Need("sour_cream", "required", "little"),
            Need("butter", "addition", "little"),
        ],
    ),

    Recipe(
        id="vareniki_sour_cream",
        name="Вареники со сметаной",
        ingredients=[
            Need("vareniki", "main", "normal"),
            Need("sour_cream", "required", "little"),
            Need("butter", "addition", "little"),
        ],
    ),

    Recipe(
        id="fried_chicken_fillet",
        name="Жареное куриное филе",
        ingredients=[
            Need("chicken_fillet", "main", "normal"),
            Need("butter", "required", "little", accepts=["smalec"]),
            Need("dry_garlic", "spice", "spice"),
            Need("black_pepper", "spice", "spice"),
        ],
    ),

    Recipe(
        id="boiled_buckwheat",
        name="Гречка варёная",
        ingredients=[
            Need("buckwheat", "main", "normal"),
            Need("butter", "addition", "little"),
        ],
    ),

    Recipe(
        id="buckwheat_with_milk",
        name="Гречка с молоком",
        ingredients=[
            Need("buckwheat", "main", "normal"),
            Need("milk", "required", "little"),
        ],
    ),

    Recipe(
        id="boiled_rice",
        name="Рис варёный",
        ingredients=[
            Need("rice", "main", "normal"),
            Need("butter", "addition", "little"),
        ],
        comment="Риса немного, поэтому получится небольшая порция.",
    ),

    Recipe(
        id="rice_with_boiled_egg",
        name="Рис с варёным яйцом",
        ingredients=[
            Need("rice", "main", "normal"),
            Need("eggs", "required", "little"),
            Need("butter", "addition", "little"),
        ],
        comment="Риса немного, но как маленькое блюдо подходит.",
    ),

    Recipe(
        id="simple_plov_chicken",
        name="Плов с курицей",
        ingredients=[
            Need("rice", "main", "many"),
            Need("lamb", "main", "normal", accepts=["chicken_fillet", "stew"]),
            Need("carrot", "required", "normal"),
            Need("onion", "required", "normal"),
            Need("smalec", "required", "little", accepts=["butter"]),
            Need("dry_garlic", "spice", "spice"),
            Need("black_pepper", "spice", "spice"),
        ],
        comment="Сейчас это скорее маленький плов или рис с курицей в стиле плова: риса и моркови немного.",
    ),

    Recipe(
        id="lentils_with_additions",
        name="Варёная оранжевая чечевица с добавками",
        ingredients=[
            Need("red_lentils", "main", "normal"),
            Need("onion", "required", "little"),
            Need("carrot", "addition", "little"),
            Need("butter", "required", "little", accepts=["smalec"]),
            Need("dry_garlic", "spice", "spice"),
            Need("black_pepper", "spice", "spice"),
        ],
        comment="Чечевицы немного, поэтому получится маленькая порция или густая добавка.",
    ),

    Recipe(
        id="mushrooms_sour_cream",
        name="Грибы в сметане с луком",
        ingredients=[
            Need("mushroom", "main", "many"),
            Need("sour_cream", "required", "normal"),
            Need("onion", "required", "little"),
            Need("butter", "required", "little", accepts=["smalec"]),
            Need("black_pepper", "spice", "spice"),
        ],
    ),

    Recipe(
        id="mushrooms_cheese_sour_cream",
        name="Грибы со сметаной и сыром",
        ingredients=[
            Need("mushroom", "main", "many"),
            Need("sour_cream", "required", "normal"),
            Need("hard_cheese", "required", "little"),
            Need("onion", "addition", "little"),
            Need("butter", "required", "little", accepts=["smalec"]),
        ],
        comment="Что-то вроде очень простой домашней версии жюльена без духовочной торжественности.",
    ),

    Recipe(
        id="chicken_mushrooms_sour_cream",
        name="Куриное филе с грибами в сметане",
        ingredients=[
            Need("chicken_fillet", "main", "normal"),
            Need("mushroom", "required", "normal"),
            Need("sour_cream", "required", "normal"),
            Need("onion", "required", "little"),
            Need("butter", "required", "little", accepts=["smalec"]),
            Need("dry_garlic", "spice", "spice"),
            Need("black_pepper", "spice", "spice"),
        ],
    ),

    Recipe(
        id="buckwheat_mushrooms_onion",
        name="Гречка с грибами и луком",
        ingredients=[
            Need("buckwheat", "main", "normal"),
            Need("mushroom", "required", "normal"),
            Need("onion", "required", "little"),
            Need("butter", "required", "little", accepts=["smalec"]),
            Need("black_pepper", "spice", "spice"),
        ],
    ),

    Recipe(
        id="buckwheat_chicken_mushrooms",
        name="Гречка с курицей и грибами",
        ingredients=[
            Need("buckwheat", "main", "normal"),
            Need("chicken_fillet", "required", "normal"),
            Need("mushroom", "addition", "normal"),
            Need("onion", "required", "little"),
            Need("butter", "required", "little", accepts=["smalec"]),
        ],
    ),

    Recipe(
        id="fried_potatoes_mushrooms",
        name="Жареная картошка с грибами и луком",
        ingredients=[
            Need("potato", "main", "normal"),
            Need("mushroom", "required", "normal"),
            Need("onion", "required", "little"),
            Need("smalec", "required", "little", accepts=["butter"]),
            Need("black_pepper", "spice", "spice"),
        ],
    ),

    Recipe(
        id="mashed_potatoes_cheese",
        name="Картофельное пюре с маслом и сыром",
        ingredients=[
            Need("potato", "main", "normal"),
            Need("butter", "required", "little"),
            Need("hard_cheese", "addition", "little"),
            Need("milk", "addition", "little"),
        ],
    ),

    Recipe(
        id="stewed_young_cabbage_sausage",
        name="Тушёная молодая капуста с варёной колбасой",
        ingredients=[
            Need("young_cabbage", "main", "normal"),
            Need("boiled_sausage", "addition", "normal"),
            Need("onion", "required", "little"),
            Need("carrot", "addition", "little"),
            Need("smalec", "required", "little", accepts=["butter"]),
            Need("black_pepper", "spice", "spice"),
        ],
    ),

    Recipe(
        id="corn_porridge_cheese",
        name="Кукурузная каша с сыром и сметаной",
        ingredients=[
            Need("corn_grits", "main", "normal"),
            Need("butter", "required", "little"),
            Need("hard_cheese", "addition", "little"),
            Need("sour_cream", "addition", "little"),
        ],
    ),

    Recipe(
        id="semolina_porridge",
        name="Манная каша",
        ingredients=[
            Need("semolina", "main", "normal"),
            Need("milk", "required", "normal"),
            Need("butter", "addition", "little"),
        ],
        comment="Молока немного, поэтому можно варить частично на воде.",
    ),

    Recipe(
        id="olivier_like_salad",
        name="Салат почти-оливье без огурцов",
        ingredients=[
            Need("potato", "main", "normal"),
            Need("eggs", "required", "normal"),
            Need("boiled_sausage", "required", "normal"),
            Need("canned_peas", "required", "normal"),
            Need("carrot", "addition", "little"),
            Need("sour_cream", "required", "little"),
            Need("black_pepper", "spice", "spice"),
        ],
        comment="Не классический оливье, но логика блюда похожая: картофель, яйцо, колбаса, горошек, сметанная заправка.",
    ),

    Recipe(
        id="fried_pelmeni_with_onion",
        name="Пельмени с жареным луком и сметаной",
        ingredients=[
            Need("pelmeni", "main", "normal"),
            Need("onion", "required", "little"),
            Need("sour_cream", "required", "little"),
            Need("butter", "required", "little", accepts=["smalec"]),
        ],
    ),

    Recipe(
        id="fried_vareniki_with_onion",
        name="Вареники с жареным луком и сметаной",
        ingredients=[
            Need("vareniki", "main", "normal"),
            Need("onion", "required", "little"),
            Need("sour_cream", "required", "little"),
            Need("butter", "required", "little", accepts=["smalec"]),
        ],
    ),

    Recipe(
        id="rice_stew_peas",
        name="Рис с тушёнкой и зелёным горошком",
        ingredients=[
            Need("rice", "main", "normal"),
            Need("stew", "required", "little"),
            Need("canned_peas", "addition", "normal"),
            Need("onion", "addition", "little"),
            Need("black_pepper", "spice", "spice"),
        ],
        comment="Риса немного, поэтому это маленькое блюдо или одна порция.",
    ),
]
