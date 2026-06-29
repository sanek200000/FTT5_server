import io
from pathlib import Path

import numpy as np
import soundfile as sf
from audiostretchy.stretch import stretch_audio

from pydub import AudioSegment
from pydub.silence import detect_nonsilent


class AudioProcessor:
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
            return 1.0

        ratio = target_duration / current_duration

        if abs(ratio - 1.0) < 0.01:
            return 1.0

        stretch_audio(
            input_path=str(wav_path),
            output_path=str(wav_path),
            ratio=ratio,
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
            return -60.0

        rms_db = audio.dBFS

        threshold = rms_db - 18
        threshold = max(threshold, -55)
        threshold = min(threshold, -25)

        return threshold

    @staticmethod
    def trim_silence(
        wav: np.ndarray,
        sample_rate: int,
        min_silence_len: int = 80,
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

        buffer = io.BytesIO()

        sf.write(
            buffer,
            wav,
            sample_rate,
            format="WAV",
        )

        buffer.seek(0)

        audio = AudioSegment.from_file(buffer, format="wav")

        silence_thresh = AudioProcessor._clalculate_silence_threshold(audio)
        print(f"[AudioProcessor] " f"dBFS={audio.dBFS:.1f} " f"threshold={silence_thresh:.1f}")

        regions = detect_nonsilent(
            audio,
            min_silence_len=min_silence_len,
            silence_thresh=silence_thresh,
        )

        if not regions:
            return wav

        start = max(0, regions[0][0] - keep_silence)

        end = min(len(audio), regions[-1][1] + keep_silence)

        trimmed = audio[start:end]

        out = io.BytesIO()

        trimmed.export(out, format="wav")

        out.seek(0)

        result, _ = sf.read(out, dtype="float32")

        return result
