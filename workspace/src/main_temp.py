import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
from src.services.text_similarity import TextSimilarityService
from src.utils.generate_tree import save_structure
from src.services.audio_processor import AudioProcessor

if __name__ == "__main__":
    # save_structure()

    AudioProcessor.analyze(wav_path=Path("/workspace/gmas_abli_albik_z_u_zvlastni_t_oUOw.wav"))
