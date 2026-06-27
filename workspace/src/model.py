from dataclasses import dataclass
from pathlib import Path
import tempfile

from f5_tts.api import F5TTS
import soundfile as sf

from src.config import SAFETENSORS_MISHA, VOCAB_MISHA


class TTSModel:
    def __init__(self) -> None:
        print("Loading F5-TTS...")

        self.tts = F5TTS(ckpt_file=str(SAFETENSORS_MISHA), vocab_file=str(VOCAB_MISHA), device="cpu")
        print("F5-TTS loaded.")

    def infer(self, ref_file, ref_text, gen_text):
        return self.tts.infer(ref_file=ref_file, ref_text=ref_text, gen_text=gen_text)

    def synthesize(
        self,
        ref_audio_bytes: bytes,
        ref_text: str,
        gen_text: str,
    ) -> Path:

        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp.write(ref_audio_bytes)
            ref_path = Path(tmp.name)

        wav, sr, _ = self.tts.infer(
            ref_file=str(ref_path),
            ref_text=ref_text,
            gen_text=gen_text,
        )

        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as out:
            out_path = Path(out.name)
            sf.write(out_path, wav, sr)

        return out_path


@dataclass
class SynthesisResult:
    wav_path: Path
    sample_rate: int
    duration: float
