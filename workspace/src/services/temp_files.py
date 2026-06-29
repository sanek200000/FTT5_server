import tempfile
from pathlib import Path


class TempFiles:
    """
    Утилита для создания временных WAV-файлов.

    Предоставляет методы для безопасного создания временных файлов,
    используемых в TTS-пайплайне для хранения входных и выходных
    аудиоданных.

    Notes:
        - Файлы создаются с delete=False для ручного управления
        - Используется стандартный tempfile.NamedTemporaryFile
    """
    @staticmethod
    def create_wav(data: bytes) -> Path:
        """
        Создаёт временный WAV-файл из бинарных данных.

        Записывает аудиобуфер на диск и возвращает путь к файлу.

        Args:
            data (bytes): WAV-аудио в бинарном формате.

        Returns:
            Path: путь к созданному временному файлу.

        Side Effects:
            - создаёт файл на диске
            - не удаляет файл автоматически (delete=False)
        """
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as file:
            file.write(data)
            return Path(file.name)

    @staticmethod
    def create_output() -> Path:
        """
        Создаёт пустой временный WAV-файл для последующей записи результата.

        Используется как контейнер для выходного аудио в TTS-пайплайне.

        Returns:
            Path: путь к созданному временному файлу.

        Side Effects:
            - создаёт пустой файл на диске
            - файл должен быть заполнен позже (например, sf.write)
        """
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as file:
            return Path(file.name)
