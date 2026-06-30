import time
import soundfile as sf

from f5_tts.api import F5TTS
import soundfile as sf

from src.services.audio_processor import AudioProcessor
from src.exceptions import SynthesisException
from src.schemas.tts import SynthesisResultDTO, TTSRequestDTO
from src.services.temp_files import TempFiles
from src.config import SAFETENSORS_MISHA, VOCAB_MISHA


class TTSModel:
    """
    Обёртка над моделью F5-TTS для локального синтеза речи.

    Инкапсулирует загрузку модели, выполнение inference и постобработку
    аудио (удаление тишины, нормализация длительности, сохранение файлов).

    Attributes:
        tts (F5TTS): Инициализированная модель TTS.
    """
    def __init__(self) -> None:
        """
        Загружает модель F5-TTS в память.

        Notes:
            Загружает веса из путей SAFETENSORS_MISHA и VOCAB_MISHA.
        """
        print("Loading F5-TTS...")

        self.tts = F5TTS(ckpt_file=str(SAFETENSORS_MISHA), vocab_file=str(VOCAB_MISHA), device="cpu")
        print("F5-TTS loaded.")

    def infer(self, ref_file, ref_text, gen_text):
        """
        Выполняет прямой inference модели F5-TTS.

        Args:
            ref_file (str): Путь к референсному аудиофайлу.
            ref_text (str): Текст, соответствующий референсному аудио.
            gen_text (str): Генерируемый текст.

        Returns:
            tuple: Результат генерации модели F5-TTS.
        """
        return self.tts.infer(ref_file=ref_file, ref_text=ref_text, gen_text=gen_text)

    def synthesize(
        self,
        request: TTSRequestDTO,
        ref_audio_bytes: bytes,
    ) -> SynthesisResultDTO:
        """
        Выполняет полный пайплайн синтеза речи.

        Включает:
        - сохранение референсного аудио во временный файл
        - выполнение TTS inference
        - постобработку (удаление тишины, выравнивание длительности)
        - сохранение результата на диск
        - расчёт метрик генерации

        Args:
            request (TTSRequestDTO): Параметры синтеза речи.
            ref_audio_bytes (bytes): Референсное аудио в бинарном виде.

        Returns:
            SynthesisResultDTO: Результат синтеза с метаданными.

        Raises:
            SynthesisException: Ошибка во время генерации TTS.

        Side Effects:
            - Создаёт временные файлы (ref и output WAV).
            - Записывает сгенерированное аудио на диск.
            - Выполняет обработку сигнала (trim / time-stretch).
        """

        started = time.perf_counter()

        ref_path = TempFiles.create_wav(ref_audio_bytes)
        ref_info = sf.info(ref_path)
        ref_duration = ref_info.duration
        try:
            wav, sr, _ = self.tts.infer(
                ref_file=str(ref_path),
                ref_text=request.ref_text,
                gen_text=request.gen_text,
                speed=request.speed,
                remove_silence=request.remove_silence,
                seed=request.seed,
            )
        except Exception as ex:
            raise SynthesisException(str(ex))

        if request.remove_silence:
            wav = AudioProcessor.trim_silence(wav, sr)

        generation_time = time.perf_counter() - started
        result_duration = len(wav) / sr

        out_path = TempFiles.create_output()
        sf.write(out_path, wav, sr)

        stretch_ratio = 1.0
        if request.match_duration:
            stretch_ratio = AudioProcessor.match_duration(
                wav_path=out_path,
                target_duration=ref_duration,
            )

        return SynthesisResultDTO(
            ref_path=ref_path,
            wav_path=out_path,
            generation_time=generation_time,
            ref_duration=ref_duration,
            result_duration=result_duration,
            stretch_ratio=stretch_ratio,
        )
