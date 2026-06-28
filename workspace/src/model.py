import time
import soundfile as sf

from f5_tts.api import F5TTS
import soundfile as sf

from src.services.audio_processor import AudioProcessor
from src.exceptions import SynthesisException
from src.schemas.tts import SynthesisResultDTO, TTSRequestDTO
from src.services.temp_files import TempFiles
from src.config import SAFETENSORS_MISHA, VOCAB_MISHA

# @dataclass(slots=True)
# class SynthesisResult:
#     ref_path: Path
#     wav_path: Path


class TTSModel:
    def __init__(self) -> None:
        print("Loading F5-TTS...")

        self.tts = F5TTS(ckpt_file=str(SAFETENSORS_MISHA), vocab_file=str(VOCAB_MISHA), device="cpu")
        print("F5-TTS loaded.")

    def infer(self, ref_file, ref_text, gen_text):
        return self.tts.infer(ref_file=ref_file, ref_text=ref_text, gen_text=gen_text)

    def synthesize(
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
