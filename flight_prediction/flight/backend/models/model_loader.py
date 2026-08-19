from pathlib import Path
import json
import joblib
import sklearn


BASE_DIR = Path(__file__).resolve().parent.parent
ARTIFACT_DIR = BASE_DIR / "artifacts"
PREPROCESSING_CANDIDATES = (
    ARTIFACT_DIR / "preprocessing.pkl",
    ARTIFACT_DIR / "preprocessor.pkl",
)


class ModelLoader:
    def __init__(self):
        self.model = None
        self.preprocessing = None
        self.metrics_data = None
        self.model_name = None
        self.model_type = None
        self.threshold = 0.5
        self.load_error = None
        self.load()

    def load(self):
        model_path = ARTIFACT_DIR / "model.pkl"
        metrics_path = ARTIFACT_DIR / "model_metrics.json"

        if not metrics_path.exists():
            raise FileNotFoundError(
                f"Metrics file not found: {metrics_path}"
            )

        with open(metrics_path, "r", encoding="utf-8") as file:
            self.metrics_data = json.load(file)

        model_info = self.metrics_data.get("model", {})
        self.model_name = model_info.get("name")
        self.model_type = model_info.get("algorithm")

        threshold_info = self.metrics_data.get("threshold", {})
        selected_threshold = threshold_info.get("selected")
        if selected_threshold is not None:
            self.threshold = float(selected_threshold)

        for preprocessing_path in PREPROCESSING_CANDIDATES:
            if preprocessing_path.exists():
                self.preprocessing = joblib.load(preprocessing_path)
                if isinstance(self.preprocessing, dict):
                    artifact_threshold = self.preprocessing.get("threshold")
                    if artifact_threshold is not None:
                        self.threshold = float(artifact_threshold)
                break

        if not model_path.exists():
            self.load_error = f"Model file not found: {model_path}"
            return

        if self.preprocessing is None:
            self.load_error = (
                "Preprocessing artifact not found. Expected one of: "
                + ", ".join(str(path) for path in PREPROCESSING_CANDIDATES)
            )
            return

        try:
            self.model = joblib.load(model_path)
        except Exception as e:
            self.load_error = (
                f"Failed to load ML artifacts with "
                f"scikit-learn {sklearn.__version__}: {e}"
            )

    @property
    def is_ready(self):
        return (
            self.model is not None
            and self.preprocessing is not None
            and self.load_error is None
        )


model_loader = ModelLoader()
