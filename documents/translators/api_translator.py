"""
Placeholder API-based translator for external services (Google Cloud free tier, DeepL free, etc.).
Implement the `translate()` method with your chosen API when ready to switch.
"""

import logging
from django.conf import settings
from .base import BaseTranslator

logger = logging.getLogger(__name__)


class ApiTranslator(BaseTranslator):

    @property
    def engine_name(self) -> str:
        return "api"

    def translate(self, text: str, source_lang: str = "ja", target_lang: str = "en") -> str:
        """
        External API translation. Swap in your preferred free API here.
        Current implementation raises NotImplementedError as a placeholder.
        """
        api_key = settings.TRANSLATION_API_KEY
        if not api_key:
            raise ValueError(
                "TRANSLATION_API_KEY is not set. "
                "Configure it in .env or switch TRANSLATION_ENGINE to 'marian_mt'."
            )

        # ── Example: Google Cloud Translation v2 (free tier) ──
        # import requests
        # url = "https://translation.googleapis.com/language/translate/v2"
        # resp = requests.post(url, params={"key": api_key}, json={
        #     "q": text,
        #     "source": source_lang,
        #     "target": target_lang,
        #     "format": "text",
        # })
        # resp.raise_for_status()
        # return resp.json()["data"]["translations"][0]["translatedText"]

        raise NotImplementedError(
            "API translator is a placeholder. "
            "Implement the translate() method for your chosen API."
        )
