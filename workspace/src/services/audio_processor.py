import io
from pathlib import Path

import numpy as np
import soundfile as sf
from audiostretchy.stretch import stretch_audio

from pydub import AudioSegment
from pydub.silence import detect_nonsilent


class AudioProcessor:

    @staticmethod
    def match_duration(wav_path: Path, target_duration: float) -> float:
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
