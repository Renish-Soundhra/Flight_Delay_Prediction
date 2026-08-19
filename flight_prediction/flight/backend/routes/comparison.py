from fastapi import APIRouter, HTTPException

from services.metrics_service import get_model_metrics

router = APIRouter()


@router.get("/comparison")
def model_comparison():
    """Legacy endpoint — returns the same real metrics as /api/model/metrics."""
    try:
        return get_model_metrics()
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
