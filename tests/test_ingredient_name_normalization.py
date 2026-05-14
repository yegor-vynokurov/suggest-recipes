from __future__ import annotations

from collections import defaultdict

from src.kitchen import constants as cnst


def test_reviewed_near_duplicate_pairs_have_distinct_ukrainian_names() -> None:
    assert cnst.item_name("dumplings", "uk") == "галушки"
    assert cnst.item_name("pelmeni", "uk") == "пельмені"

    assert cnst.item_name("chicken_gizzards", "uk") == "курячі шлунки"
    assert cnst.item_name("tripe", "uk") == "рубець"

    assert cnst.item_name("ground_veal", "uk") == "телячий фарш"
    assert cnst.item_name("minced_meat", "uk") == "фарш"

    assert cnst.item_name("reblochon", "uk") == "реблошон"
    assert cnst.item_name("soft_cheese", "uk") == "м'який сир"

    assert cnst.item_name("bresaola", "uk") == "брезаола"
    assert cnst.item_name("fenalar", "uk") == "феналар"

    assert cnst.item_name("matjes_herring", "uk") == "оселедець матіас"
    assert cnst.item_name("pickled_herring", "uk") == "маринований оселедець"

    assert cnst.item_name("cocoa", "uk") == "какао"
    assert cnst.item_name("cocoa_powder", "uk") == "какао-порошок"


def test_visible_ingredients_do_not_share_the_same_ukrainian_name() -> None:
    duplicates: dict[str, list[str]] = defaultdict(list)

    for item_id, item in cnst.INGREDIENTS.items():
        inventory = item.get("inventory", {}) or {}
        if not inventory.get("track", False):
            continue

        name_uk = cnst.item_name(item_id, "uk").strip()
        if name_uk:
            duplicates[name_uk].append(item_id)

    conflicting = {
        name_uk: sorted(item_ids)
        for name_uk, item_ids in duplicates.items()
        if len(item_ids) > 1
    }

    assert not conflicting, (
        "Visible ingredients should not collapse into the same Ukrainian display name: "
        f"{conflicting!r}"
    )
