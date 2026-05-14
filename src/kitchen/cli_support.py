from __future__ import annotations

import sys
from dataclasses import dataclass

from . import constants as cnst
from .i18n import DEFAULT_LANG, normalize_language, t


@dataclass(frozen=True)
class CliRuntime:
    lang: str = DEFAULT_LANG

    def __post_init__(self) -> None:
        object.__setattr__(self, "lang", normalize_language(self.lang))

    @classmethod
    def from_args(cls, args) -> "CliRuntime":
        return cls(getattr(args, "lang", DEFAULT_LANG))

    @staticmethod
    def bootstrap_lang_from_argv(argv: list[str] | None = None) -> str:
        tokens = list(argv if argv is not None else sys.argv[1:])

        for index, token in enumerate(tokens):
            if token == "--lang" and index + 1 < len(tokens):
                return normalize_language(tokens[index + 1])

            if token.startswith("--lang="):
                return normalize_language(token.split("=", 1)[1])

        return DEFAULT_LANG

    @staticmethod
    def configure_console_output() -> None:
        for stream_name in ("stdout", "stderr"):
            stream = getattr(sys, stream_name, None)
            if stream is None or not hasattr(stream, "reconfigure"):
                continue

            try:
                stream.reconfigure(encoding="utf-8")
            except ValueError:
                continue

    def text(self, key: str, **kwargs: object) -> str:
        return t(f"cli.{key}", self.lang, **kwargs)

    def recipe_status(self, status: str) -> str:
        return t(f"recipe.status.{status}", self.lang)

    def cuisine_label(self, cuisine_id: str) -> str:
        return cnst.facet_label("cuisine", cuisine_id, self.lang)
