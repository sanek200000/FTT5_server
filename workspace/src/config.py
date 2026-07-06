import sys
from pathlib import Path
from pydantic_settings import BaseSettings
from loguru import logger

sys.path.append(str(Path(__file__).parent.parent))

BASE_DIR = Path(__file__).resolve().parent.parent

APP_PATH = BASE_DIR.joinpath("src/")
TEMP_PATH = BASE_DIR.joinpath("temp/")
MODELS_PATH = BASE_DIR.joinpath("models/")

SAFETENSORS_MISHA = MODELS_PATH.joinpath(
    "F5-TTS_RUSSIAN_misha/F5TTS_v1_Base_accent_tune/model_last_inference.safetensors"
)
VOCAB_MISHA = MODELS_PATH.joinpath("F5-TTS_RUSSIAN_misha/F5TTS_v1_Base/vocab.txt")


class Settings(BaseSettings):
    COMPOSE_PROFILES: str

    URL_VOCAB: str
    URL_MODEL_SAFETENSORS: str


SS = Settings()
DEVICE = SS.COMPOSE_PROFILES


def should_rotate_on_start(message, file):
    if not hasattr(should_rotate_on_start, "has_run"):
        should_rotate_on_start.has_run = True
        return True
    return False


logger.remove()
logger.add(
    APP_PATH.joinpath("logs/tts_server.log"),
    rotation=should_rotate_on_start,
    retention=10,
)

if __name__ == "__main__":
    [print(f"{key} = {value}") for key, value in globals().items() if not key.startswith("__")]
