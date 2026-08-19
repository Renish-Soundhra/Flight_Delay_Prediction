from typing import List, Optional

from pydantic import BaseModel, Field


class PredictionRequest(BaseModel):
    airline: str
    origin: str
    destination: str
    flight_number: int = Field(gt=0)
    month: int = Field(ge=1, le=12)
    day_of_month: int = Field(ge=1, le=31)
    day_of_week: int = Field(ge=1, le=7)
    scheduled_dep_time: float = Field(ge=0, le=2359)
    scheduled_arrival_time: float = Field(ge=0, le=2359)
    distance: float = Field(gt=0)


class ContributingFactor(BaseModel):
    feature: str
    label: str
    importance: float
    contribution: float
    explanation: str


class PredictionInsights(BaseModel):
    delay_probability: float
    on_time_probability: float
    contributing_factors: List[ContributingFactor]
    explanation_available: bool
    message: Optional[str] = None


class PredictionResponse(BaseModel):
    prediction: int
    status: str
    probability: float
    model: str
    insights: Optional[PredictionInsights] = None
