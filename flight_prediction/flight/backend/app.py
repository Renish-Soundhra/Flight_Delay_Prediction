from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.prediction import router as prediction_router
from routes.comparison import router as comparison_router
from routes.metrics import router as metrics_router
from routes.models import router as models_router
from routes.dashboard import router as dashboard_router

app = FastAPI(
    title="Flight Delay Prediction API",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:2000",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(prediction_router, prefix="/api")
app.include_router(comparison_router, prefix="/api")
app.include_router(metrics_router, prefix="/api")
app.include_router(models_router, prefix="/api")
app.include_router(dashboard_router, prefix="/api")


@app.get("/")
def root():
    return {
        "message": "Flight Delay Prediction API is running"
    }


@app.get("/health")
def health():
    from models.model_loader import model_loader

    return {
        "status": "healthy",
        "model_loaded": model_loader.is_ready,
        "model_load_error": model_loader.load_error,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
