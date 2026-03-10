"""
MarianMT translator — runs Helsinki-NLP/opus-mt-ja-en locally via Hugging Face Transformers.
No API keys needed. Model is downloaded on first use and cached.
Offline mode is enforced — no data is ever sent to HF Hub.
"""

import os
import logging

# Block all outbound Hugging Face Hub network calls.
# Model must already be cached locally. Ensures confidential files never touch external servers.
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
os.environ.setdefault("HF_HUB_OFFLINE", "1")

from .base import BaseTranslator

logger = logging.getLogger(__name__)

# Singleton cache for model + tokenizer
_model = None
_tokenizer = None

# MarianMT has a max token limit; we chunk by sentences to stay safe.
MAX_CHUNK_LENGTH = 400  # characters per chunk (conservative for Japanese)


def _load_model():
    global _model, _tokenizer
    if _model is None:
        from transformers import MarianMTModel, MarianTokenizer

        model_name = "Helsinki-NLP/opus-mt-ja-en"

        # First attempt: load from local cache (offline, no network)
        try:
            logger.info("Loading MarianMT model from local cache...")
            _tokenizer = MarianTokenizer.from_pretrained(model_name, local_files_only=True)
            _model = MarianMTModel.from_pretrained(model_name, local_files_only=True)
            logger.info("MarianMT model loaded from cache.")

        except OSError:
            # Model not cached — temporarily lift offline mode to download, then restore
            logger.warning(
                "MarianMT model not found in local cache. "
                "Downloading now (one-time operation, ~303MB)..."
            )
            prev_tf = os.environ.pop("TRANSFORMERS_OFFLINE", None)
            prev_hf = os.environ.pop("HF_HUB_OFFLINE", None)
            try:
                _tokenizer = MarianTokenizer.from_pretrained(model_name)
                _model = MarianMTModel.from_pretrained(model_name)
                logger.info("MarianMT model downloaded and cached successfully.")
            except Exception as download_exc:
                raise RuntimeError(
                    f"Failed to download MarianMT model: {download_exc}. "
                    "Ensure the server has internet access for the first-time setup."
                ) from download_exc
            finally:
                # Always restore offline restrictions
                if prev_tf is not None:
                    os.environ["TRANSFORMERS_OFFLINE"] = prev_tf
                if prev_hf is not None:
                    os.environ["HF_HUB_OFFLINE"] = prev_hf

    return _model, _tokenizer


def _chunk_text(text: str, max_length: int = MAX_CHUNK_LENGTH) -> list[str]:
    """
    Split text into chunks small enough for MarianMT.
    Tries to split on sentence boundaries (。 or \\n), falls back to hard split.
    """
    chunks: list[str] = []
    # Split on Japanese sentence-ending period or newlines first
    import re
    sentences = re.split(r'(?<=[。\n])', text)

    current_chunk = ""
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        if len(current_chunk) + len(sentence) <= max_length:
            current_chunk += sentence
        else:
            if current_chunk:
                chunks.append(current_chunk)
            # If a single sentence exceeds max_length, hard-split it
            if len(sentence) > max_length:
                for i in range(0, len(sentence), max_length):
                    chunks.append(sentence[i:i + max_length])
            else:
                current_chunk = sentence
                continue
            current_chunk = ""

    if current_chunk:
        chunks.append(current_chunk)

    return chunks if chunks else [text]


class MarianTranslator(BaseTranslator):

    @property
    def engine_name(self) -> str:
        return "marian_mt"

    def translate(self, text: str, source_lang: str = "ja", target_lang: str = "en") -> str:
        if not text.strip():
            return ""

        model, tokenizer = _load_model()
        chunks = _chunk_text(text)
        translated_parts: list[str] = []

        for chunk in chunks:
            inputs = tokenizer(chunk, return_tensors="pt", padding=True, truncation=True, max_length=512)
            outputs = model.generate(**inputs)
            decoded = tokenizer.decode(outputs[0], skip_special_tokens=True)
            translated_parts.append(decoded)

        return " ".join(translated_parts)
