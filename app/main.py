from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import deposits_router, health_router

app = FastAPI(
    title="Deposits API",
    description="API для подбора вкладов и расчета итоговой доходности",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "message": "Deposits API is running",
        "docs": "/docs",
        "health": "/health",
        "catalog": "/api/deposits",
        "search": "/api/deposits/search",
        "calculate": "/api/deposits/calculate",
        "stats": "/api/deposits/stats",
    }

app.include_router(health_router)
app.include_router(deposits_router)