import re
from rapidfuzz import fuzz

from src.schemas.similarity import SimilarityResultDTO


class TextSimilarityService:

    @staticmethod
    def normalize(text: str) -> str:
        text = text.lower()
        text = text.replace("ё", "е")

        text = re.sub(r"[^\w\s]", "", text)
        text = re.sub(r"[-–—]", " ", text)
        text = re.sub(r"\s+", " ", text)

        return text.strip()

    @staticmethod
    def calculate_score(
        ratio: float,
        token_ratio: float,
        partial_ratio: float,
    ) -> float:
        return max(ratio, token_ratio, partial_ratio)

    @classmethod
    def similarity(
        cls,
        expected: str,
        recognized: str,
    ) -> float:
        expected_norm = cls.normalize(expected)
        recognized_norm = cls.normalize(recognized)

        ratio = fuzz.ratio(expected_norm, recognized_norm)
        token_ratio = fuzz.token_set_ratio(expected_norm, recognized_norm)
        partial_ratio = fuzz.partial_ratio(expected_norm, recognized_norm)

        score = cls.calculate_score(ratio, token_ratio, partial_ratio)

        return SimilarityResultDTO(
            score=score,
            ratio=ratio,
            token_ratio=token_ratio,
            partial_ratio=partial_ratio,
            expected=expected,
            recognized=recognized,
            expected_norm=expected_norm,
            recognized_norm=recognized_norm,
        )
