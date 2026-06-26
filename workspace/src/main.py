from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def root():
    return {"status": "OK"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", reload=True, host="0.0.0.0", port=8000)
