import sys
from pathlib import Path
from pydantic_settings import BaseSettings
from loguru import logger

sys.path.append(str(Path(__file__).parent.parent))

from src.schemas.tts_manager import SafetensorsDTO, SafetensorDTO

BASE_DIR = Path(__file__).resolve().parent.parent

APP_PATH = BASE_DIR.joinpath("src/")
TEMP_PATH = BASE_DIR.joinpath("temp/")
MODELS_PATH = BASE_DIR.joinpath("models/")

SAFETENSORS_MISHA = MODELS_PATH.joinpath("01/model_last_inference.safetensors")
VOCAB_MISHA = MODELS_PATH.joinpath("vocab.txt")


class Settings(BaseSettings):
    COMPOSE_PROFILES: str

    URL_VOCAB: str
    URL_MODEL_SAFETENSORS: str

    @property
    def MODELS_LIST(self) -> SafetensorsDTO:
        return SafetensorsDTO(
            {
                i: SafetensorDTO(
                    name=item.parent.name,
                    ckpt_path=item,
                    vocab_path=VOCAB_MISHA,
                )
                for i, item in enumerate(MODELS_PATH.rglob("*.safetensors"), start=1)
            }
        )


SS = Settings()
DEVICE = SS.COMPOSE_PROFILES


def should_rotate_on_start(message, file):
    if not hasattr(should_rotate_on_start, "rotated_files"):
        should_rotate_on_start.rotated_files = set()

    file_name = file.name

    if file_name not in should_rotate_on_start.rotated_files:
        should_rotate_on_start.rotated_files.add(file_name)
        return True
    return False

    # if not hasattr(should_rotate_on_start, "has_run"):
    #     should_rotate_on_start.has_run = True
    #     return True
    # return False


logger.remove()
logger.add(
    APP_PATH.joinpath("logs/tts_server.log"),
    rotation=should_rotate_on_start,
    retention=10,
    filter=lambda record: record["extra"].get("name") != "special_log",
)

logger.add(
    APP_PATH.joinpath("logs/memory_check.log"),
    rotation=should_rotate_on_start,
    retention=10,
    filter=lambda record: record["extra"].get("name") == "special_log",
)
mem_log = logger.bind(name="special_log")
mem_log.debug("new session")


if __name__ == "__main__":
    # [print(f"{key} = {value}") for key, value in globals().items() if not key.startswith("__")]
    print(SS.MODELS_LIST)
