"""
Translator factory — returns the appropriate translator based on TRANSLATION_ENGINE setting.
"""

from django.conf import settings
from .base import BaseTranslator


def get_translator() -> BaseTranslator:
    """
    Factory function: reads TRANSLATION_ENGINE from settings and returns the
    appropriate translator instance.
    """
    engine = getattr(settings, "TRANSLATION_ENGINE", "marian_mt")

    if engine == "marian_mt":
        from .marian_translator import MarianTranslator
        return MarianTranslator()

    if engine == "api":
        from .api_translator import ApiTranslator
        return ApiTranslator()

    raise ValueError(
        f"Unknown TRANSLATION_ENGINE: '{engine}'. "
        f"Valid options: 'marian_mt', 'api'."
    )
