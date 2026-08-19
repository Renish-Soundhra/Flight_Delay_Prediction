import json
from pathlib import Path

import numpy as np
from sklearn.metrics import precision_recall_curve, roc_curve

from models.model_loader import model_loader

ARTIFACT_DIR = Path(__file__).resolve().parent.parent / "artifacts"
CURVE_CACHE_PATH = ARTIFACT_DIR / "evaluation_curves.json"
CURVE_SAMPLE_PATH = ARTIFACT_DIR / "test_curve_sample.npz"


def _downsample_curve(x, y, max_points=180):
    if len(x) <= max_points:
        return [
            {"x": float(x[i]), "y": float(y[i])}
            for i in range(len(x))
        ]
    indices = np.linspace(0, len(x) - 1, max_points).astype(int)
    return [
        {"x": float(x[i]), "y": float(y[i])}
        for i in indices
    ]


def get_evaluation_curves():
    if CURVE_CACHE_PATH.exists():
        with open(CURVE_CACHE_PATH, "r", encoding="utf-8") as file:
            return json.load(file)

    if not model_loader.is_ready:
        raise RuntimeError(model_loader.load_error or "Prediction model is not loaded")
    if not CURVE_SAMPLE_PATH.exists():
        raise FileNotFoundError(
            "test_curve_sample.npz not found. Curves are computed from a held-out "
            "test sample of the existing HistGradientBoosting evaluation matrices."
        )

    if CURVE_SAMPLE_PATH.is_dir():
        X = np.load(CURVE_SAMPLE_PATH / "X.npy").astype(np.float32)
        y = np.load(CURVE_SAMPLE_PATH / "y.npy").astype(int)
    else:
        data = np.load(CURVE_SAMPLE_PATH)
        X = data["X"].astype(np.float32)
        y = data["y"].astype(int)
    probabilities = model_loader.model.predict_proba(X)[:, 1]
    threshold = float(model_loader.threshold)
    predictions = (probabilities >= threshold).astype(int)

    fpr, tpr, _ = roc_curve(y, probabilities)
    precision, recall, _ = precision_recall_curve(y, probabilities)

    payload = {
        "model_name": model_loader.model_name,
        "evaluation_dataset": "test_sample",
        "evaluation_samples": int(len(y)),
        "threshold": threshold,
        "note": (
            "Headline accuracy/precision/recall/F1/ROC-AUC/PR-AUC remain the saved "
            "full test-set metrics. These curves visualize the same HistGradientBoosting "
            "model on a 30,000-row test subsample."
        ),
        "roc": _downsample_curve(fpr, tpr),
        "pr": _downsample_curve(recall, precision),
        "probability_mean": float(np.mean(probabilities)),
        "predicted_positive_rate": float(predictions.mean()),
        "actual_positive_rate": float(y.mean()),
    }

    CURVE_CACHE_PATH.write_text(json.dumps(payload), encoding="utf-8")
    return payload
