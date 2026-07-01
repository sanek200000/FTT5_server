from fastapi import FastAPI
from fastapi.responses import JSONResponse

from config import logger

from src.utils.generate_tree import save_structure
from src.services.lifespan import lifespan
from src.exceptions import SynthesisException

from src.api.tts import router as router_f5tts
from src.api.whisper import router as router_whisper

app = FastAPI(lifespan=lifespan)
# app = FastAPI()

app.include_router(router_f5tts)
app.include_router(router_whisper)


@app.exception_handler(SynthesisException)
async def synthesis_exception_handler(request, ex):
    return JSONResponse(
        status_code=500,
        content={"error": str(ex)},
    )


if __name__ == "__main__":
    import uvicorn

    logger.info("----------------------START NEW SESSION----------------------")

    # save_structure()
    uvicorn.run("main:app", reload=False, host="0.0.0.0", port=8000)
