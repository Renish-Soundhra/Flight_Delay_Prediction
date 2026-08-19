from pydantic import BaseModel
from typing import Dict


class ModelMetrics(BaseModel):
    precision: float
    recall: float
    accuracy: float
    f1_score: float
    roc_auc: float


class ComparisonResponse(BaseModel):
    models: Dict[str, ModelMetrics]
    best_model: str