from models.model_loader import model_loader
from utils.feature_processor import build_features, prepare_model_input


def predict(data):
    if not model_loader.is_ready:
        raise RuntimeError(
            model_loader.load_error or "Prediction model is not loaded"
        )

    features = build_features(data)
    model_input = prepare_model_input(features, model_loader.preprocessing)

    if hasattr(model_loader.model, "predict_proba"):
        probability = float(
            model_loader.model.predict_proba(model_input)[0][1]
        )
    elif hasattr(model_loader.model, "decision_function"):
        probability = float(
            model_loader.model.decision_function(model_input)[0]
        )
    else:
        raw_prediction = model_loader.model.predict(model_input)[0]
        probability = float(raw_prediction)
        return int(raw_prediction), probability

    threshold = model_loader.threshold
    prediction = int(probability >= threshold)

    return prediction, probability
