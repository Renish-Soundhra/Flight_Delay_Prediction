"""
Build a server-side dashboard SQLite store from the existing engineered
dataset and the EXISTING HistGradientBoosting model.

Does not retrain. Does not change the 68-feature pipeline or threshold.
"""

import argparse
import json
import os
import sqlite3
import sys
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from models.model_loader import ModelLoader  # noqa: E402


DEFAULT_FEATURES_PATH = r"C:\Users\renis\OneDrive\Desktop\Flight_Delay_Prediction\flights_features_v4_2.csv"
DEFAULT_RAW_PATH = r"C:\Users\renis\Downloads\flights.csv\flights.csv"
DEFAULT_DB_PATH = BACKEND_DIR / "artifacts" / "dashboard.sqlite"
CHUNK_SIZE = 80_000
HISTORICAL_YEAR = 2015


def encode_chunk(df, preprocessing):
    feature_columns = preprocessing["feature_columns"]
    categorical_columns = set(preprocessing["categorical_columns"])
    frequency_maps = preprocessing["frequency_maps"]
    missing_key = preprocessing["missing_category_key"]
    unknown_frequency = preprocessing["unknown_category_frequency"]
    dtype = preprocessing.get("feature_dtype", "float32")

    encoded = np.empty((len(df), len(feature_columns)), dtype=dtype)

    for index, column in enumerate(feature_columns):
        series = df[column]
        if column in categorical_columns:
            keys = series.astype("string")
            keys = keys.mask(series.isna(), missing_key)
            mapped = keys.map(frequency_maps.get(column, {}))
            encoded[:, index] = mapped.fillna(unknown_frequency).to_numpy(dtype=dtype)
        else:
            encoded[:, index] = pd.to_numeric(series, errors="coerce").to_numpy(
                dtype=dtype
            )

    return encoded


def hhmm_to_minutes(values):
    numeric = pd.to_numeric(values, errors="coerce")
    return (numeric // 100 * 60 + numeric % 100).to_numpy()


def load_delay_lookup(raw_path):
    lookup = {}
    if not raw_path or not Path(raw_path).exists():
        print("Raw flights file not found; departure/arrival delay columns will be empty.")
        return lookup

    print("Building delay lookup from raw flights file...")
    usecols = [
        "YEAR",
        "MONTH",
        "DAY",
        "AIRLINE",
        "FLIGHT_NUMBER",
        "TAIL_NUMBER",
        "ORIGIN_AIRPORT",
        "DESTINATION_AIRPORT",
        "SCHEDULED_ARRIVAL",
        "DEPARTURE_DELAY",
        "ARRIVAL_DELAY",
        "ARRIVAL_TIME",
    ]
    for chunk in pd.read_csv(raw_path, usecols=usecols, chunksize=200_000, low_memory=True):
        keys = (
            chunk["AIRLINE"].astype(str)
            + "|"
            + chunk["FLIGHT_NUMBER"].astype(str)
            + "|"
            + chunk["TAIL_NUMBER"].astype(str)
            + "|"
            + chunk["ORIGIN_AIRPORT"].astype(str)
            + "|"
            + chunk["DESTINATION_AIRPORT"].astype(str)
            + "|"
            + chunk["MONTH"].astype(str)
            + "|"
            + chunk["DAY"].astype(str)
        )
        years = pd.to_numeric(chunk["YEAR"], errors="coerce").to_numpy()
        dep = pd.to_numeric(chunk["DEPARTURE_DELAY"], errors="coerce").to_numpy()
        arr = pd.to_numeric(chunk["ARRIVAL_DELAY"], errors="coerce").to_numpy()
        sched_arr = hhmm_to_minutes(chunk["SCHEDULED_ARRIVAL"])
        act_arr = hhmm_to_minutes(chunk["ARRIVAL_TIME"])
        for key, year, ddelay, adelay, sarr, aarr in zip(
            keys.to_numpy(), years, dep, arr, sched_arr, act_arr
        ):
            lookup[str(key)] = (year, ddelay, adelay, sarr, aarr)
    print(f"Delay lookup keys: {len(lookup):,}")
    return lookup


def build_timestamps(years, months, days, hours, minutes):
    stamps = []
    for year, month, day, hour, minute in zip(years, months, days, hours, minutes):
        try:
            ts = datetime(int(year), int(month), int(day), int(hour), int(minute))
            stamps.append(ts.isoformat(timespec="minutes"))
        except (ValueError, TypeError):
            stamps.append(None)
    return stamps


def optional_float(values):
    numeric = pd.to_numeric(values, errors="coerce").to_numpy(dtype=np.float64)
    return [None if np.isnan(value) else float(value) for value in numeric]


def optional_int(values):
    numeric = pd.to_numeric(values, errors="coerce").to_numpy(dtype=np.float64)
    return [None if np.isnan(value) else int(value) for value in numeric]


def optional_str(values):
    return [None if pd.isna(value) else str(value) for value in values]


def build_store(features_path, raw_path, db_path, max_rows=None, chunk_size=CHUNK_SIZE):
    loader = ModelLoader()
    if not loader.is_ready:
        raise RuntimeError(loader.load_error or "Existing HistGradientBoosting model is not loaded")

    preprocessing = loader.preprocessing
    model = loader.model
    threshold = float(loader.threshold)
    feature_columns = preprocessing["feature_columns"]
    if len(feature_columns) != 68:
        raise RuntimeError(f"Expected 68 features, found {len(feature_columns)}")

    delay_lookup = load_delay_lookup(raw_path)

    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()

    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA journal_mode=OFF")
    conn.execute("PRAGMA synchronous=OFF")
    conn.execute(
        """
        CREATE TABLE flights (
            id INTEGER PRIMARY KEY,
            flight_number INTEGER,
            airline TEXT,
            airline_name TEXT,
            tail_number TEXT,
            origin TEXT,
            destination TEXT,
            origin_lat REAL,
            origin_lon REAL,
            dest_lat REAL,
            dest_lon REAL,
            scheduled_dep_min INTEGER,
            scheduled_arr_min INTEGER,
            scheduled_time REAL,
            year INTEGER,
            month INTEGER,
            day INTEGER,
            day_of_week INTEGER,
            day_of_year INTEGER,
            week INTEGER,
            scheduled_ts TEXT,
            actual_delayed INTEGER,
            departure_delay REAL,
            arrival_delay REAL,
            actual_arrival_min INTEGER,
            probability REAL,
            prediction INTEGER,
            prev_dep_delay REAL,
            prev_arr_delay REAL,
            time_since_prev REAL,
            scheduled_turnaround REAL,
            remaining_turnaround REAL,
            turnaround_stress REAL,
            buffer_ratio REAL,
            propagation_pressure REAL
        )
        """
    )

    usecols = list(dict.fromkeys(feature_columns + ["target"]))
    inserted = 0
    next_id = 1
    verified = []

    for chunk in pd.read_csv(
        features_path,
        usecols=usecols,
        chunksize=chunk_size,
        low_memory=True,
    ):
        if max_rows is not None and inserted >= max_rows:
            break
        if max_rows is not None:
            remaining = max_rows - inserted
            if len(chunk) > remaining:
                chunk = chunk.iloc[:remaining].copy()

        encoded = encode_chunk(chunk, preprocessing)
        probabilities = model.predict_proba(encoded)[:, 1].astype(np.float32)
        predictions = (probabilities >= threshold).astype(np.int8)

        n = len(chunk)
        if len(verified) < 5:
            for i in range(min(5 - len(verified), n)):
                verified.append(
                    {
                        "id": next_id + i,
                        "airline": str(chunk["AIRLINE"].iloc[i]),
                        "origin": str(chunk["ORIGIN_AIRPORT"].iloc[i]),
                        "destination": str(chunk["DESTINATION_AIRPORT"].iloc[i]),
                        "flight_number": int(chunk["FLIGHT_NUMBER"].iloc[i]),
                        "tail_number": str(chunk["TAIL_NUMBER"].iloc[i]),
                        "probability": float(probabilities[i]),
                        "prediction": int(predictions[i]),
                        "threshold": threshold,
                    }
                )

        join_keys = (
            chunk["AIRLINE"].astype(str)
            + "|"
            + chunk["FLIGHT_NUMBER"].astype(str)
            + "|"
            + chunk["TAIL_NUMBER"].astype(str)
            + "|"
            + chunk["ORIGIN_AIRPORT"].astype(str)
            + "|"
            + chunk["DESTINATION_AIRPORT"].astype(str)
            + "|"
            + chunk["departure_month"].astype(str)
            + "|"
            + chunk["departure_day"].astype(str)
        ).to_numpy()

        years = np.full(n, HISTORICAL_YEAR, dtype=np.float64)
        dep_delay = np.full(n, np.nan)
        arr_delay = np.full(n, np.nan)
        scheduled_arr_min = np.full(n, np.nan)
        actual_arrival_min = np.full(n, np.nan)
        if delay_lookup:
            for i, key in enumerate(join_keys):
                match = delay_lookup.get(str(key))
                if match is None:
                    continue
                year, ddelay, adelay, sarr, aarr = match
                if not np.isnan(year):
                    years[i] = year
                dep_delay[i] = ddelay
                arr_delay[i] = adelay
                scheduled_arr_min[i] = sarr
                actual_arrival_min[i] = aarr

        hours = pd.to_numeric(chunk["departure_hour"], errors="coerce").fillna(0).astype(int).to_numpy()
        minutes = pd.to_numeric(chunk["departure_minute"], errors="coerce").fillna(0).astype(int).to_numpy()
        dep_min = hours * 60 + minutes
        scheduled_time = pd.to_numeric(chunk["SCHEDULED_TIME"], errors="coerce").to_numpy()
        missing_arr = np.isnan(scheduled_arr_min)
        scheduled_arr_min[missing_arr] = (dep_min[missing_arr] + np.nan_to_num(scheduled_time[missing_arr])) % (24 * 60)

        months = pd.to_numeric(chunk["departure_month"], errors="coerce").fillna(1).astype(int).to_numpy()
        days = pd.to_numeric(chunk["departure_day"], errors="coerce").fillna(1).astype(int).to_numpy()
        timestamps = build_timestamps(years, months, days, hours, minutes)

        ids = np.arange(next_id, next_id + n)
        rows = list(
            zip(
                ids.tolist(),
                optional_int(chunk["FLIGHT_NUMBER"]),
                optional_str(chunk["AIRLINE"].to_numpy()),
                optional_str(chunk["AIRLINE_NAME"].to_numpy()),
                optional_str(chunk["TAIL_NUMBER"].to_numpy()),
                optional_str(chunk["ORIGIN_AIRPORT"].to_numpy()),
                optional_str(chunk["DESTINATION_AIRPORT"].to_numpy()),
                optional_float(chunk["origin_latitude"]),
                optional_float(chunk["origin_longitude"]),
                optional_float(chunk["destination_latitude"]),
                optional_float(chunk["destination_longitude"]),
                dep_min.tolist(),
                optional_int(scheduled_arr_min),
                optional_float(chunk["SCHEDULED_TIME"]),
                [int(value) if not np.isnan(value) else HISTORICAL_YEAR for value in years],
                optional_int(chunk["departure_month"]),
                optional_int(chunk["departure_day"]),
                optional_int(chunk["departure_day_of_week"]),
                optional_int(chunk["departure_day_of_year"]),
                optional_int(chunk["departure_week"]),
                timestamps,
                optional_int(chunk["target"]),
                optional_float(dep_delay),
                optional_float(arr_delay),
                optional_int(actual_arrival_min),
                [float(value) for value in probabilities],
                [int(value) for value in predictions],
                optional_float(chunk["previous_flight_departure_delay"]),
                optional_float(chunk["previous_flight_arrival_delay"]),
                optional_float(chunk["time_since_previous_flight_min"]),
                optional_float(chunk["scheduled_turnaround_min"]),
                optional_float(chunk["remaining_turnaround_min"]),
                optional_float(chunk["turnaround_stress_min"]),
                optional_float(chunk["buffer_ratio"]),
                optional_float(chunk["propagation_pressure"]),
            )
        )

        conn.executemany(
            """
            INSERT INTO flights VALUES (
                ?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?
            )
            """,
            rows,
        )
        next_id += n
        inserted += n
        conn.commit()
        print(f"Inserted {inserted:,} flights | threshold={threshold:.6f}")

    conn.execute("CREATE INDEX idx_flights_ts ON flights(scheduled_ts)")
    conn.execute("CREATE INDEX idx_flights_airline ON flights(airline)")
    conn.execute("CREATE INDEX idx_flights_origin ON flights(origin)")
    conn.execute("CREATE INDEX idx_flights_dest ON flights(destination)")
    conn.execute("CREATE INDEX idx_flights_tail ON flights(tail_number)")
    conn.execute("CREATE INDEX idx_flights_prob ON flights(probability)")
    conn.execute("CREATE INDEX idx_flights_pred ON flights(prediction)")
    conn.commit()
    conn.close()

    verify_path = Path(db_path).with_suffix(".verify.json")
    verify_path.write_text(
        json.dumps(
            {
                "rows": inserted,
                "model": loader.model_name,
                "threshold": threshold,
                "features": 68,
                "sample_predictions": verified,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"Wrote {db_path} ({inserted:,} rows)")
    return inserted


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--features-path", default=os.getenv("FLIGHT_FEATURES_PATH", DEFAULT_FEATURES_PATH))
    parser.add_argument("--raw-path", default=os.getenv("FLIGHTS_RAW_PATH", DEFAULT_RAW_PATH))
    parser.add_argument("--db-path", default=str(DEFAULT_DB_PATH))
    parser.add_argument("--max-rows", type=int, default=None)
    parser.add_argument("--chunk-size", type=int, default=CHUNK_SIZE)
    args = parser.parse_args()
    build_store(
        features_path=args.features_path,
        raw_path=args.raw_path,
        db_path=args.db_path,
        max_rows=args.max_rows,
        chunk_size=args.chunk_size,
    )


if __name__ == "__main__":
    main()
