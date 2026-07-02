import time
from typing import Optional
from loguru import logger
import soundfile as sf

from f5_tts.api import F5TTS

from src.services.text_similarity import TextSimilarityService
from src.services.whisper import WhisperService
from src.services.audio_processor import AudioProcessor
from src.exceptions import SynthesisException
from src.schemas.tts import SynthesisResultDTO, TTSRequestDTO
from src.services.temp_files import TempFiles
from src.config import DEVICE, SAFETENSORS_MISHA, VOCAB_MISHA


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
        logger.info("Loading F5-TTS...")
        self.tts = F5TTS(ckpt_file=str(SAFETENSORS_MISHA), vocab_file=str(VOCAB_MISHA), device=DEVICE)
        logger.info("F5-TTS loaded.")

        self._whisper = WhisperService()
        self._similarity = TextSimilarityService()

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

    def _verify_result(
        self,
        request: TTSRequestDTO,
        result: SynthesisResultDTO,
    ) -> float:
        recognized = self._whisper.transcribe(result.wav_path)
        similarity = self._similarity.similarity(
            expected=request.gen_text,
            recognized=recognized,
        )

        result.similarity = similarity.score
        result.recognized_text = similarity.recognized

        # logger.debug(
        #     "\n"
        #     "Whisper:\n"
        #     "score=%.2f%%\n"
        #     "expected='%s'\n"
        #     "recognized='%s'\n"
        #     "expected_norm='%s'\n"
        #     "recognized_norm='%s'",
        #     similarity.score,
        #     similarity.expected,
        #     similarity.recognized,
        #     similarity.expected_norm,
        #     similarity.recognized_norm,
        # )

        return similarity.score

    def _synthesize_once(
        self,
        request: TTSRequestDTO,
        ref_audio_bytes: bytes,
    ) -> SynthesisResultDTO:
        started = time.perf_counter()

        ref_path = TempFiles.create_wav(ref_audio_bytes)
        ref_info = sf.info(ref_path)
        ref_duration = ref_info.duration

        # logger.debug(
        #     "\n" "Request:\n" "ref_text='%s'\n" "gen_text='%s'\n" "speed=%.3f\n" "seed=%s",
        #     request.ref_text,
        #     request.gen_text,
        #     request.speed,
        #     request.seed,
        # )

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

        # logger.debug(
        #     "TTS: " "gen=%.2fs " "ref=%.2fs " "out=%.2fs " "stretch=%.3f",
        #     generation_time,
        #     ref_duration,
        #     result_duration,
        #     stretch_ratio,
        # )

        return SynthesisResultDTO(
            ref_path=ref_path,
            wav_path=out_path,
            generation_time=generation_time,
            ref_duration=ref_duration,
            result_duration=result_duration,
            stretch_ratio=stretch_ratio,
        )

    def synthesize(
        self,
        request: TTSRequestDTO,
        ref_audio_bytes: bytes,
    ) -> SynthesisResultDTO:

        if not request.verify_with_whisper:
            result = self._synthesize_once(
                request=request,
                ref_audio_bytes=ref_audio_bytes,
            )

            logger.info(result.format_log(request))
            return result

        best_result: Optional[SynthesisResultDTO] = None
        best_score = -1.0

        for attempt in range(1, request.max_attempts + 1):
            result = self._synthesize_once(
                request=request,
                ref_audio_bytes=ref_audio_bytes,
            )

            score = self._verify_result(
                request=request,
                result=result,
            )

            result.attempts = attempt

            if score > best_score:
                if best_result in not None:
                    best_result.wav_path.unlink(missing_ok=True)

                best_result = result
                best_score = score

            else:
                best_result.wav_path.unlink(missing_ok=True)

            logger.info(
            f"Attempt {attempt}/{request.max_attempts}: "
            f"{score:.2f}%"
            )

            if score >= request.min_similarity:
                logger.info(
                    f"Similarity threshold reached "
                    f"({score:.2f}% >= {request.min_similarity:.2f}%)"
                )

                logger.info(result.format_log(request))
                return result

        logger.warning(
            f"Similarity threshold not reached after "
            f"{request.max_attempts} attempts. "
            f"Best result = {best_score:.2f}%"
        )
    
        logger.info(best_result.format_log(request))
    
        return best_result

