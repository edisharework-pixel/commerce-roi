from fastapi import FastAPI

from app.routers import auth, platforms, products

app = FastAPI(title="Commerce ROI", version="0.1.0")
app.include_router(auth.router)
app.include_router(platforms.router)
app.include_router(products.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
