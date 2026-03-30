from fastapi import FastAPI

app = FastAPI(title="Commerce ROI", version="0.1.0")


@app.get("/health")
async def health():
    return {"status": "ok"}
