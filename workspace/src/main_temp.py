import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
from src.services.text_similarity import TextSimilarityService
from src.utils.generate_tree import save_structure
from src.services.audio_processor import AudioProcessor

if __name__ == "__main__":
    save_structure()

    # AudioProcessor.analyze(wav_path=Path("/workspace/ru.wav"))

    # AudioProcessor.adjust_pauses(
    #     reference_wav=Path("/workspace/en.wav"),
    #     generated_wav=Path("/workspace/ru.wav"),
    # )
