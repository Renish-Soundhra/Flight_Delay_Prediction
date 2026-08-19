from fastapi import APIRouter, HTTPException

from services.metrics_service import get_model_metrics

router = APIRouter(prefix="/models", tags=["Models"])


@router.get("")
def get_models():
    try:
        return get_model_metrics()
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
