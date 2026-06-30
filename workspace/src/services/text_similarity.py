import re
from rapidfuzz import fuzz

from src.schemas.similarity import SimilarityResultDTO


class TextSimilarityService:
    all_text_symbols = [
        ".",
        ",",
        "!",
        "?",
        ";",
        ":",
        "…",
        "—",
        "–",
        "-",
        "(",
        ")",
        "[",
        "]",
        "{",
        "}",
        "<",
        ">",
        '"',
        "'",
        "`",
        "«",
        "»",
        "“",
        "”",
        "‘",
        "’",
        "„",
        "+",
        "=",
        "*",
        "/",
        "%",
        "№",
        "$",
        "€",
        "£",
        "¥",
        "₽",
        "¢",
        "¤",
        "@",
        "#",
        "§",
        "&",
        "_",
        "|",
        "\\",
        "^",
        "~",
        "☺",
        "☹",
        "♥",
        "★",
        "✔",
        "✖",
        "⚠",
        "ℹ",
        "⚙",
        "✉",
        "✏",
    ]

    @staticmethod
    def normalize(text: str) -> str:
        text = text.lower()
        text = text.replace("ё", "е")

        text = re.sub(r"[^\w\s]", "", text)
        text = re.sub(r"[-–—]", " ", text)
        text = re.sub(r"\s+", " ", text)

        return text.strip()

    # @classmethod
    # def normalize(cls, text: str) -> str:
    #     text = text.lower()
    #     text = text.replace("ё", "е")
    #
    #     for symbol in cls.all_text_symbols:
    #         text = text.replace(symbol, "")
    #
    #     text = text.replace(" ", "")
    #     return text.strip()

    @classmethod
    def similarity(
        cls,
        expected: str,
        recognized: str,
    ) -> float:
        expected_norm = cls.normalize(expected)
        recognized_norm = cls.normalize(recognized)

        score = fuzz.token_set_ratio(expected_norm, recognized_norm)

        return SimilarityResultDTO(
            score=score,
            expected=expected,
            recognized=recognized,
            expected_norm=expected_norm,
            recognized_norm=recognized_norm,
        )
