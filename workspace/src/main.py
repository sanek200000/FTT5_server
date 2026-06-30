import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import JSONResponse

sys.path.append(str(Path(__file__).parent.parent))

from src.services.lifespan import lifespan
from src.exceptions import SynthesisException
from src.api.tts import router as router_f5tts

app = FastAPI(lifespan=lifespan)
app.include_router(router_f5tts)
# app = FastAPI()


@app.exception_handler(SynthesisException)
async def synthesis_exception_handler(request, ex):
    return JSONResponse(
        status_code=500,
        content={"error": str(ex)},
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", reload=False, host="0.0.0.0", port=8000)
