import sys
from pathlib import Path
from typing import Optional
from fastapi import FastAPI

sys.path.append(str(Path(__file__).parent.parent))

from src.model import TTSModel

app = FastAPI()
tts: Optional[TTSModel] = None
# tts = TTSModel()


@app.get("/")
def root():
    return {"status": "OK"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", reload=True, host="0.0.0.0", port=8000)
