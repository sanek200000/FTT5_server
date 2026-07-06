from random import randint

from src.schemas.tts import GenerationAttemptDTO, GenerationPlanDTO, TTSRequestDTO


class GenerationPlanBuilder:
    SHORT_SENTENCE_WORDS = 3

    @staticmethod
    def _random_seed() -> int:
        return randint(0, 2**32 - 1)

    @classmethod
    def _build_short(cls, request: TTSRequestDTO) -> GenerationPlanDTO:
        speeds = (1.00, 0.95, 0.9, 0.85, 0.80)
        attempts = list()

        for _ in range(20):
            attempts.append(
                GenerationAttemptDTO(
                    seed=cls._random_seed(),
                    speed=speeds[_ % len(speeds)],
                )
            )

        attempts[0].seed = request.seed

        return GenerationPlanDTO(attempts)

    @classmethod
    def _build_normal(cls, request: TTSRequestDTO) -> GenerationPlanDTO:
        attempts = [
            GenerationAttemptDTO(
                seed=request.seed,
                speed=request.speed,
            )
        ]

        for _ in range(4):
            attempts.append(
                GenerationAttemptDTO(
                    seed=cls._random_seed(),
                    speed=request.speed,
                )
            )

        return GenerationPlanDTO(attempts)

    @classmethod
    def duild(cls, request: TTSRequestDTO) -> GenerationPlanDTO:
        words = len(request.gen_text.split())

        if words <= cls.SHORT_SENTENCE_WORDS:
            return cls._build_short(request)

        return cls._build_normal(request)
