from fastapi import APIRouter, HTTPException

from schemas.prediction import (
    PredictionRequest,
    PredictionResponse
)

from models.model_loader import model_loader
from services.prediction_service import make_prediction


router = APIRouter(
    prefix="/prediction",
    tags=["Prediction"]
)


@router.post(
    "",
    response_model=PredictionResponse
)
def predict_flight(
    request: PredictionRequest
):
    if not model_loader.is_ready:
        detail = model_loader.load_error or "Prediction model is not loaded"
        raise HTTPException(status_code=503, detail=detail)

    try:
        return make_prediction(request.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
