import os
from pathlib import Path

import numpy as np

ARTIFACT_DIR = Path(__file__).resolve().parent.parent / "artifacts"


def _subsample(X, y, max_samples, random_state=42):
    if max_samples is None or len(y) <= max_samples:
        return X, y

    rng = np.random.default_rng(random_state)
    positive_idx = np.flatnonzero(y == 1)
    negative_idx = np.flatnonzero(y == 0)

    positive_rate = len(positive_idx) / len(y)
    positive_count = max(1, int(max_samples * positive_rate))
    negative_count = max_samples - positive_count

    positive_sample = rng.choice(
        positive_idx,
        size=min(positive_count, len(positive_idx)),
        replace=False,
    )
    negative_sample = rng.choice(
        negative_idx,
        size=min(negative_count, len(negative_idx)),
        replace=False,
    )
    sample_idx = np.concatenate([positive_sample, negative_sample])
    rng.shuffle(sample_idx)
    return X[sample_idx], y[sample_idx]


def load_test_data(max_samples=2000, random_state=42, prefer_permutation_sample=False):
    env_path = os.getenv("TEST_DATA_PATH")
    if env_path:
        path = Path(env_path)
        if not path.exists():
            raise FileNotFoundError(f"TEST_DATA_PATH not found: {path}")
        if path.suffix != ".npz":
            raise FileNotFoundError(f"Unsupported TEST_DATA_PATH format: {path}")
        data = np.load(path)
        X = data["X"].astype(np.float32)
        y = data["y"].astype(int)
        return _subsample(X, y, max_samples, random_state)

    permutation_path = ARTIFACT_DIR / "permutation_sample.npz"
    if prefer_permutation_sample and permutation_path.exists():
        data = np.load(permutation_path)
        X = data["X"].astype(np.float32)
        y = data["y"].astype(int)
        return _subsample(X, y, max_samples, random_state)

    npz_path = ARTIFACT_DIR / "test_data.npz"
    if npz_path.exists():
        data = np.load(npz_path)
        X = data["X"].astype(np.float32)
        y = data["y"].astype(int)
        return _subsample(X, y, max_samples, random_state)

    x_path = ARTIFACT_DIR / "X_test.npy"
    y_path = ARTIFACT_DIR / "y_test.npy"
    if x_path.exists() and y_path.exists():
        X = np.load(x_path).astype(np.float32)
        y = np.load(y_path).astype(int)
        return _subsample(X, y, max_samples, random_state)

    raise FileNotFoundError(
        "Test evaluation data not found. Expected artifacts/test_data.npz with "
        "arrays 'X' and 'y', or set TEST_DATA_PATH to a compatible .npz file."
    )


def get_test_feature_baselines(max_samples=2000):
    X, _ = load_test_data(max_samples=max_samples)
    return np.median(X, axis=0)
