"""
Abstract base class for translation engines.
All translators must subclass `BaseTranslator` and implement `translate()`.
"""

from abc import ABC, abstractmethod


class BaseTranslator(ABC):

    @abstractmethod
    def translate(self, text: str, source_lang: str = "ja", target_lang: str = "en") -> str:
        """
        Translate `text` from `source_lang` to `target_lang`.
        Returns the translated text.
        """
        ...

    @property
    @abstractmethod
    def engine_name(self) -> str:
        """Return a short identifier for this engine, e.g. 'marian_mt'."""
        ...
