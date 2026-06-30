from pathlib import Path

from src.config import APP_PATH, TEMP_PATH

IGNORE_LIST = {
    "__pycache__",
    ".git",
    ".venv",
    "venv",
    ".idea",
    ".vscode",
    "project_structure.txt",  # Игнорируем сам файл отчета
}


def build_tree(dir_path: Path, prefix: str = "") -> list:
    """
    Рекурсивно строит текстовое дерево файловой системы.

    Обходит директорию и формирует список строк, представляющих
    иерархическую структуру файлов и каталогов в формате дерева
    (ASCII tree).

    Args:
        dir_path (Path): Корневая директория для обхода.
        prefix (str): Префикс отступов для текущего уровня вложенности.

    Returns:
        list[str]: Список строк, представляющих структуру каталога.

    Notes:
        - Исключает директории и файлы, перечисленные в IGNORE_LIST.
        - Сортирует сначала директории, затем файлы (по алфавиту).
        - Использует символы ├── и └── для визуализации структуры.
        - При отсутствии доступа возвращает строку ошибки.
    """

    tree_lines = []

    try:
        items = sorted(
            [x for x in dir_path.iterdir() if x.name not in IGNORE_LIST],
            key=lambda x: (not x.is_dir(), x.name.lower()),
        )
    except PermissionError:
        return [f"{prefix}└── [Ошибка доступа]"]

    count = len(items)
    for index, item in enumerate(items):
        is_last = index == count - 1
        connector = "└── " if is_last else "├── "

        suffix = "/" if item.is_dir() else ""
        tree_lines.append(f"{prefix}{connector}{item.name}{suffix}")

        if item.is_dir():
            next_prefix = prefix + ("    " if is_last else "│   ")
            tree_lines.extend(build_tree(item, next_prefix))

    return tree_lines


def save_structure(root_dir: Path = APP_PATH):
    """
    Сохраняет структуру проекта в текстовый файл.

    Строит дерево файловой системы начиная с `root_dir` и сохраняет
    результат в файл `project_structure.txt` в директории TEMP_PATH.

    Args:
        root_dir (Path): Корневая директория проекта.

    Returns:
        None

    Side Effects:
        - Создает файл `project_structure.txt`.
        - Записывает в него ASCII-дерево структуры проекта.
        - Выводит путь сохраненного файла в консоль.
    """

    tree = [f"{root_dir.name}/"] + build_tree(root_dir)

    output_file = TEMP_PATH.joinpath("project_structure.txt")
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(tree))

    print(f"Структура успешно сохранена в файл: {output_file.name}")
