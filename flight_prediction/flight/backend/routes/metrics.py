from fastapi import APIRouter, HTTPException

from models.model_loader import model_loader
from services.metrics_service import get_model_metrics
from services.insights_service import get_global_feature_importance

router = APIRouter(prefix="/model", tags=["Model"])


@router.get("/metrics")
def model_metrics():
    try:
        payload = get_model_metrics()
        payload["model_loaded"] = model_loader.is_ready
        if model_loader.load_error:
            payload["model_load_error"] = model_loader.load_error
        return payload
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/feature-importance")
def model_feature_importance():
    if not model_loader.is_ready:
        detail = model_loader.load_error or "Prediction model is not loaded"
        raise HTTPException(status_code=503, detail=detail)

    try:
        return get_global_feature_importance(top_n=68)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e