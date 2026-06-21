import json
from typing import Optional


from markupsafe import Markup


class I18nTerm:
    def __init__(self, key: str, term: Optional[str]):
        self.key = key
        self.term = term

    def __str__(self):
        return self.term if self.term is not None else f"<untranslated {self.key}>"

    def __repr__(self):
        return f"I18nTerm({self.key}, {self.term})"

    def format(self, *args, **kwargs):
        if self.term is None:
            return f"<untranslated {self.key}>"
        # Use Markup.format which automatically escapes arguments
        return Markup(self.term).format(*args, **kwargs)


class I18nProvider:
    def __init__(self, language: str = "en") -> None:
        self.language = language
        self.translations = {}
        self.load_translations()

    def load_translations(self) -> None:
        with open(f"languages/{self.language}.json", "r", encoding="utf-8") as f:
            terms = json.load(f)
        self.translations = {key: I18nTerm(key, term) for key, term in terms.items()}

    def __getattr__(self, key: str) -> I18nTerm:
        return self.translations.get(key, I18nTerm(key, None))
