import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
from src.services.text_similarity import TextSimilarityService

if __name__ == "__main__":
    print(
        TextSimilarityService.similarity(
            "Ну что ж, если ты действительно решил идти туда один.",
            "Ну что же если ты действ+ительно .,!?;:() решил идти туда один",
        )
    )
