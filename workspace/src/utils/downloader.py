import subprocess
from pathlib import Path

from loguru import logger

from config import SS


def download_model(file: Path):
    file.parent.mkdir(parents=True, exist_ok=True)

    if file.name.endswith("vocab.txt"):
        url = SS.URL_VOCAB
    else:
        url = SS.URL_MODEL_SAFETENSORS

    command = f"curl -L -o '{str(file)}' {url}"
    logger.info(f"Sell command: {command}")
    subprocess.run(command, shell=True, check=True)

    if file.exists():
        logger.info(f"File {str(file)} downloaded.")
    else:
        logger.error(f"File {str(file)} not downloaded.")
