import tempfile
from pathlib import Path


class TempFiles:
    @staticmethod
    def create_wav(data: bytes) -> Path:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as file:
            file.write(data)
            return Path(file.name)

    @staticmethod
    def create_output() -> Path:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as file:
            return Path(file.name)
