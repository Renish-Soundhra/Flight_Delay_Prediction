from models.predictor import predict
from models.model_loader import model_loader
from services.insights_service import get_prediction_insights


def make_prediction(data):
    prediction, probability = predict(data)

    if prediction == 1:
        status = "Delayed"
    else:
        status = "On Time"

    insights = get_prediction_insights(data, probability)

    return {
        "prediction": prediction,
        "status": status,
        "probability": round(probability, 4),
        "model": model_loader.model_name or "Unknown",
        "insights": insights,
    }
