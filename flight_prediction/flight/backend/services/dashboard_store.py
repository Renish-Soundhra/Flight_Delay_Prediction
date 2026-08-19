import os
import sqlite3
from functools import lru_cache
from pathlib import Path

ARTIFACT_DIR = Path(__file__).resolve().parent.parent / "artifacts"
DEFAULT_DB_PATH = ARTIFACT_DIR / "dashboard.sqlite"

ML_THRESHOLD = None  # loaded from model at query time; visualization risk is separate

VIZ_RISK_MEDIUM = 0.70
VIZ_RISK_HIGH = 0.90


def dashboard_db_path():
    return Path(os.getenv("DASHBOARD_DB_PATH", str(DEFAULT_DB_PATH)))


def visualization_risk(probability):
    if probability is None:
        return None
    if probability >= VIZ_RISK_HIGH:
        return "HIGH"
    if probability >= VIZ_RISK_MEDIUM:
        return "MEDIUM"
    return "LOW"


@lru_cache(maxsize=1)
def get_connection():
    path = dashboard_db_path()
    if not path.exists():
        raise FileNotFoundError(
            f"Dashboard store not found at {path}. "
            "Run: python scripts/build_dashboard_store.py"
        )
    conn = sqlite3.connect(str(path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def store_ready():
    return dashboard_db_path().exists()
