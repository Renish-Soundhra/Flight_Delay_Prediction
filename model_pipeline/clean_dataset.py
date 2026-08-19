import pandas as pd
import numpy as np
import os

# ============================================================
# CONFIG
# ============================================================

INPUT_PATH = r"C:\Users\ASUS\Downloads\archive (2)\flights.csv"

OUTPUT_PATH = r"D:\Cognizant\flights_clean.csv"

CHUNK_SIZE = 250_000


# ============================================================
# COLUMNS WE NEED
# ============================================================

USE_COLS = [
    "YEAR",
    "MONTH",
    "DAY",
    "DAY_OF_WEEK",

    "AIRLINE",
    "FLIGHT_NUMBER",
    "TAIL_NUMBER",

    "ORIGIN_AIRPORT",
    "DESTINATION_AIRPORT",

    "SCHEDULED_DEPARTURE",
    "DEPARTURE_TIME",
    "DEPARTURE_DELAY",

    "SCHEDULED_ARRIVAL",
    "ARRIVAL_TIME",
    "ARRIVAL_DELAY",

    "SCHEDULED_TIME",
    "DISTANCE",

    "CANCELLED",
    "DIVERTED"
]


# ============================================================
# DATA TYPES
# ============================================================

DTYPES = {
    "AIRLINE": "string",
    "TAIL_NUMBER": "string",
    "ORIGIN_AIRPORT": "string",
    "DESTINATION_AIRPORT": "string"
}


# ============================================================
# HHMM → MINUTES
# ============================================================

def hhmm_to_minutes(series):

    series = pd.to_numeric(
        series,
        errors="coerce"
    )

    hours = series // 100
    minutes = series % 100

    # Invalid HHMM values
    invalid = (
        (minutes >= 60) |
        (hours >= 24)
    )

    result = hours * 60 + minutes

    result[invalid] = np.nan

    return result


# ============================================================
# PROCESS CHUNK
# ============================================================

def process_chunk(df):

    # --------------------------------------------------------
    # Keep normal flights
    # --------------------------------------------------------

    df = df[
        (df["CANCELLED"] == 0) &
        (df["DIVERTED"] == 0)
    ].copy()

    # --------------------------------------------------------
    # Remove records without arrival delay
    # --------------------------------------------------------

    df = df[
        df["ARRIVAL_DELAY"].notna()
    ].copy()

    # --------------------------------------------------------
    # Normalize categorical strings
    # --------------------------------------------------------

    categorical_cols = [
        "AIRLINE",
        "TAIL_NUMBER",
        "ORIGIN_AIRPORT",
        "DESTINATION_AIRPORT"
    ]

    for col in categorical_cols:
        df[col] = df[col].astype("string").str.strip()

    # --------------------------------------------------------
    # Create date
    # --------------------------------------------------------

    df["flight_date"] = pd.to_datetime(
        dict(
            year=df["YEAR"],
            month=df["MONTH"],
            day=df["DAY"]
        ),
        errors="coerce"
    )

    # --------------------------------------------------------
    # Convert scheduled times
    # --------------------------------------------------------

    dep_min = hhmm_to_minutes(
        df["SCHEDULED_DEPARTURE"]
    )

    arr_min = hhmm_to_minutes(
        df["SCHEDULED_ARRIVAL"]
    )

    # --------------------------------------------------------
    # Scheduled departure timestamp
    # --------------------------------------------------------

    df["scheduled_departure_ts"] = (
        df["flight_date"] +
        pd.to_timedelta(
            dep_min,
            unit="m"
        )
    )

    # --------------------------------------------------------
    # Scheduled arrival timestamp
    # --------------------------------------------------------

    df["scheduled_arrival_ts"] = (
        df["flight_date"] +
        pd.to_timedelta(
            arr_min,
            unit="m"
        )
    )

    # --------------------------------------------------------
    # Midnight crossing
    # --------------------------------------------------------

    crosses_midnight = (
        arr_min < dep_min
    )

    df.loc[
        crosses_midnight,
        "scheduled_arrival_ts"
    ] += pd.Timedelta(days=1)

    # --------------------------------------------------------
    # Actual departure
    # --------------------------------------------------------

    actual_dep_min = hhmm_to_minutes(
        df["DEPARTURE_TIME"]
    )

    df["actual_departure_ts"] = (
        df["flight_date"] +
        pd.to_timedelta(
            actual_dep_min,
            unit="m"
        )
    )

    # --------------------------------------------------------
    # Actual arrival
    # --------------------------------------------------------

    actual_arr_min = hhmm_to_minutes(
        df["ARRIVAL_TIME"]
    )

    df["actual_arrival_ts"] = (
        df["flight_date"] +
        pd.to_timedelta(
            actual_arr_min,
            unit="m"
        )
    )

    # --------------------------------------------------------
    # Actual midnight crossing
    # --------------------------------------------------------

    actual_cross_midnight = (
        (actual_arr_min < actual_dep_min) &
        actual_dep_min.notna() &
        actual_arr_min.notna()
    )

    df.loc[
        actual_cross_midnight,
        "actual_arrival_ts"
    ] += pd.Timedelta(days=1)

    # --------------------------------------------------------
    # Time features
    # --------------------------------------------------------

    df["departure_hour"] = (
        dep_min // 60
    )

    df["departure_minute"] = (
        dep_min % 60
    )

    df["is_weekend"] = (
        df["DAY_OF_WEEK"].isin([6, 7])
    ).astype("int8")

    # --------------------------------------------------------
    # Cyclical hour
    # --------------------------------------------------------

    df["departure_hour_sin"] = np.sin(
        2 * np.pi *
        df["departure_hour"] / 24
    )

    df["departure_hour_cos"] = np.cos(
        2 * np.pi *
        df["departure_hour"] / 24
    )

    # --------------------------------------------------------
    # Cyclical day of week
    # --------------------------------------------------------

    df["day_of_week_sin"] = np.sin(
        2 * np.pi *
        (df["DAY_OF_WEEK"] - 1) / 7
    )

    df["day_of_week_cos"] = np.cos(
        2 * np.pi *
        (df["DAY_OF_WEEK"] - 1) / 7
    )

    # --------------------------------------------------------
    # Target
    # --------------------------------------------------------

    df["target"] = (
        df["ARRIVAL_DELAY"] > 15
    ).astype("int8")

    # --------------------------------------------------------
    # Final columns
    # --------------------------------------------------------

    final_cols = [

        # Identification
        "flight_date",
        "AIRLINE",
        "FLIGHT_NUMBER",
        "TAIL_NUMBER",
        "ORIGIN_AIRPORT",
        "DESTINATION_AIRPORT",

        # Scheduled information
        "scheduled_departure_ts",
        "scheduled_arrival_ts",
        "SCHEDULED_TIME",
        "DISTANCE",

        # Actual information
        "actual_departure_ts",
        "actual_arrival_ts",
        "DEPARTURE_DELAY",

        # Time features
        "departure_hour",
        "departure_minute",
        "is_weekend",

        "departure_hour_sin",
        "departure_hour_cos",

        "day_of_week_sin",
        "day_of_week_cos",

        # Target
        "target"
    ]

    return df[final_cols]


# ============================================================
# MAIN
# ============================================================

print("=" * 60)
print("STEP 2 — CLEANING + TIME PREPROCESSING")
print("=" * 60)

if os.path.exists(OUTPUT_PATH):
    os.remove(OUTPUT_PATH)

total_processed = 0
first_chunk = True

for chunk_no, chunk in enumerate(
    pd.read_csv(
        INPUT_PATH,
        usecols=USE_COLS,
        dtype=DTYPES,
        chunksize=CHUNK_SIZE,
        low_memory=False
    ),
    start=1
):

    processed = process_chunk(chunk)

    processed.to_csv(
        OUTPUT_PATH,
        mode="w" if first_chunk else "a",
        header=first_chunk,
        index=False
    )

    total_processed += len(processed)

    first_chunk = False

    print(
        f"Chunk {chunk_no:02d} | "
        f"Processed: {total_processed:,}"
    )


print("\n" + "=" * 60)
print("STEP 2 COMPLETE")
print("=" * 60)

print(
    f"Clean flights: {total_processed:,}"
)

print(
    f"Saved to:\n{OUTPUT_PATH}"
)