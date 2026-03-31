from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import ads, analysis, auth, costs, events, platforms, products, reports, upload

app = FastAPI(title="Commerce ROI", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:4000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(platforms.router)
app.include_router(products.router)
app.include_router(upload.router)
app.include_router(costs.router)
app.include_router(ads.router)
app.include_router(events.router)
app.include_router(reports.router)
app.include_router(analysis.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
