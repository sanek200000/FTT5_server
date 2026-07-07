from loguru import logger


class TextPreprocessor:
    SHORT_SENTENCE_WORDS = 3

    PREFIX = "..."
    SUFFIX = "..."

    @classmethod
    def prepare_generation_text(cls, text: str) -> str:
        if len(text.split()) > cls.SHORT_SENTENCE_WORDS:
            return text

        result = f"{cls.PREFIX} {text} {cls.SUFFIX}"
        logger.debug(f"Prepared short text '{text}' -> '{result}'")
        return result
