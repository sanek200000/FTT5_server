import io
import re
from statistics import median
import subprocess
from pathlib import Path

import numpy as np
import soundfile as sf
from loguru import logger
from audiostretchy.stretch import stretch_audio

from pydub import AudioSegment
from pydub.silence import detect_nonsilent

from src.schemas.audio import (
    ListRegionsDTO,
    PauseEditDTO,
    PauseEditPlanDTO,
    PauseScaleDTO,
    PauseStatisticDTO,
    SilenceRegionDTO,
)


class AudioProcessor:

    @staticmethod
    def analyze(
        wav_path: Path,
        noise: float = -35,
        min_duration: float = 0.1,
    ) -> ListRegionsDTO:
        command = f"ffmpeg -i {str(wav_path)} -af silencedetect={noise}dB:d={min_duration} -f null -"
        logger.info(f"Command: '{command}'")

        procces = subprocess.run(
            command,
            shell=True,
            # check=True,
            capture_output=True,
            text=True,
        )
        stderr = procces.stderr

        silence_start_pattern = re.compile(r"silence_start:\s*([\d.]+)")
        silence_end_pattern = re.compile(r"silence_end:\s*([\d.]+)")

        starts = [float(match.group(1)) for match in silence_start_pattern.finditer(stderr)]
        ends = [float(match.group(1)) for match in silence_end_pattern.finditer(stderr)]

        regions = ListRegionsDTO(
            regions=[
                SilenceRegionDTO(
                    start=start,
                    end=end,
                )
                for start, end in zip(starts, ends)
            ]
        )

        logger.debug(f"Detected {regions.length} silence regions")
        logger.debug(regions.format_log())

        return regions

    @staticmethod
    def calculate_pause_scale(reference: ListRegionsDTO, generated: ListRegionsDTO) -> PauseScaleDTO:
        ref = reference.statistics
        gen = generated.statistics

        def safe_div(a: float, b: float) -> float:
            if b <= 0:
                return 1.0
            return a / b

        k25 = safe_div(ref.p25, gen.p25)
        k50 = safe_div(ref.median, gen.median)
        k75 = safe_div(ref.p75, gen.p75)

        scale = median([k25, k50, k75])

        return PauseScaleDTO(
            scale=scale,
            reference=ref,
            generated=gen,
            k25=k25,
            k50=k50,
            k75=k75,
        )

    @staticmethod
    def build_pause_edit_plan(reference: ListRegionsDTO, generated: ListRegionsDTO) -> PauseEditPlanDTO:
        scale = AudioProcessor.calculate_pause_scale(reference, generated)

        plan = PauseEditPlanDTO()

        ref_stats = reference.statistics
        for region in generated.regions:
            new_duration = region.duration * scale.scale
            new_duration = max(ref_stats.minimum, new_duration)
            new_duration = min(ref_stats.maximum, new_duration)

            plan.edits.append(
                PauseEditDTO(
                    original=region,
                    target_duration=new_duration,
                )
            )

        return plan

    @staticmethod
    def build_segments(regions: ListRegionsDTO, duration: float) -> list[tuple[float, float]]:
        segments = list()
        cursor = 0.0

        for region in regions.regions:
            if region.start > cursor:
                segments.append(cursor, region.start)

            cursor = region.end

        if cursor < duration:
            segments.append(cursor, duration)

        return segments

    @staticmethod
    def trim_edges(wav_path: Path) -> None:
        raise NotImplementedError

    @staticmethod
    def compress_pauses(wav_path: Path, target_pause: float) -> None:
        raise NotImplementedError

    @staticmethod
    def fit_duration(wav_path: Path, target_duration: float) -> float:
        raise NotImplementedError


class AudioProcessor_old:
    """
    Утилитарный процессор аудио для постобработки TTS-результатов.

    Предоставляет операции:
    - нормализация длительности аудио (time-stretch)
    - удаление тишины на основе энергетического анализа сигнала

    Использует комбинацию:
    - soundfile (I/O WAV)
    - pydub (анализ и сегментация тишины)
    - audiostretchy (time stretching без изменения pitch)
    """

    @staticmethod
    def match_duration(wav_path: Path, target_duration: float) -> float:
        """
        Приводит длительность аудиофайла к целевой.

        Вычисляет коэффициент растяжения и применяет time-stretch
        к WAV-файлу in-place.

        Args:
            wav_path (Path): путь к WAV-файлу (будет изменён).
            target_duration (float): целевая длительность в секундах.

        Returns:
            float: коэффициент растяжения (ratio).

        Notes:
            - если отклонение < 1%, операция пропускается
            - используется audiostretchy.stretch_audio
        """
        info = sf.info(wav_path)
        current_duration = info.duration

        if current_duration <= 0:
            logger.debug(f"Длительность файла '{str(wav_path)}' меньше 0: {current_duration} сек.")
            return 1.0

        ratio = target_duration / current_duration

        if abs(ratio - 1.0) < 0.01:
            logger.debug("Отклонение целевой и реальной длинны файла < 1%")
            return 1.0

        stretch_audio(
            input_path=str(wav_path),
            output_path=str(wav_path),
            ratio=ratio,
        )
        logger.info(
            "\n----------------------------------------------------------\n"
            f"Длительность файла '{str(wav_path)}' {current_duration} сек. приведена к целевой {target_duration} сек.\n"
            f"Коэффициент растяжения/сжатия = {ratio}"
            "\n----------------------------------------------------------\n"
        )
        return ratio

    @staticmethod
    def _clalculate_silence_threshold(audio: AudioSegment) -> float:
        """
        Вычисляет порог тишины для аудиосегмента.

        Основан на уровне громкости (dBFS) с ограничениями диапазона.

        Args:
            audio (AudioSegment): входной аудиосигнал.

        Returns:
            float: порог тишины в dBFS.
        """
        if audio.rms == 0:
            logger.warning("Аудиосигнал пустой (RMS = 0). Возвращен дефолтный порог -60.0 dBFS.")
            return -60.0

        rms_db = audio.dBFS
        logger.debug(f"Исходная средняя громкость аудио (dBFS): {rms_db:.2f}")

        base_threshold = rms_db - 28
        threshold = max(base_threshold, -55)
        threshold = min(threshold, -48)

        logger.debug(
            "\n----------------------------------------------------------\n"
            f"Расчет окончен. Базовый (без ограничений): {base_threshold:.2f} dBFS. \n"
            f"Итоговый (с ограничениями): {threshold:.2f} dBFS."
            "\n----------------------------------------------------------\n"
        )
        return threshold

    @staticmethod
    def trim_silence(
        wav: np.ndarray,
        sample_rate: int,
        min_silence_len: int = 200,  # было 80
        keep_silence: int = 30,
    ) -> np.ndarray:
        """
        Удаляет тишину в начале и конце аудиосигнала.

        Выполняет:
        - конвертацию numpy → WAV buffer
        - детекцию ненулевых сегментов
        - обрезку по границам активности
        - восстановление numpy массива

        Args:
            wav (np.ndarray): аудиосигнал.
            sample_rate (int): частота дискретизации.
            min_silence_len (int): минимальная длина тишины (ms).
            keep_silence (int): запас тишины вокруг сегмента (ms).

        Returns:
            np.ndarray: обрезанный аудиосигнал.

        Notes:
            - используется pydub.detect_nonsilent
            - порог вычисляется динамически через dBFS
            - если сегменты не найдены, возвращает исходный wav
        """

        logger.info(
            f"Старт trim_silence: Сэмплов={len(wav)}, Sample Rate={sample_rate}Hz, "
            f"min_silence_len={min_silence_len}ms, keep_silence={keep_silence}ms"
        )

        # Конвертация numpy → WAV buffe
        buffer = io.BytesIO()
        sf.write(buffer, wav, sample_rate, format="WAV")
        buffer.seek(0)

        audio = AudioSegment.from_file(buffer, format="wav")
        total_duration = len(audio)

        # Фильтруем низкочастотный ИИ-гул (sub-bass) перед детекцией.
        # Это не меняет финальный звук, но убирает невидимый шум, мешающий определять тишину.
        analysis_audio = audio.high_pass_filter(60).low_pass_filter(8000)

        # Динамический расчет порога
        silence_thresh = AudioProcessor._clalculate_silence_threshold(analysis_audio)
        logger.info(
            f"Анализ аудио: Длительность={total_duration}ms, "
            f"Общая громкость dBFS={analysis_audio.dBFS:.2f}, Порог тишины={silence_thresh:.2f} dBFS"
        )

        # Детекция активных (не-тихих) сегментов
        regions = detect_nonsilent(
            analysis_audio,
            min_silence_len=min_silence_len,
            silence_thresh=silence_thresh,
        )

        if not regions:
            logger.warning("Активные звуковые сегменты не найдены. Возвращаем исходный массив.")
            return wav

        logger.info(f"Найдено активных сегментов: {len(regions)}")
        logger.info(f"Первый сегмент: {regions[0]}, Последний сегмент: {regions[-1]}")

        start = max(0, regions[0][0] - keep_silence)
        end = min(total_duration, regions[-1][1] + keep_silence)
        trimmed_duration = end - start
        logger.info(
            f"Результат обрезки: {start}ms -> {end}ms. "
            f"Отрезано с начала: {start}ms, Отрезано с конца: {total_duration - end}ms. "
            f"Новая длительность: {trimmed_duration}ms"
        )

        # Если фактически ничего не изменилось, возвращаем оригинал без лишних пересборок
        if start == 0 and end == total_duration:
            logger.debug("Изменений не требуется, возвращаем исходный массив.")
            return wav

        # Обрезка оригинального (!) аудио по вычисленным меткам
        trimmed = audio[start:end]

        # Восстановление numpy массива
        out = io.BytesIO()
        trimmed.export(out, format="wav")
        out.seek(0)

        result, _ = sf.read(out, dtype="float32")
        return result
