from dataclasses import dataclass, field


@dataclass
class Need:
    item: str
    role: str
    amount: str = "normal"
    accepts: list[str] = field(default_factory=list)
    note: str = ""


@dataclass
class Recipe:
    id: str
    name: str
    ingredients: list[Need]
    comment: str = ""
    name_uk: str = ""
    comment_uk: str = ""
    kind: str = "dish"
    tags: list[str] = field(default_factory=list)
    facets: dict[str, object] = field(default_factory=dict)
    uses_components: list[str] = field(default_factory=list)
    component_for: list[str] = field(default_factory=list)
    missing_allowed: int = 0
    source_family: str = ""
    source_file: str = ""
