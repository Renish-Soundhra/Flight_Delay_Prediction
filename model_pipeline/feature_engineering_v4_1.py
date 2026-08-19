# =============================================================================
# STEP 14.1 — LEAKAGE-SAFE FEATURE ENGINEERING V4.1
#
# FINAL REBUILD FROM ORIGINAL DATASET
#
# FEATURES:
#   - Time features
#   - Cyclical time features
#   - Flight characteristics
#   - Airport metadata
#   - Airline metadata
#   - Geographic route distance
#   - Corrected aircraft rotation
#   - Aircraft historical statistics
#   - Airline historical statistics
#   - Route historical statistics
#   - Origin historical statistics
#   - Destination historical statistics
#   - Comparative historical statistics
#
# REMOVED:
#   - Airport traffic features
#
# OUTPUT:
#   D:\Cognizant\flights_features_v4_1.csv
#
# IMPORTANT:
#   This script starts from flights_clean.csv.
#   It does NOT use flights_features_v4.csv.
# =============================================================================

import os
import warnings
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")


# =============================================================================
# PATHS
# =============================================================================

FLIGHTS_PATH = r"D:\Cognizant\flights_clean.csv"

AIRPORTS_PATH = (
    r"C:\Users\ASUS\Downloads\archive (2)\airports.csv"
)

AIRLINES_PATH = (
    r"C:\Users\ASUS\Downloads\archive (2)\airlines.csv"
)

AIRPORT_MAPPING_PATH = (
    r"D:\Cognizant\airport_id_mapping_final.csv"
)

OUTPUT_PATH = (
    r"D:\Cognizant\flights_features_v4_1.csv"
)

FEATURE_LIST_PATH = (
    r"D:\Cognizant\feature_v4_1_list.txt"
)

TARGET = "target"

EXPECTED_ROWS = 5_714_008

MAX_ROTATION_GAP_MIN = 1440


# =============================================================================
# HELPER
# =============================================================================

def section(title):

    print()
    print("=" * 80)
    print(title)
    print("=" * 80)


def haversine_km(
    lat1,
    lon1,
    lat2,
    lon2
):

    lat1 = np.radians(lat1)
    lon1 = np.radians(lon1)

    lat2 = np.radians(lat2)
    lon2 = np.radians(lon2)

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = (
        np.sin(dlat / 2) ** 2
        +
        np.cos(lat1)
        * np.cos(lat2)
        * np.sin(dlon / 2) ** 2
    )

    a = np.clip(a, 0, 1)

    return (
        6371.0
        * 2
        * np.arctan2(
            np.sqrt(a),
            np.sqrt(1 - a)
        )
    )


def add_history(
    df,
    group_col,
    prefix
):

    # Number of PREVIOUS flights only
    past_count = (
        df.groupby(
            group_col,
            sort=False
        )
        .cumcount()
        .astype(np.float32)
    )

    # Target
    target_values = (
        df[TARGET]
        .fillna(0)
        .astype(np.float32)
    )

    cumulative_target = (
        target_values
        .groupby(
            df[group_col],
            sort=False
        )
        .cumsum()
    )

    previous_target_sum = (
        cumulative_target
        - target_values
    )

    delay_rate = (
        previous_target_sum
        /
        past_count.replace(
            0,
            np.nan
        )
    )

    # Departure delay
    delay_values = (
        pd.to_numeric(
            df["DEPARTURE_DELAY"],
            errors="coerce"
        )
        .fillna(0)
        .astype(np.float32)
    )

    cumulative_delay = (
        delay_values
        .groupby(
            df[group_col],
            sort=False
        )
        .cumsum()
    )

    previous_delay_sum = (
        cumulative_delay
        - delay_values
    )

    average_delay = (
        previous_delay_sum
        /
        past_count.replace(
            0,
            np.nan
        )
    )

    df[
        f"{prefix}_past_flights"
    ] = past_count

    df[
        f"{prefix}_delay_rate"
    ] = delay_rate.astype(np.float32)

    df[
        f"{prefix}_avg_departure_delay"
    ] = average_delay.astype(np.float32)

    return df


# =============================================================================
# START
# =============================================================================

section(
    "STEP 14.1 — LEAKAGE-SAFE FEATURE ENGINEERING V4.1"
)

print("FINAL REBUILD FROM ORIGINAL FLIGHT DATA")
print("Airport traffic features: REMOVED")
print("Aircraft rotation: CORRECTED")
print("Target leakage: EXCLUDED")


# =============================================================================
# CHECK FILES
# =============================================================================

section("CHECKING INPUT FILES")

paths = {
    "Flight dataset": FLIGHTS_PATH,
    "Airport metadata": AIRPORTS_PATH,
    "Airline metadata": AIRLINES_PATH,
    "Airport mapping": AIRPORT_MAPPING_PATH
}

for name, path in paths.items():

    if not os.path.exists(path):

        raise FileNotFoundError(
            f"{name} not found:\n{path}"
        )

    print(
        f"{name}: ✓"
    )


# =============================================================================
# LOAD FLIGHT DATA
# =============================================================================

section(
    "LOADING ORIGINAL FLIGHT DATA"
)

df = pd.read_csv(
    FLIGHTS_PATH,
    low_memory=False
)

print(
    "Rows loaded    :",
    f"{len(df):,}"
)

print(
    "Columns loaded :",
    len(df.columns)
)

if len(df) != EXPECTED_ROWS:

    raise ValueError(
        f"Expected {EXPECTED_ROWS:,} rows "
        f"but found {len(df):,}"
    )

print(
    "Expected row count confirmed. ✓"
)


# =============================================================================
# REQUIRED COLUMNS
# =============================================================================

required = [

    "flight_date",
    "AIRLINE",
    "FLIGHT_NUMBER",
    "TAIL_NUMBER",
    "ORIGIN_AIRPORT",
    "DESTINATION_AIRPORT",
    "scheduled_departure_ts",
    "scheduled_arrival_ts",
    "SCHEDULED_TIME",
    "DISTANCE",
    "actual_departure_ts",
    "actual_arrival_ts",
    "DEPARTURE_DELAY",
    "target"
]

missing = [
    c
    for c in required
    if c not in df.columns
]

if missing:

    raise ValueError(
        "Missing required columns:\n"
        +
        "\n".join(missing)
    )

print(
    "Required flight columns available. ✓"
)


# =============================================================================
# CLEAN CATEGORICALS
# =============================================================================

section(
    "CLEANING CATEGORICAL COLUMNS"
)

for col in [

    "AIRLINE",
    "TAIL_NUMBER",
    "ORIGIN_AIRPORT",
    "DESTINATION_AIRPORT"

]:

    df[col] = (
        df[col]
        .astype("string")
        .str.strip()
        .str.upper()
    )


# =============================================================================
# TARGET
# =============================================================================

df[TARGET] = (
    pd.to_numeric(
        df[TARGET],
        errors="coerce"
    )
    .fillna(0)
    .astype(np.int8)
)


# =============================================================================
# AIRPORT MAPPING
# =============================================================================

section(
    "LOADING VERIFIED AIRPORT ID MAPPING"
)

mapping = pd.read_csv(
    AIRPORT_MAPPING_PATH,
    dtype="string"
)

mapping["AIRPORT_ID"] = (
    mapping["AIRPORT_ID"]
    .astype("string")
    .str.strip()
    .str.upper()
)

mapping["IATA_CODE"] = (
    mapping["IATA_CODE"]
    .astype("string")
    .str.strip()
    .str.upper()
)

mapping = mapping.drop_duplicates(
    "AIRPORT_ID"
)

mapping_dict = dict(
    zip(
        mapping["AIRPORT_ID"],
        mapping["IATA_CODE"]
    )
)

print(
    "Mapping rows:",
    len(mapping)
)


# =============================================================================
# NORMALIZE AIRPORT IDENTIFIERS
# =============================================================================

section(
    "NORMALIZING AIRPORT IDENTIFIERS"
)

for col in [

    "ORIGIN_AIRPORT",
    "DESTINATION_AIRPORT"

]:

    mapped = df[col].map(
        mapping_dict
    )

    df[col] = (
        mapped
        .fillna(df[col])
        .astype("string")
        .str.strip()
        .str.upper()
    )


# =============================================================================
# AIRPORT METADATA
# =============================================================================

section(
    "LOADING AIRPORT METADATA"
)

airports = pd.read_csv(
    AIRPORTS_PATH,
    low_memory=False
)

airports["IATA_CODE"] = (
    airports["IATA_CODE"]
    .astype("string")
    .str.strip()
    .str.upper()
)

airports = airports.drop_duplicates(
    "IATA_CODE"
)

print(
    "Airport rows:",
    len(airports)
)


airport_lookup = airports.set_index(
    "IATA_CODE"
)

state_map = airport_lookup["STATE"]

lat_map = airport_lookup["LATITUDE"]

lon_map = airport_lookup["LONGITUDE"]


origin_known = (
    df["ORIGIN_AIRPORT"]
    .isin(
        airports["IATA_CODE"]
    )
)

destination_known = (
    df["DESTINATION_AIRPORT"]
    .isin(
        airports["IATA_CODE"]
    )
)

print(
    "Origin unmapped:",
    (~origin_known).sum()
)

print(
    "Destination unmapped:",
    (~destination_known).sum()
)

if (~origin_known).sum() > 0:

    raise ValueError(
        "Some origin airports remain unmapped."
    )

if (~destination_known).sum() > 0:

    raise ValueError(
        "Some destination airports remain unmapped."
    )


# =============================================================================
# AIRPORT FEATURES
# =============================================================================

section(
    "ADDING AIRPORT METADATA"
)

df["origin_state"] = (
    df["ORIGIN_AIRPORT"]
    .map(state_map)
    .astype("string")
)

df["destination_state"] = (
    df["DESTINATION_AIRPORT"]
    .map(state_map)
    .astype("string")
)

df["origin_latitude"] = pd.to_numeric(
    df["ORIGIN_AIRPORT"].map(lat_map),
    errors="coerce"
).astype(np.float32)

df["origin_longitude"] = pd.to_numeric(
    df["ORIGIN_AIRPORT"].map(lon_map),
    errors="coerce"
).astype(np.float32)

df["destination_latitude"] = pd.to_numeric(
    df["DESTINATION_AIRPORT"].map(lat_map),
    errors="coerce"
).astype(np.float32)

df["destination_longitude"] = pd.to_numeric(
    df["DESTINATION_AIRPORT"].map(lon_map),
    errors="coerce"
).astype(np.float32)


# =============================================================================
# AIRLINE METADATA
# =============================================================================

section(
    "LOADING AIRLINE METADATA"
)

airlines = pd.read_csv(
    AIRLINES_PATH,
    low_memory=False
)

airlines["IATA_CODE"] = (
    airlines["IATA_CODE"]
    .astype("string")
    .str.strip()
    .str.upper()
)

airline_map = dict(
    zip(
        airlines["IATA_CODE"],
        airlines["AIRLINE"]
    )
)

df["AIRLINE_NAME"] = (
    df["AIRLINE"]
    .map(airline_map)
    .astype("string")
)

print(
    "Airline rows:",
    len(airlines)
)


# =============================================================================
# TIMESTAMPS
# =============================================================================

section(
    "CONVERTING TIMESTAMPS"
)

timestamp_columns = [

    "scheduled_departure_ts",
    "scheduled_arrival_ts",
    "actual_departure_ts",
    "actual_arrival_ts"

]

for col in timestamp_columns:

    df[col] = pd.to_datetime(
        df[col],
        errors="coerce"
    )

    print(
        f"{col}: "
        f"{df[col].notna().sum():,} valid / "
        f"{df[col].isna().sum():,} missing"
    )


# =============================================================================
# SORT CHRONOLOGICALLY
# =============================================================================

section(
    "SORTING CHRONOLOGICALLY"
)

df = df.sort_values(
    "scheduled_departure_ts",
    kind="mergesort"
).reset_index(
    drop=True
)

print(
    "Chronological sorting complete. ✓"
)


# =============================================================================
# TIME FEATURES
# =============================================================================

section(
    "CREATING TIME FEATURES"
)

sd = df["scheduled_departure_ts"]

df["departure_hour"] = (
    sd.dt.hour
    .fillna(0)
    .astype(np.int8)
)

df["departure_minute"] = (
    sd.dt.minute
    .fillna(0)
    .astype(np.int8)
)

df["departure_day_of_week"] = (
    sd.dt.dayofweek
    .fillna(0)
    .astype(np.int8)
)

df["departure_day"] = (
    sd.dt.day
    .fillna(0)
    .astype(np.int8)
)

df["departure_month"] = (
    sd.dt.month
    .fillna(0)
    .astype(np.int8)
)

df["departure_day_of_year"] = (
    sd.dt.dayofyear
    .fillna(0)
    .astype(np.int16)
)

df["departure_week"] = (
    sd.dt.isocalendar()
    .week
    .fillna(0)
    .astype(np.int16)
)

df["is_weekend"] = (
    df["departure_day_of_week"] >= 5
).astype(np.int8)


# =============================================================================
# CYCLICAL TIME
# =============================================================================

section(
    "CREATING CYCLICAL TIME FEATURES"
)

df["departure_hour_sin"] = (
    np.sin(
        2 * np.pi
        * df["departure_hour"]
        / 24
    )
).astype(np.float32)

df["departure_hour_cos"] = (
    np.cos(
        2 * np.pi
        * df["departure_hour"]
        / 24
    )
).astype(np.float32)

df["day_of_week_sin"] = (
    np.sin(
        2 * np.pi
        * df["departure_day_of_week"]
        / 7
    )
).astype(np.float32)

df["day_of_week_cos"] = (
    np.cos(
        2 * np.pi
        * df["departure_day_of_week"]
        / 7
    )
).astype(np.float32)


# =============================================================================
# FLIGHT CHARACTERISTICS
# =============================================================================

section(
    "CREATING FLIGHT CHARACTERISTICS"
)

df["SCHEDULED_TIME"] = pd.to_numeric(
    df["SCHEDULED_TIME"],
    errors="coerce"
)

df["DISTANCE"] = pd.to_numeric(
    df["DISTANCE"],
    errors="coerce"
)

df["distance_per_scheduled_min"] = (
    df["DISTANCE"]
    /
    df["SCHEDULED_TIME"].replace(
        0,
        np.nan
    )
).astype(np.float32)

df["scheduled_speed_proxy"] = (
    df["DISTANCE"]
    /
    (
        df["SCHEDULED_TIME"] / 60
    ).replace(
        0,
        np.nan
    )
).astype(np.float32)

df["same_state"] = (
    df["origin_state"]
    ==
    df["destination_state"]
).astype(np.int8)


# =============================================================================
# ROUTE
# =============================================================================

section(
    "CREATING ROUTE IDENTIFIER"
)

df["ROUTE"] = (
    df["ORIGIN_AIRPORT"]
    +
    "_"
    +
    df["DESTINATION_AIRPORT"]
)


# =============================================================================
# GEOGRAPHIC DISTANCE
# =============================================================================

section(
    "CALCULATING GEOGRAPHIC ROUTE DISTANCE"
)

df["route_geographic_distance_km"] = (
    haversine_km(
        df["origin_latitude"],
        df["origin_longitude"],
        df["destination_latitude"],
        df["destination_longitude"]
    )
).astype(np.float32)

print(
    "Geographic distance created. ✓"
)


# =============================================================================
# AIRCRAFT ROTATION — CORRECTED
# =============================================================================

section(
    "CREATING CORRECTED AIRCRAFT ROTATION FEATURES"
)

tail_group = df.groupby(
    "TAIL_NUMBER",
    sort=False
)

previous_actual_arrival = (
    tail_group["actual_arrival_ts"]
    .shift(1)
)

previous_scheduled_arrival = (
    tail_group["scheduled_arrival_ts"]
    .shift(1)
)

previous_departure_delay = (
    tail_group["DEPARTURE_DELAY"]
    .shift(1)
)

previous_target = (
    tail_group[TARGET]
    .shift(1)
)


# -------------------------------------------------------------------------
# RAW VALUES
# -------------------------------------------------------------------------

raw_scheduled_turnaround = (
    (
        df["scheduled_departure_ts"]
        -
        previous_scheduled_arrival
    )
    .dt.total_seconds()
    / 60
)

raw_actual_gap = (
    (
        df["scheduled_departure_ts"]
        -
        previous_actual_arrival
    )
    .dt.total_seconds()
    / 60
)


# -------------------------------------------------------------------------
# VALID CONNECTION
# -------------------------------------------------------------------------
#
# A previous aircraft flight is usable only when:
#
#   previous actual arrival exists
#   previous scheduled arrival exists
#   scheduled gap is >= 0
#   scheduled gap <= 24 hours
#   actual gap is >= 0
#   actual gap <= 24 hours
#
# Everything else is treated as NO VALID AIRCRAFT CONNECTION.
# -------------------------------------------------------------------------

valid_connection = (

    previous_actual_arrival.notna()

    &

    previous_scheduled_arrival.notna()

    &

    raw_scheduled_turnaround.between(
        0,
        MAX_ROTATION_GAP_MIN
    )

    &

    raw_actual_gap.between(
        0,
        MAX_ROTATION_GAP_MIN
    )
)


df["valid_aircraft_connection"] = (
    valid_connection
).astype(np.int8)


print(
    "Valid aircraft connections:",
    f"{valid_connection.sum():,}"
)

print(
    "Invalid aircraft connections:",
    f"{(~valid_connection).sum():,}"
)


# -------------------------------------------------------------------------
# SCHEDULED TURNAROUND
# -------------------------------------------------------------------------

df["scheduled_turnaround_min"] = (
    raw_scheduled_turnaround
)

df.loc[
    ~valid_connection,
    "scheduled_turnaround_min"
] = np.nan


# -------------------------------------------------------------------------
# ACTUAL GAP
# -------------------------------------------------------------------------

df["time_since_previous_flight_min"] = (
    raw_actual_gap
)

df.loc[
    ~valid_connection,
    "time_since_previous_flight_min"
] = np.nan


# -------------------------------------------------------------------------
# PREVIOUS DEPARTURE DELAY
# -------------------------------------------------------------------------

df["previous_flight_departure_delay"] = (
    previous_departure_delay
)

df.loc[
    ~valid_connection,
    "previous_flight_departure_delay"
] = np.nan


# -------------------------------------------------------------------------
# PREVIOUS FLIGHT DELAYED
# -------------------------------------------------------------------------

df["previous_flight_delayed"] = (
    previous_target
)

df.loc[
    ~valid_connection,
    "previous_flight_delayed"
] = np.nan


# -------------------------------------------------------------------------
# PREVIOUS DELAY MAGNITUDE
# -------------------------------------------------------------------------

df["previous_delay_magnitude"] = (
    df["previous_flight_departure_delay"]
    .clip(
        lower=0
    )
)

df.loc[
    ~valid_connection,
    "previous_delay_magnitude"
] = np.nan


# -------------------------------------------------------------------------
# REMAINING TURNAROUND
# -------------------------------------------------------------------------

df["remaining_turnaround_min"] = (
    raw_actual_gap
)

df.loc[
    ~valid_connection,
    "remaining_turnaround_min"
] = np.nan


# -------------------------------------------------------------------------
# TURNAROUND STRESS
# -------------------------------------------------------------------------

df["turnaround_stress_min"] = (
    -df["remaining_turnaround_min"]
).clip(
    lower=0
)

df.loc[
    ~valid_connection,
    "turnaround_stress_min"
] = np.nan


# -------------------------------------------------------------------------
# BUFFER RATIO
# -------------------------------------------------------------------------

df["buffer_ratio"] = (
    df["remaining_turnaround_min"]
    /
    df["scheduled_turnaround_min"]
    .replace(
        0,
        np.nan
    )
)

df.loc[
    ~valid_connection,
    "buffer_ratio"
] = np.nan


# -------------------------------------------------------------------------
# PROPAGATION PRESSURE
# -------------------------------------------------------------------------

df["propagation_pressure"] = (
    df["previous_delay_magnitude"]
    /
    df["scheduled_turnaround_min"]
    .replace(
        0,
        np.nan
    )
)

df.loc[
    ~valid_connection,
    "propagation_pressure"
] = np.nan


# -------------------------------------------------------------------------
# PROPAGATION RISK
# -------------------------------------------------------------------------

df["propagation_risk"] = (

    valid_connection

    &

    (
        df["previous_delay_magnitude"]
        > 15
    )

    &

    (
        df["remaining_turnaround_min"]
        < 30
    )

).astype(np.int8)


# =============================================================================
# HISTORICAL FEATURES
# =============================================================================

section(
    "CREATING LEAKAGE-SAFE HISTORICAL STATISTICS"
)

print(
    "Aircraft historical statistics..."
)

df = add_history(
    df,
    "TAIL_NUMBER",
    "aircraft"
)

print(
    "Airline historical statistics..."
)

df = add_history(
    df,
    "AIRLINE",
    "airline"
)

print(
    "Route historical statistics..."
)

df = add_history(
    df,
    "ROUTE",
    "route"
)

print(
    "Origin historical statistics..."
)

df = add_history(
    df,
    "ORIGIN_AIRPORT",
    "origin"
)

print(
    "Destination historical statistics..."
)

df = add_history(
    df,
    "DESTINATION_AIRPORT",
    "destination"
)


# =============================================================================
# COMPARATIVE FEATURES
# =============================================================================

section(
    "CREATING COMPARATIVE HISTORICAL FEATURES"
)

df["route_vs_airline_delay_rate"] = (
    df["route_delay_rate"]
    -
    df["airline_delay_rate"]
)

df["origin_vs_airline_delay_rate"] = (
    df["origin_delay_rate"]
    -
    df["airline_delay_rate"]
)

df["destination_vs_airline_delay_rate"] = (
    df["destination_delay_rate"]
    -
    df["airline_delay_rate"]
)


# =============================================================================
# HISTORY STRENGTH
# =============================================================================

df["route_history_strength"] = (
    np.log1p(
        df["route_past_flights"]
    )
    /
    np.log1p(
        max(
            df["route_past_flights"].max(),
            1
        )
    )
).astype(np.float32)

df["airline_history_strength"] = (
    np.log1p(
        df["airline_past_flights"]
    )
    /
    np.log1p(
        max(
            df["airline_past_flights"].max(),
            1
        )
    )
).astype(np.float32)

df["origin_history_strength"] = (
    np.log1p(
        df["origin_past_flights"]
    )
    /
    np.log1p(
        max(
            df["origin_past_flights"].max(),
            1
        )
    )
).astype(np.float32)

df["destination_history_strength"] = (
    np.log1p(
        df["destination_past_flights"]
    )
    /
    np.log1p(
        max(
            df["destination_past_flights"].max(),
            1
        )
    )
).astype(np.float32)


# =============================================================================
# CLEAN INFINITY
# =============================================================================

numeric_cols = (
    df
    .select_dtypes(
        include=[np.number]
    )
    .columns
)

df[numeric_cols] = (
    df[numeric_cols]
    .replace(
        [np.inf, -np.inf],
        np.nan
    )
)


# =============================================================================
# FINAL FEATURE LIST
# =============================================================================

section(
    "BUILDING FINAL 64-FEATURE SET"
)

MODEL_FEATURES = [

    # Base
    "AIRLINE",
    "FLIGHT_NUMBER",
    "TAIL_NUMBER",
    "ORIGIN_AIRPORT",
    "DESTINATION_AIRPORT",

    # Flight
    "SCHEDULED_TIME",
    "DISTANCE",

    # Time
    "departure_hour",
    "departure_minute",
    "is_weekend",
    "departure_hour_sin",
    "departure_hour_cos",
    "day_of_week_sin",
    "day_of_week_cos",
    "departure_day_of_week",
    "departure_day",
    "departure_month",
    "departure_day_of_year",
    "departure_week",

    # Airline / airport
    "AIRLINE_NAME",
    "origin_state",
    "origin_latitude",
    "origin_longitude",
    "destination_state",
    "destination_latitude",
    "destination_longitude",
    "same_state",
    "route_geographic_distance_km",

    # Flight characteristics
    "distance_per_scheduled_min",
    "scheduled_speed_proxy",

    # Route
    "ROUTE",

    # Aircraft rotation
    "previous_flight_departure_delay",
    "previous_flight_delayed",
    "previous_delay_magnitude",
    "time_since_previous_flight_min",
    "valid_aircraft_connection",
    "scheduled_turnaround_min",
    "remaining_turnaround_min",
    "turnaround_stress_min",
    "buffer_ratio",
    "propagation_pressure",
    "propagation_risk",

    # Aircraft history
    "aircraft_past_flights",
    "aircraft_delay_rate",
    "aircraft_avg_departure_delay",

    # Airline history
    "airline_past_flights",
    "airline_delay_rate",
    "airline_avg_departure_delay",

    # Route history
    "route_past_flights",
    "route_delay_rate",
    "route_avg_departure_delay",

    # Origin history
    "origin_past_flights",
    "origin_delay_rate",
    "origin_avg_departure_delay",

    # Destination history
    "destination_past_flights",
    "destination_delay_rate",
    "destination_avg_departure_delay",

    # Comparative
    "route_vs_airline_delay_rate",
    "origin_vs_airline_delay_rate",
    "destination_vs_airline_delay_rate",

    # History strength
    "route_history_strength",
    "airline_history_strength",
    "origin_history_strength",
    "destination_history_strength"
]


MODEL_FEATURES = list(
    dict.fromkeys(
        MODEL_FEATURES
    )
)


print(
    "Model features:",
    len(MODEL_FEATURES)
)

if len(MODEL_FEATURES) != 64:

    raise ValueError(
        f"Expected 64 model features, "
        f"found {len(MODEL_FEATURES)}"
    )

print(
    "64 features confirmed. ✓"
)


# =============================================================================
# FEATURE EXISTENCE
# =============================================================================

missing_features = [

    c
    for c in MODEL_FEATURES
    if c not in df.columns

]

if missing_features:

    raise ValueError(
        "Missing features:\n"
        +
        "\n".join(
            missing_features
        )
    )

print(
    "All model features exist. ✓"
)


# =============================================================================
# LEAKAGE AUDIT
# =============================================================================

section(
    "LEAKAGE AUDIT"
)

FORBIDDEN = [

    "target",
    "flight_date",
    "scheduled_departure_ts",
    "scheduled_arrival_ts",
    "actual_departure_ts",
    "actual_arrival_ts",
    "DEPARTURE_DELAY"

]

leakage = [

    c
    for c in MODEL_FEATURES
    if c in FORBIDDEN

]

if leakage:

    raise ValueError(
        "LEAKAGE DETECTED:\n"
        +
        "\n".join(
            leakage
        )
    )

print(
    "No explicit target leakage detected. ✓"
)


# =============================================================================
# TRAFFIC FEATURES MUST NOT EXIST
# =============================================================================

section(
    "AIRPORT TRAFFIC FEATURE CHECK"
)

TRAFFIC_FEATURES = [

    "origin_departures_prev_60min",
    "origin_departures_prev_180min",
    "destination_arrivals_prev_60min",
    "destination_arrivals_prev_180min",
    "origin_traffic_intensity",
    "destination_traffic_intensity",
    "origin_delay_pressure",
    "origin_congestion_score",
    "destination_congestion_score",
    "origin_high_traffic",
    "destination_high_traffic"

]

traffic_present = [

    c
    for c in TRAFFIC_FEATURES
    if c in MODEL_FEATURES

]

if traffic_present:

    raise ValueError(
        "Traffic features still present:\n"
        +
        "\n".join(
            traffic_present
        )
    )

print(
    "All 11 traffic features removed. ✓"
)


# =============================================================================
# FINAL ROTATION VALIDATION
# =============================================================================

section(
    "FINAL AIRCRAFT ROTATION VALIDATION"
)


rotation_features = [

    "time_since_previous_flight_min",
    "scheduled_turnaround_min",
    "remaining_turnaround_min",
    "buffer_ratio",
    "propagation_pressure"

]


for feature in rotation_features:

    series = pd.to_numeric(
        df[feature],
        errors="coerce"
    )

    print()
    print(feature)

    print(
        "  missing:",
        f"{series.isna().sum():,}"
    )

    print(
        "  min:",
        series.min()
    )

    print(
        "  median:",
        series.median()
    )

    print(
        "  mean:",
        series.mean()
    )

    print(
        "  99%:",
        series.quantile(0.99)
    )

    print(
        "  max:",
        series.max()
    )


# =============================================================================
# HARD VALIDATION
# =============================================================================

negative_actual_gap = (

    df["time_since_previous_flight_min"]
    .dropna()
    < 0

).sum()


negative_remaining = (

    df["remaining_turnaround_min"]
    .dropna()
    < 0

).sum()


large_actual_gap = (

    df["time_since_previous_flight_min"]
    .dropna()
    > MAX_ROTATION_GAP_MIN

).sum()


large_scheduled_gap = (

    df["scheduled_turnaround_min"]
    .dropna()
    > MAX_ROTATION_GAP_MIN

).sum()


print()
print(
    "Negative actual gaps:",
    negative_actual_gap
)

print(
    "Negative remaining turnaround:",
    negative_remaining
)

print(
    "Actual gaps > 24h:",
    large_actual_gap
)

print(
    "Scheduled gaps > 24h:",
    large_scheduled_gap
)


if negative_actual_gap != 0:

    raise ValueError(
        "Negative actual aircraft gaps remain."
    )


if negative_remaining != 0:

    raise ValueError(
        "Negative remaining turnaround remains."
    )


if large_actual_gap != 0:

    raise ValueError(
        "Actual aircraft gaps > 24h remain."
    )


if large_scheduled_gap != 0:

    raise ValueError(
        "Scheduled aircraft gaps > 24h remain."
    )


print(
    "Aircraft rotation validation passed. ✓"
)


# =============================================================================
# CREATE FINAL DATASET
# =============================================================================

section(
    "CREATING FINAL DATASET"
)

final_columns = (
    MODEL_FEATURES
    +
    [TARGET]
)

output = df[
    final_columns
].copy()


print(
    "Rows:",
    f"{len(output):,}"
)

print(
    "Model features:",
    len(MODEL_FEATURES)
)

print(
    "Total columns:",
    len(output.columns)
)


# =============================================================================
# FINAL STRUCTURE VALIDATION
# =============================================================================

if len(output) != EXPECTED_ROWS:

    raise ValueError(
        "Final row count is incorrect."
    )


if len(MODEL_FEATURES) != 64:

    raise ValueError(
        "Final feature count is incorrect."
    )


if len(output.columns) != 65:

    raise ValueError(
        "Expected 65 total columns."
    )


# =============================================================================
# TARGET VALIDATION
# =============================================================================

section(
    "TARGET VALIDATION"
)

print(
    output[TARGET].value_counts()
)

print()

print(
    output[TARGET]
    .value_counts(
        normalize=True
    )
    * 100
)


# =============================================================================
# SAVE
# =============================================================================

section(
    "SAVING FINAL V4.1 DATASET"
)

print(
    "Output:"
)

print(
    OUTPUT_PATH
)

output.to_csv(
    OUTPUT_PATH,
    index=False
)

print(
    "Dataset saved successfully. ✓"
)


# =============================================================================
# SAVE FEATURE LIST
# =============================================================================

with open(
    FEATURE_LIST_PATH,
    "w",
    encoding="utf-8"
) as f:

    for feature in MODEL_FEATURES:

        f.write(
            feature
            +
            "\n"
        )


print(
    "Feature list saved:"
)

print(
    FEATURE_LIST_PATH
)


# =============================================================================
# FINAL SUMMARY
# =============================================================================

section(
    "STEP 14.1 COMPLETE"
)

print(
    "Rows             :",
    f"{len(output):,}"
)

print(
    "Model features   :",
    len(MODEL_FEATURES)
)

print(
    "Total columns    :",
    len(output.columns)
)

print(
    "Traffic features : REMOVED"
)

print(
    "Airport mapping  : VERIFIED"
)

print(
    "Aircraft rotation: CORRECTED"
)

print(
    "Leakage audit    : PASSED"
)

print(
    "Row count        : PRESERVED"
)

print()
print(
    "OUTPUT:"
)

print(
    OUTPUT_PATH
)

print()
print(
    "✓ FINAL V4.1 FEATURE DATASET CREATED"
)

print(
    "✓ READY FOR CATBOOST TRAINING"
)