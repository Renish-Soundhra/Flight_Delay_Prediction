"""
One-time utility to export a stratified test sample for permutation importance.

Usage (from backend directory):
  python scripts/export_test_data.py --flights-path "C:/path/to/flights.csv.zip"
"""

import argparse
import math
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from models.model_loader import ModelLoader
from utils.feature_processor import build_features, prepare_model_input


DELAY_THRESHOLD_MIN = 15
TEST_FRAC = 0.15


def _enrich_delay_rates(features, preprocessing):
    frequency_maps = preprocessing["frequency_maps"]
    unknown = preprocessing["unknown_category_frequency"]

    def lookup(column, key):
        return frequency_maps.get(column, {}).get(str(key), unknown)

    route = features.get("ROUTE")
    airline = features.get("AIRLINE")
    origin = features.get("ORIGIN_AIRPORT")
    destination = features.get("DESTINATION_AIRPORT")

    airline_rate = lookup("AIRLINE", airline)
    origin_rate = lookup("ORIGIN_AIRPORT", origin)
    destination_rate = lookup("DESTINATION_AIRPORT", destination)
    route_rate = lookup("ROUTE", route)
    aircraft_rate = lookup("TAIL_NUMBER", features.get("TAIL_NUMBER", "UNKNOWN"))

    features["airline_delay_rate"] = airline_rate
    features["origin_delay_rate"] = origin_rate
    features["destination_delay_rate"] = destination_rate
    features["route_delay_rate"] = route_rate
    features["aircraft_delay_rate"] = aircraft_rate
    features["route_vs_airline_delay_rate"] = route_rate - airline_rate
    features["origin_vs_airline_delay_rate"] = origin_rate - airline_rate
    features["destination_vs_airline_delay_rate"] = destination_rate - airline_rate

    return features


def _csv_row_to_payload(row):
    scheduled_dep = int(row["SCHEDULED_DEPARTURE"])
    dep_time = int(row["DEPARTURE_TIME"]) if pd.notna(row["DEPARTURE_TIME"]) else scheduled_dep
    scheduled_arr = int(row["SCHEDULED_ARRIVAL"])

    day_of_week = int(row["DAY_OF_WEEK"])
    if day_of_week == 0:
        day_of_week = 7

    return {
        "airline": str(row["AIRLINE"]).upper(),
        "origin": str(row["ORIGIN_AIRPORT"]).upper(),
        "destination": str(row["DESTINATION_AIRPORT"]).upper(),
        "flight_number": int(row["FLIGHT_NUMBER"]),
        "month": int(row["MONTH"]),
        "day_of_month": int(row["DAY"]),
        "day_of_week": day_of_week,
        "scheduled_dep_time": scheduled_dep,
        "dep_time": dep_time,
        "scheduled_arrival_time": scheduled_arr,
        "distance": float(row["DISTANCE"]),
    }


def _read_flights_test_sample(flights_path, test_frac=TEST_FRAC, sample_size=2000, random_state=42):
    path = Path(flights_path)
    usecols = [
        "YEAR", "MONTH", "DAY", "DAY_OF_WEEK", "AIRLINE", "FLIGHT_NUMBER",
        "TAIL_NUMBER", "ORIGIN_AIRPORT", "DESTINATION_AIRPORT",
        "SCHEDULED_DEPARTURE", "DEPARTURE_TIME", "SCHEDULED_ARRIVAL",
        "ARRIVAL_DELAY", "DISTANCE", "CANCELLED", "DIVERTED",
    ]

    if path.suffix == ".zip":
        with zipfile.ZipFile(path) as archive:
            csv_name = next(name for name in archive.namelist() if name.endswith(".csv"))
            csv_handle = archive.open(csv_name)
    else:
        csv_handle = open(path, "rb")

    row_count = 0
    with pd.read_csv(csv_handle, usecols=usecols, chunksize=250_000, low_memory=True) as reader:
        for chunk in reader:
            row_count += len(chunk)

    test_start = int(math.floor(row_count * (1 - test_frac)))

    def _skip_row(row_index):
        return row_index != 0 and row_index <= test_start

    if path.suffix == ".zip":
        with zipfile.ZipFile(path) as archive:
            csv_name = next(name for name in archive.namelist() if name.endswith(".csv"))
            csv_handle = archive.open(csv_name)
    else:
        csv_handle = open(path, "rb")

    test_frames = []
    with pd.read_csv(
        csv_handle,
        usecols=usecols,
        skiprows=_skip_row,
        chunksize=250_000,
        low_memory=True,
    ) as reader:
        for chunk in reader:
            test_frames.append(chunk)

    test_df = pd.concat(test_frames, ignore_index=True)
    test_df = test_df[(test_df["CANCELLED"] == 0) & (test_df["DIVERTED"] == 0)].copy()
    test_df["IS_DELAYED"] = (test_df["ARRIVAL_DELAY"] > DELAY_THRESHOLD_MIN).astype(int)

    if len(test_df) > sample_size:
        sampled_parts = []
        for _, group in test_df.groupby("IS_DELAYED"):
            part_size = max(1, int(sample_size * len(group) / len(test_df)))
            sampled_parts.append(group.sample(n=min(part_size, len(group)), random_state=random_state))
        test_df = pd.concat(sampled_parts, ignore_index=True).head(sample_size)

    return test_df


def export_test_data(
    flights_path,
    output_path,
    sample_size=2000,
    random_state=42,
):
    test_df = _read_flights_test_sample(
        flights_path,
        sample_size=sample_size,
        random_state=random_state,
    )

    loader = ModelLoader()
    if loader.preprocessing is None:
        raise RuntimeError("Preprocessing artifact is not loaded")

    rows = []
    labels = []

    for _, row in test_df.iterrows():
        payload = _csv_row_to_payload(row)
        features = build_features(payload)
        features = _enrich_delay_rates(features, loader.preprocessing)
        encoded = prepare_model_input(features, loader.preprocessing)[0]
        rows.append(encoded)
        labels.append(int(row["IS_DELAYED"]))

    X = np.asarray(rows, dtype=np.float32)
    y = np.asarray(labels, dtype=np.int8)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(output_path, X=X, y=y)

    return {
        "output_path": str(output_path),
        "rows": len(y),
        "positive_rate": float(y.mean()),
        "test_period_rows": len(test_df),
    }


def main():
    parser = argparse.ArgumentParser(description="Export test_data.npz for permutation importance")
    parser.add_argument(
        "--flights-path",
        required=True,
        help="Path to flights.csv or flights.csv.zip",
    )
    parser.add_argument(
        "--output-path",
        default=str(Path(__file__).resolve().parent.parent / "artifacts" / "test_data.npz"),
    )
    parser.add_argument("--sample-size", type=int, default=2000)
    args = parser.parse_args()

    summary = export_test_data(
        flights_path=args.flights_path,
        output_path=args.output_path,
        sample_size=args.sample_size,
    )
    print(summary)


if __name__ == "__main__":
    main()
