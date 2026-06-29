from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field


class TTSRequestDTO(BaseModel):
    """
    Pydantic-схема для параметров запроса на синтез речи.

    Определяет входные параметры для TTS-пайплайна,
    включая текстовую кондицию, управление скоростью
    и параметры постобработки аудио.

    Attributes:
        ref_text (str): Референсный текст, соответствующий
            аудиофайлу диктора.
        gen_text (str): Текст для синтеза речи.
        speed (float): Скорость генерации речи (0.5–2.0).
        remove_silence (bool): Удаление тишины после генерации.
        seed (Optional[int]): Seed для воспроизводимости генерации.
        match_duration (bool): Приведение длительности к референсу.
    """
    ref_text: str
    gen_text: str

    speed: float = Field(default=1.0, ge=0.5, le=2.0)
    remove_silence: bool = False
    seed: Optional[int] = None

    match_duration: bool = False
    # target_duration: Optional[float] = Field(default=None, gt=0)


class SynthesisResultDTO(BaseModel):
    """
    Pydantic-схема для результата синтеза речи.

    Содержит метаданные генерации и пути к артефактам,
    созданным в процессе TTS-инференса.

    Attributes:
        ref_path (Path): Путь к сохранённому референсному аудио.
        wav_path (Path): Путь к сгенерированному аудиофайлу.
        generation_time (float): Время выполнения генерации (сек).
        ref_duration (float): Длительность референсного аудио.
        result_duration (float): Длительность сгенерированного аудио.
        stretch_ratio (float): Коэффициент выравнивания длительности
            (если применялся `match_duration`).
    """
    ref_path: Path
    wav_path: Path
    generation_time: float
    ref_duration: float
    result_duration: float
    stretch_ratio: float
