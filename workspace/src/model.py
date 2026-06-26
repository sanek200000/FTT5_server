from f5_tts.api import F5TTS

from src.config import SAFETENSORS_MISHA, VOCAB_MISHA


class TTSModel:
    def __init__(self) -> None:
        print("Loading F5-TTS...")

        self.tts = F5TTS(ckpt_file=str(SAFETENSORS_MISHA), vocab_file=str(VOCAB_MISHA), device="cpu")
        print("F5-TTS loaded.")

    def infer(self, ref_file, ref_text, gen_text):
        return self.tts.infer(ref_file=ref_file, ref_text=ref_text, gen_text=gen_text)
