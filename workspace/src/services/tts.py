import time
import soundfile as sf
from loguru import logger
from typing import Optional

from f5_tts.api import F5TTS

from src.services.generation_plan import GenerationPlanBuilder
from src.schemas.job import JobStatus
from src.services.text_similarity import TextSimilarityService
from src.services.whisper import WhisperService
from src.services.audio_processor import AudioProcessor
from src.exceptions import SynthesisException
from src.schemas.tts import AttemptDTO, SynthesisResultDTO, TTSRequestDTO
from src.services.temp_files import TempFiles
from src.services.job import job_manager
from src.config import DEVICE, SAFETENSORS_MISHA, VOCAB_MISHA
from src.utils.downloader import download_model


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
        if not SAFETENSORS_MISHA.exists():
            logger.warning(f"File {str(SAFETENSORS_MISHA)} is not exists")
            download_model(SAFETENSORS_MISHA)
        if not VOCAB_MISHA.exists():
            logger.warning(f"File {str(VOCAB_MISHA)} is not exists")
            download_model(VOCAB_MISHA)

        logger.info("Loading F5-TTS...")
        try:
            self.tts = F5TTS(ckpt_file=str(SAFETENSORS_MISHA), vocab_file=str(VOCAB_MISHA), device=DEVICE)
        except Exception as ex:
            logger.error(f"{type(ex)}: {ex}")
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

        result.ratio = similarity.ratio
        result.token_ratio = similarity.token_ratio
        result.partial_ratio = similarity.partial_ratio

        result.recognized_text = similarity.recognized

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

    # def _prepare_attempt_request(
    #     self,
    #     request: TTSRequestDTO,
    #     attempt: int,
    # ) -> TTSRequestDTO:
    #     current_request = request.model_copy(deep=True)
    #
    #     if attempt > 1:
    #         current_request.seed = randint(0, 2**32 - 1)
    #
    #     if attempt > 3:
    #         current_request.speed = max(0.5, request.speed - 0.1 * (attempt - 3))
    #
    #     return current_request

    def _register_attempt(
        self,
        attempt_history: list[AttemptDTO],
        attempt: int,
        request: TTSRequestDTO,
        result: SynthesisResultDTO,
        score: float,
    ) -> None:

        result.attempt = attempt

        attempt_history.append(
            AttemptDTO(
                attempt=attempt,
                seed=request.seed,
                speed=request.speed,
                similarity=score,
                recognized_text=result.recognized_text,
                generation_time=result.generation_time,
            )
        )

        logger.info(f"Attempt {attempt}/{request.max_attempts}: " f"{score:.2f}%")

    def _select_best_result(
        self,
        result: SynthesisResultDTO,
        request: TTSRequestDTO,
        score: float,
        best_result: Optional[SynthesisResultDTO],
        best_request: Optional[TTSRequestDTO],
        best_score: float,
    ) -> tuple[Optional[SynthesisResultDTO], Optional[TTSRequestDTO], float]:

        if score > best_score:
            if best_result is not None:
                best_result.wav_path.unlink(missing_ok=True)

            return result, request, score

        result.wav_path.unlink(missing_ok=True)
        return best_result, best_request, best_score

    def _finalize_best_result(
        self,
        request: TTSRequestDTO,
        attempt_history: list[AttemptDTO],
        best_result: Optional[SynthesisResultDTO],
        best_request: Optional[TTSRequestDTO],
        best_score: float,
        job_id: Optional[str] = None,
    ) -> SynthesisResultDTO:

        assert best_result is not None
        assert best_request is not None

        logger.warning(
            f"Similarity threshold not reached after "
            f"{request.max_attempts} attempts. "
            f"Best result = {best_score:.2f}%"
        )

        if best_score < request.accept_similarity:
            best_result.wav_path.unlink(missing_ok=True)

            if job_id:
                job_manager.update(
                    job_id,
                    status=JobStatus.FAILED,
                    error=str(
                        f"Best similarity ({best_score:.2f}%) "
                        f"is below accept threshold "
                        f"({request.accept_similarity:.2f}%)"
                        f"Result: {best_result.format_log(best_request)}"
                    ),
                )

            raise SynthesisException(
                f"Best similarity ({best_score:.2f}%) "
                f"is below accept threshold "
                f"({request.accept_similarity:.2f}%)"
            )

        best_result.attempt_history = attempt_history
        logger.info(best_result.format_log(best_request))
        return best_result

    def _synthesize_with_verification(
        self,
        request: TTSRequestDTO,
        ref_audio_bytes: bytes,
        job_id: Optional[str] = None,
    ) -> SynthesisResultDTO:

        if job_id:
            job_manager.update(job_id, status=JobStatus.PROGRESSING)

        attempt_history: list[AttemptDTO] = list()
        best_result: Optional[SynthesisResultDTO] = None
        best_request: Optional[TTSRequestDTO] = None
        best_score = -1.0

        plan = GenerationPlanBuilder.build(request)
        request.max_attempts = plan.max_attempts

        for attempt, params in enumerate(plan.attempts, start=1):
            # current_request = self._prepare_attempt_request(request, attempt)
            current_request = request.model_copy(deep=True)
            current_request.seed = params.seed
            current_request.speed = params.speed

            result = self._synthesize_once(
                request=current_request,
                ref_audio_bytes=ref_audio_bytes,
            )

            score = self._verify_result(current_request, result)
            if job_id:
                job_manager.update(
                    job_id,
                    current_attempt=attempt,
                    similarity=score,
                    speed=current_request.speed,
                )

            self._register_attempt(attempt_history, attempt, current_request, result, score)

            best_result, best_request, best_score = self._select_best_result(
                result,
                current_request,
                score,
                best_result,
                best_request,
                best_score,
            )

            if score >= request.min_similarity:
                logger.info(f"Similarity threshold reached " f"({score:.2f}% >= {request.min_similarity:.2f}%)")

                result.attempt_history = attempt_history
                logger.info(result.format_log(current_request))

                if job_id:
                    job_manager.update(
                        job_id,
                        status=JobStatus.COMPLETED,
                        similarity=score,
                    )
                return result

        return self._finalize_best_result(
            request,
            attempt_history,
            best_result,
            best_request,
            best_score,
            job_id,
        )

    def _synthesize_without_verification(
        self,
        request: TTSRequestDTO,
        ref_audio_bytes: bytes,
    ) -> SynthesisResultDTO:
        result = self._synthesize_once(
            request=request,
            ref_audio_bytes=ref_audio_bytes,
        )

        logger.info(result.format_log(request))
        return result

    def synthesize(
        self,
        request: TTSRequestDTO,
        ref_audio_bytes: bytes,
        job_id: Optional[str] = None,
    ) -> SynthesisResultDTO:

        if not request.verify_with_whisper:
            return self._synthesize_without_verification(request=request, ref_audio_bytes=ref_audio_bytes)

        return self._synthesize_with_verification(
            request=request,
            ref_audio_bytes=ref_audio_bytes,
            job_id=job_id,
        )
