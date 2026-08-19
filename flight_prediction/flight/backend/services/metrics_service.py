import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
METRICS_PATH = BASE_DIR / "artifacts" / "model_metrics.json"


def get_model_metrics():
    if not METRICS_PATH.exists():
        raise FileNotFoundError(
            f"model_metrics.json not found at {METRICS_PATH}"
        )

    with open(METRICS_PATH, "r", encoding="utf-8") as file:
        data = json.load(file)

    model_info = data.get("model", {})
    threshold_info = data.get("threshold", {})
    test_metrics = data.get("test_metrics", {})
    dataset = data.get("dataset", {})
    problem = data.get("problem", {})
    confusion_matrix = data.get("confusion_matrix")

    metrics = {}
    for key in ("precision", "recall", "f1_score", "roc_auc", "pr_auc", "accuracy"):
        if key in test_metrics:
            metrics[key] = test_metrics[key]

    response = {
        "model_name": model_info.get("name"),
        "model_type": model_info.get("algorithm"),
        "task": problem.get("name"),
        "target": problem.get("target"),
        "evaluation_dataset": "test",
        "evaluation_samples": dataset.get("test_rows"),
        "threshold": threshold_info.get("selected"),
        "metrics": metrics,
        "confusion_matrix": confusion_matrix,
        "model_loaded": False,
    }

    return response
