from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field


class TTSRequestDTO(BaseModel):
    """
    Pydantic-схема параметров запроса на синтез речи.

    Определяет параметры генерации, постобработки аудио и
    верификации результата распознаванием речи.

    Attributes:
        ref_text (str): Референсный текст, соответствующий
            аудиофайлу диктора.
        gen_text (str): Текст, который необходимо синтезировать.
        speed (float): Скорость генерации речи в диапазоне
            от 0.5 до 2.0.
        remove_silence (bool): Удалять ли тишину после генерации.
        seed (Optional[int]): Seed для воспроизводимости результата.
        match_duration (bool): Приводить ли длительность
            сгенерированного аудио к длительности референса.
        max_attempts (int): Максимальное количество попыток
            генерации при неудовлетворительной верификации.
        min_similarity (float): Минимально допустимое значение
            схожести (%) между ожидаемым и распознанным текстом.
        verify_with_whisper (bool): Выполнять ли проверку качества
            синтеза с помощью модели распознавания речи (Whisper).
    """

    ref_text: str
    gen_text: str

    speed: float = Field(default=1.0, ge=0.5, le=2.0)
    remove_silence: bool = False
    seed: Optional[int] = None

    match_duration: bool = False

    max_attempts: Optional[int] = None
    min_similarity: float = Field(default=95.0, ge=0.0, le=100.0)
    accept_similarity: float = 90.0
    verify_with_whisper: bool = True


class AttemptDTO(BaseModel):
    attempt: int
    seed: Optional[int]
    speed: float
    similarity: float
    recognized_text: str
    generation_time: float


class GenerationAttemptDTO(BaseModel):
    seed: Optional[int]
    speed: float


class GenerationPlanDTO(BaseModel):
    attempts: list[GenerationAttemptDTO]

    @property
    def max_attempts(self) -> int:
        return len(self.attempts)


class SynthesisResultDTO(BaseModel):
    ref_path: Path
    wav_path: Path
    generation_time: float
    ref_duration: float
    result_duration: float
    stretch_ratio: float

    attempt: int = 1
    similarity: Optional[float] = None

    ratio: Optional[float] = None
    token_ratio: Optional[float] = None
    partial_ratio: Optional[float] = None

    recognized_text: Optional[str] = None
    attempt_history: list[AttemptDTO] = Field(default_factory=list)

    def format_log(self, request: TTSRequestDTO) -> str:
        attempts_log = "\n".join(
            (
                f"[{item.attempt}] "
                f"score={item.similarity:.2f}% "
                f"speed={item.speed:.2f} "
                f"seed={item.seed} "
                f"time={item.generation_time} "
            )
            for item in self.attempt_history
        )

        return (
            "\n"
            "========================================================\n"
            "Request\n"
            "--------------------------------------------------------\n"
            f"ref_text : {request.ref_text}\n"
            f"gen_text : {request.gen_text}\n"
            f"speed    : {request.speed:.2f}\n"
            f"seed     : {request.seed}\n"
            "\n"
            "Generation\n"
            "--------------------------------------------------------\n"
            f"generation_time : {self.generation_time:.2f} s\n"
            f"reference_time  : {self.ref_duration:.2f} s\n"
            f"result_time     : {self.result_duration:.2f} s\n"
            f"stretch_ratio   : {self.stretch_ratio:.3f}\n"
            "\n"
            "Verification\n"
            "--------------------------------------------------------\n"
            f"attempt         : {self.attempt}\n"
            f"similarity      : {self.similarity}\n"
            f"ratio           : {self.ratio:.2f}\n"
            f"token_ratio     : {self.token_ratio:.2f}\n"
            f"partial_ratio   : {self.partial_ratio:.2f}\n"
            f"recognized      : {self.recognized_text}\n"
            "--------------------------------------------------------\n"
            f"{attempts_log}\n"
            "========================================================"
            "\n"
        )
