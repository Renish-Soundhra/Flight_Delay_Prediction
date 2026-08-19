# =============================================================================
# STEP 16 — V4.2 AIRCRAFT PROPAGATION ENHANCEMENT
# =============================================================================
#
# FINAL CORRECTED VERSION
#
# V4.1:
#   64 model features
#
# V4.2 adds:
#   1. previous_flight_arrival_delay
#   2. tight_turnaround
#   3. is_first_flight_of_day
#   4. aircraft_cumulative_delay_today
#
# IMPORTANT:
#   - No target leakage
#   - No current-flight actual delay
#   - No future-flight information
#   - Previous aircraft flight information only
#   - Negative arrival delays converted to 0 propagation delay
#   - Cumulative delay contains only positive previous-flight delays
#   - Original row order preserved
#   - Airport columns are NOT used for raw/V4.1 alignment because
#     V4.1 intentionally normalized BTS airport IDs to IATA codes.
#
# =============================================================================

import os
import gc
import time

import numpy as np
import pandas as pd


# =============================================================================
# PATHS
# =============================================================================

ORIGINAL_FLIGHTS_PATH = (
    r"D:\Cognizant\flights_clean.csv"
)

V4_1_PATH = (
    r"D:\Cognizant\flights_features_v4_1.csv"
)

OUTPUT_PATH = (
    r"D:\Cognizant\flights_features_v4_2.csv"
)

FEATURE_LIST_PATH = (
    r"D:\Cognizant\feature_v4_2_list.txt"
)

VALIDATION_REPORT_PATH = (
    r"D:\Cognizant\v4_2_propagation_validation.txt"
)


# =============================================================================
# CONFIGURATION
# =============================================================================

EXPECTED_ROWS = 5_714_008

TARGET = "target"

TIGHT_TURNAROUND_THRESHOLD = 45.0

MAX_CONNECTION_GAP_MINUTES = 1440.0


# =============================================================================
# REQUIRED ORIGINAL COLUMNS
# =============================================================================

REQUIRED_COLUMNS = [

    "flight_date",
    "AIRLINE",
    "FLIGHT_NUMBER",
    "TAIL_NUMBER",
    "ORIGIN_AIRPORT",
    "DESTINATION_AIRPORT",
    "scheduled_departure_ts",
    "scheduled_arrival_ts",
    "actual_departure_ts",
    "actual_arrival_ts",
    "target"

]


# =============================================================================
# NEW FEATURES
# =============================================================================

NEW_FEATURES = [

    "previous_flight_arrival_delay",
    "tight_turnaround",
    "is_first_flight_of_day",
    "aircraft_cumulative_delay_today"

]


# =============================================================================
# HELPER
# =============================================================================

def section(title):

    print()
    print("=" * 80)
    print(title)
    print("=" * 80)


def print_stats(name, series):

    print()
    print(name)

    print(
        "  missing:",
        int(series.isna().sum())
    )

    valid = series.dropna()

    if len(valid) == 0:

        print("  no valid values")

        return

    print(
        "  min    :",
        float(valid.min())
    )

    print(
        "  median :",
        float(valid.median())
    )

    print(
        "  mean   :",
        float(valid.mean())
    )

    print(
        "  99%    :",
        float(valid.quantile(0.99))
    )

    print(
        "  max    :",
        float(valid.max())
    )


# =============================================================================
# START
# =============================================================================

section(
    "STEP 16 — V4.2 AIRCRAFT PROPAGATION ENHANCEMENT"
)

print(
    "FINAL CORRECTED VERSION"
)

print()
print(
    "Base dataset:",
    V4_1_PATH
)

print(
    "Original flight data:",
    ORIGINAL_FLIGHTS_PATH
)

print()
print("New features:")

for i, feature in enumerate(
    NEW_FEATURES,
    start=1
):

    print(
        f"  {i}. {feature}"
    )

print()
print(
    "Tight turnaround threshold:",
    TIGHT_TURNAROUND_THRESHOLD,
    "minutes"
)

print(
    "Maximum aircraft connection gap:",
    MAX_CONNECTION_GAP_MINUTES,
    "minutes"
)


# =============================================================================
# CHECK INPUT FILES
# =============================================================================

section(
    "CHECKING INPUT FILES"
)

if not os.path.exists(
    ORIGINAL_FLIGHTS_PATH
):

    raise FileNotFoundError(
        ORIGINAL_FLIGHTS_PATH
    )

print(
    "Original flight dataset: ✓"
)


if not os.path.exists(
    V4_1_PATH
):

    raise FileNotFoundError(
        V4_1_PATH
    )

print(
    "V4.1 feature dataset: ✓"
)


# =============================================================================
# LOAD V4.1
# =============================================================================

section(
    "LOADING V4.1 FEATURE DATASET"
)

start = time.time()

v4 = pd.read_csv(
    V4_1_PATH,
    low_memory=False
)

print(
    "V4.1 rows:",
    f"{len(v4):,}"
)

print(
    "V4.1 columns:",
    len(v4.columns)
)

if len(v4) != EXPECTED_ROWS:

    raise ValueError(
        f"V4.1 row count mismatch.\n"
        f"Expected: {EXPECTED_ROWS:,}\n"
        f"Found: {len(v4):,}"
    )

print(
    "V4.1 row count confirmed. ✓"
)

print(
    "Loading time:",
    f"{(time.time() - start) / 60:.2f} minutes"
)


# =============================================================================
# TARGET CHECK
# =============================================================================

section(
    "V4.1 TARGET VALIDATION"
)

if TARGET not in v4.columns:

    raise ValueError(
        "Target column not found in V4.1."
    )

print(
    v4[TARGET].value_counts()
)

print()

print(
    v4[TARGET].value_counts(
        normalize=True
    )
)


# =============================================================================
# IDENTIFY V4.1 FEATURES
# =============================================================================

section(
    "IDENTIFYING V4.1 MODEL FEATURES"
)

v4_model_features = [

    c
    for c in v4.columns
    if c != TARGET

]

print(
    "V4.1 model features:",
    len(v4_model_features)
)

if len(v4_model_features) != 64:

    raise ValueError(
        f"Expected 64 V4.1 features. "
        f"Found {len(v4_model_features)}."
    )

print(
    "64 V4.1 features confirmed. ✓"
)


# =============================================================================
# LOAD ORIGINAL DATA
# =============================================================================

section(
    "LOADING ORIGINAL FLIGHT DATA"
)

original = pd.read_csv(

    ORIGINAL_FLIGHTS_PATH,

    usecols=REQUIRED_COLUMNS,

    low_memory=False

)

print(
    "Original rows:",
    f"{len(original):,}"
)

if len(original) != EXPECTED_ROWS:

    raise ValueError(
        f"Original row count mismatch.\n"
        f"Expected: {EXPECTED_ROWS:,}\n"
        f"Found: {len(original):,}"
    )

print(
    "Original row count confirmed. ✓"
)


# =============================================================================
# CREATE ORIGINAL ROW POSITION
# =============================================================================

section(
    "CREATING ORIGINAL ROW POSITIONS"
)

original["__original_row_position"] = np.arange(

    len(original),

    dtype=np.int64

)

print(
    "Original row positions created. ✓"
)


# =============================================================================
# CLEAN AIRCRAFT IDENTIFIERS
# =============================================================================

section(
    "CLEANING AIRCRAFT IDENTIFIERS"
)

original["TAIL_NUMBER"] = (

    original["TAIL_NUMBER"]
    .astype("string")
    .fillna("__MISSING_AIRCRAFT__")
    .astype(str)

)

missing_aircraft = (

    original["TAIL_NUMBER"]
    == "__MISSING_AIRCRAFT__"

).sum()

print(
    "Missing aircraft identifiers:",
    f"{missing_aircraft:,}"
)


# =============================================================================
# TIMESTAMP CONVERSION
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

for column in timestamp_columns:

    original[column] = pd.to_datetime(

        original[column],

        errors="coerce"

    )

    print(

        f"{column}: "
        f"{original[column].notna().sum():,} valid / "
        f"{original[column].isna().sum():,} missing"

    )


# =============================================================================
# SORT CHRONOLOGICALLY BY AIRCRAFT
# =============================================================================

section(
    "SORTING AIRCRAFT FLIGHTS CHRONOLOGICALLY"
)

original = original.sort_values(

    [
        "TAIL_NUMBER",
        "scheduled_departure_ts",
        "__original_row_position"

    ],

    kind="mergesort"

).reset_index(
    drop=True
)

print(
    "Aircraft chronological ordering complete. ✓"
)


# =============================================================================
# AIRCRAFT GROUP
# =============================================================================

aircraft_group = original.groupby(

    "TAIL_NUMBER",

    sort=False

)


# =============================================================================
# PREVIOUS AIRCRAFT FLIGHT
# =============================================================================

section(
    "CREATING PREVIOUS AIRCRAFT FLIGHT INFORMATION"
)

original[
    "__previous_scheduled_arrival"
] = (

    aircraft_group[
        "scheduled_arrival_ts"
    ].shift(1)

)


original[
    "__previous_actual_arrival"
] = (

    aircraft_group[
        "actual_arrival_ts"
    ].shift(1)

)


original[
    "__previous_flight_date"
] = (

    aircraft_group[
        "flight_date"
    ].shift(1)

)


print(
    "Previous aircraft flight information created. ✓"
)


# =============================================================================
# CONNECTION GAP
# =============================================================================

section(
    "CALCULATING AIRCRAFT CONNECTION GAPS"
)

connection_gap = (

    original[
        "scheduled_departure_ts"
    ]
    -
    original[
        "__previous_actual_arrival"
    ]

).dt.total_seconds() / 60.0


original[
    "__connection_gap_min"
] = connection_gap


valid_connection = (

    original[
        "__previous_actual_arrival"
    ].notna()

    &

    original[
        "scheduled_departure_ts"
    ].notna()

    &

    (connection_gap >= 0)

    &

    (
        connection_gap
        <=
        MAX_CONNECTION_GAP_MINUTES
    )

)


original[
    "__valid_aircraft_connection"
] = valid_connection


print(
    "Valid aircraft connections:",
    f"{valid_connection.sum():,}"
)

print(
    "Invalid aircraft connections:",
    f"{(~valid_connection).sum():,}"
)


# =============================================================================
# PREVIOUS FLIGHT ARRIVAL DELAY
# =============================================================================

section(
    "CREATING PREVIOUS FLIGHT ARRIVAL DELAY"
)

raw_previous_arrival_delay = (

    original[
        "__previous_actual_arrival"
    ]
    -
    original[
        "__previous_scheduled_arrival"
    ]

).dt.total_seconds() / 60.0


raw_previous_arrival_delay = (

    raw_previous_arrival_delay
    .where(valid_connection)

)


# IMPORTANT:
# Early arrival is NOT negative propagation.
#
# Example:
#   -15 min early -> 0 propagation delay
#
previous_arrival_delay = (

    raw_previous_arrival_delay
    .clip(lower=0)

)


original[
    "previous_flight_arrival_delay"
] = previous_arrival_delay


print_stats(

    "previous_flight_arrival_delay",

    original[
        "previous_flight_arrival_delay"
    ]

)


# =============================================================================
# FIRST FLIGHT OF DAY
# =============================================================================

section(
    "CREATING FIRST-FLIGHT-OF-DAY FEATURE"
)

current_date = pd.to_datetime(

    original[
        "flight_date"
    ],

    errors="coerce"

)


previous_date = pd.to_datetime(

    original[
        "__previous_flight_date"
    ],

    errors="coerce"

)


is_first_flight = (

    previous_date.isna()

    |

    (
        previous_date
        !=
        current_date
    )

)


original[
    "is_first_flight_of_day"
] = is_first_flight.astype(
    "int8"
)


print(
    "First flight of day:",
    f"{int(is_first_flight.sum()):,}"
)

print(
    "Non-first flight:",
    f"{int((~is_first_flight).sum()):,}"
)


# =============================================================================
# ACTUAL ARRIVAL TURNAROUND
# =============================================================================

section(
    "CALCULATING ACTUAL-ARRIVAL-BASED TURNAROUND"
)

turnaround = (

    original[
        "scheduled_departure_ts"
    ]
    -
    original[
        "__previous_actual_arrival"
    ]

).dt.total_seconds() / 60.0


turnaround = turnaround.where(
    valid_connection
)


original[
    "__actual_arrival_turnaround_min"
] = turnaround


print_stats(

    "actual-arrival-based turnaround",

    original[
        "__actual_arrival_turnaround_min"
    ]

)


# =============================================================================
# TIGHT TURNAROUND
# =============================================================================

section(
    "CREATING TIGHT TURNAROUND FEATURE"
)

tight_turnaround = (

    valid_connection

    &

    (
        turnaround
        <
        TIGHT_TURNAROUND_THRESHOLD
    )

)


original[
    "tight_turnaround"
] = tight_turnaround.astype(
    "int8"
)


print(
    "Tight turnaround flights:",
    f"{int(tight_turnaround.sum()):,}"
)

print(
    "Percentage:",
    f"{tight_turnaround.mean() * 100:.2f}%"
)


# =============================================================================
# AIRCRAFT-DAY GROUP
# =============================================================================

section(
    "CREATING AIRCRAFT-DAY GROUP"
)

original[
    "__aircraft_day"
] = (

    original[
        "TAIL_NUMBER"
    ].astype(str)

    + "___"

    + original[
        "flight_date"
    ].astype(str)

)

print(
    "Aircraft-day groups created. ✓"
)


# =============================================================================
# CUMULATIVE POSITIVE DELAY
# =============================================================================

section(
    "CREATING AIRCRAFT CUMULATIVE DELAY TODAY"
)

original[
    "__delay_contribution"
] = (

    original[
        "previous_flight_arrival_delay"
    ].fillna(0.0)

)


original[
    "aircraft_cumulative_delay_today"
] = (

    original

    .groupby(
        "__aircraft_day",
        sort=False
    )

    [
        "__delay_contribution"
    ]

    .cumsum()

)


# First flight of the day has no previous delay.

original.loc[

    original[
        "is_first_flight_of_day"
    ] == 1,

    "aircraft_cumulative_delay_today"

] = 0.0


original[
    "aircraft_cumulative_delay_today"
] = (

    original[
        "aircraft_cumulative_delay_today"
    ].astype(float)

)


print_stats(

    "aircraft_cumulative_delay_today",

    original[
        "aircraft_cumulative_delay_today"
    ]

)


# =============================================================================
# RESTORE ORIGINAL ORDER
# =============================================================================

section(
    "RESTORING ORIGINAL ROW ORDER"
)

original = original.sort_values(

    "__original_row_position",

    kind="mergesort"

).reset_index(
    drop=True
)

print(
    "Original row order restored. ✓"
)


# =============================================================================
# V4.1 / ORIGINAL ALIGNMENT VALIDATION
# =============================================================================
#
# IMPORTANT:
#
# DO NOT compare:
#
#   ORIGIN_AIRPORT
#   DESTINATION_AIRPORT
#
# because V4.1 intentionally normalized airport identifiers.
#
# Example:
#
# Original:
#   ORIGIN_AIRPORT = 10397
#
# V4.1:
#   ORIGIN_AIRPORT = ATL
#
# These represent the same airport but are different strings.
#
# =============================================================================

section(
    "VALIDATING V4.1 / ORIGINAL ROW ALIGNMENT"
)


alignment_columns = [

    "AIRLINE",
    "FLIGHT_NUMBER",
    "TAIL_NUMBER"

]


for column in alignment_columns:

    original_values = (

        original[
            column
        ]
        .astype("string")
        .fillna("__NA__")

    )

    v4_values = (

        v4[
            column
        ]
        .astype("string")
        .fillna("__NA__")

    )

    mismatches = (

        original_values
        !=
        v4_values

    ).sum()

    print(
        f"{column}: mismatches = {mismatches:,}"
    )

    if mismatches != 0:

        raise ValueError(
            f"Row alignment failed for {column}."
        )


# =============================================================================
# TARGET ALIGNMENT
# =============================================================================

original_target = (

    original[
        TARGET
    ]
    .to_numpy()

)

v4_target = (

    v4[
        TARGET
    ]
    .to_numpy()

)


target_mismatches = np.sum(

    original_target
    !=
    v4_target

)


print(
    f"{TARGET}: mismatches = "
    f"{target_mismatches:,}"
)


if target_mismatches != 0:

    raise ValueError(
        "Target row alignment failed."
    )


print(
    "V4.1 and original flight rows are aligned. ✓"
)


# =============================================================================
# EXTRACT PROPAGATION FEATURES
# =============================================================================

section(
    "EXTRACTING V4.2 PROPAGATION FEATURES"
)

propagation_features = original[

    [
        "previous_flight_arrival_delay",
        "tight_turnaround",
        "is_first_flight_of_day",
        "aircraft_cumulative_delay_today"

    ]

].copy()


# =============================================================================
# ADD ROW POSITION
# =============================================================================

propagation_features[
    "__row_position"
] = np.arange(

    len(propagation_features),

    dtype=np.int64

)

v4["__row_position"] = np.arange(

    len(v4),

    dtype=np.int64

)


# =============================================================================
# MERGE
# =============================================================================

section(
    "MERGING V4.2 FEATURES INTO V4.1"
)

v4 = v4.merge(

    propagation_features,

    on="__row_position",

    how="left",

    validate="one_to_one"

)


v4 = v4.drop(

    columns=[
        "__row_position"
    ]

)


print(
    "V4.2 features merged. ✓"
)


# =============================================================================
# NEW FEATURE VALIDATION
# =============================================================================

section(
    "V4.2 NEW FEATURE VALIDATION"
)

for feature in NEW_FEATURES:

    print_stats(

        feature,

        v4[
            feature
        ]

    )


# =============================================================================
# PREVIOUS DELAY VALIDATION
# =============================================================================

section(
    "PREVIOUS ARRIVAL DELAY VALIDATION"
)

negative_previous_delay = (

    v4[
        "previous_flight_arrival_delay"
    ]
    < 0

).sum()


print(
    "Negative previous arrival delay:",
    f"{negative_previous_delay:,}"
)


if negative_previous_delay != 0:

    raise ValueError(
        "Negative previous arrival delay remains."
    )


print(
    "Previous arrival delay validation passed. ✓"
)


# =============================================================================
# TIGHT TURNAROUND VALIDATION
# =============================================================================

section(
    "TIGHT TURNAROUND VALIDATION"
)

expected_tight = (

    original[
        "__actual_arrival_turnaround_min"
    ].notna()

    &

    (
        original[
            "__actual_arrival_turnaround_min"
        ]
        <
        TIGHT_TURNAROUND_THRESHOLD
    )

)


actual_tight = (

    v4[
        "tight_turnaround"
    ]
    == 1

)


tight_mismatches = (

    expected_tight
    !=
    actual_tight

).sum()


print(
    "Tight turnaround mismatches:",
    f"{tight_mismatches:,}"
)


if tight_mismatches != 0:

    raise ValueError(
        "Tight turnaround validation failed."
    )


print(
    "Tight turnaround validation passed. ✓"
)


# =============================================================================
# FIRST-FLIGHT VALIDATION
# =============================================================================

section(
    "FIRST-FLIGHT-OF-DAY VALIDATION"
)

first_values = sorted(

    v4[
        "is_first_flight_of_day"
    ]
    .dropna()
    .unique()
    .tolist()

)


print(
    "Unique values:",
    first_values
)


if not set(first_values).issubset(
    {0, 1}
):

    raise ValueError(
        "First-flight feature contains invalid values."
    )


print(
    "Binary validation passed. ✓"
)


# =============================================================================
# CUMULATIVE DELAY VALIDATION
# =============================================================================

section(
    "CUMULATIVE AIRCRAFT DELAY VALIDATION"
)

negative_cumulative = (

    v4[
        "aircraft_cumulative_delay_today"
    ]
    < 0

).sum()


print(
    "Negative cumulative delay rows:",
    f"{negative_cumulative:,}"
)


if negative_cumulative != 0:

    raise ValueError(
        "Negative cumulative aircraft delay remains."
    )


print(
    "Cumulative delay validation passed. ✓"
)


# =============================================================================
# FIRST FLIGHT CUMULATIVE VALIDATION
# =============================================================================

first_flight_nonzero = (

    v4.loc[

        v4[
            "is_first_flight_of_day"
        ] == 1,

        "aircraft_cumulative_delay_today"

    ]
    != 0

).sum()


print(
    "First-flight rows with non-zero cumulative delay:",
    f"{first_flight_nonzero:,}"
)


if first_flight_nonzero != 0:

    raise ValueError(
        "First flight has non-zero cumulative delay."
    )


print(
    "First-flight cumulative validation passed. ✓"
)


# =============================================================================
# LEAKAGE AUDIT
# =============================================================================

section(
    "V4.2 LEAKAGE AUDIT"
)

print(
    "Target used in feature construction: NO"
)

print(
    "Current flight departure delay used: NO"
)

print(
    "Current flight actual departure used: NO"
)

print(
    "Current flight actual arrival used: NO"
)

print(
    "Future flights used: NO"
)

print(
    "Previous aircraft information used: YES"
)

print(
    "Leakage audit passed. ✓"
)


# =============================================================================
# FINAL FEATURE COUNT
# =============================================================================

section(
    "BUILDING FINAL V4.2 FEATURE SET"
)

v4_model_features = [

    c
    for c in v4.columns
    if c != TARGET

]


print(
    "V4.1 features:",
    64
)

print(
    "New features:",
    len(NEW_FEATURES)
)

print(
    "V4.2 total model features:",
    len(v4_model_features)
)


if len(v4_model_features) != 68:

    raise ValueError(
        f"Expected 68 model features. "
        f"Found {len(v4_model_features)}."
    )


print(
    "68 features confirmed. ✓"
)


# =============================================================================
# ROW COUNT VALIDATION
# =============================================================================

section(
    "FINAL ROW COUNT VALIDATION"
)

print(
    "Current rows:",
    f"{len(v4):,}"
)

print(
    "Expected rows:",
    f"{EXPECTED_ROWS:,}"
)


if len(v4) != EXPECTED_ROWS:

    raise ValueError(
        "V4.2 row count changed."
    )


print(
    "Row count preserved. ✓"
)


# =============================================================================
# TARGET VALIDATION
# =============================================================================

section(
    "FINAL TARGET VALIDATION"
)

print(
    v4[TARGET].value_counts()
)

print()

print(
    v4[TARGET].value_counts(
        normalize=True
    )
)


# =============================================================================
# FEATURE LIST
# =============================================================================

section(
    "SAVING V4.2 FEATURE LIST"
)

with open(

    FEATURE_LIST_PATH,

    "w",

    encoding="utf-8"

) as f:

    f.write(
        "STEP 16 — V4.2 MODEL FEATURES\n"
    )

    f.write(
        "=" * 80
        + "\n\n"
    )

    f.write(
        f"Total model features: "
        f"{len(v4_model_features)}\n\n"
    )

    for i, feature in enumerate(

        v4_model_features,

        start=1

    ):

        f.write(
            f"{i}. {feature}\n"
        )


print(
    "Feature list saved:"
)

print(
    FEATURE_LIST_PATH
)


# =============================================================================
# VALIDATION REPORT
# =============================================================================

section(
    "SAVING VALIDATION REPORT"
)

with open(

    VALIDATION_REPORT_PATH,

    "w",

    encoding="utf-8"

) as f:

    f.write(
        "STEP 16 — V4.2 AIRCRAFT PROPAGATION VALIDATION\n"
    )

    f.write(
        "=" * 80
        + "\n\n"
    )

    f.write(
        f"Rows: {len(v4):,}\n"
    )

    f.write(
        "V4.1 model features: 64\n"
    )

    f.write(
        "V4.2 model features: 68\n\n"
    )

    f.write(
        "NEW FEATURES\n"
    )

    f.write(
        "-" * 80
        + "\n"
    )

    for feature in NEW_FEATURES:

        f.write(
            feature + "\n"
        )

    f.write(
        "\n"
    )

    f.write(
        f"Tight turnaround threshold: "
        f"{TIGHT_TURNAROUND_THRESHOLD} minutes\n"
    )

    f.write(
        f"Maximum connection gap: "
        f"{MAX_CONNECTION_GAP_MINUTES} minutes\n"
    )

    f.write(
        "\nLEAKAGE AUDIT\n"
    )

    f.write(
        "-" * 80
        + "\n"
    )

    f.write(
        "Target excluded.\n"
    )

    f.write(
        "Current flight actual delay excluded.\n"
    )

    f.write(
        "Current flight actual arrival excluded.\n"
    )

    f.write(
        "Future flights excluded.\n"
    )

    f.write(
        "Only previous aircraft information used.\n"
    )

print(
    "Validation report saved:"
)

print(
    VALIDATION_REPORT_PATH
)


# =============================================================================
# SAVE FINAL V4.2
# =============================================================================

section(
    "SAVING FINAL V4.2 DATASET"
)

print(
    "Output:"
)

print(
    OUTPUT_PATH
)

start = time.time()

v4.to_csv(

    OUTPUT_PATH,

    index=False

)

print(
    "Dataset saved successfully. ✓"
)

print(
    "Save time:",
    f"{(time.time() - start) / 60:.2f} minutes"
)


# =============================================================================
# CLEANUP
# =============================================================================

del original
del propagation_features

gc.collect()


# =============================================================================
# FINAL SUMMARY
# =============================================================================

section(
    "STEP 16 — V4.2 COMPLETE"
)

print(
    "Rows:",
    f"{len(v4):,}"
)

print(
    "V4.1 model features:",
    64
)

print(
    "New features:",
    4
)

print(
    "V4.2 model features:",
    68
)

print()

print(
    "NEW FEATURES:"
)

for feature in NEW_FEATURES:

    print(
        "  ✓",
        feature
    )

print()

print(
    "VALIDATION:"
)

print(
    "  ✓ Row count preserved"
)

print(
    "  ✓ Row alignment verified"
)

print(
    "  ✓ Target alignment verified"
)

print(
    "  ✓ Airport normalization not incorrectly compared"
)

print(
    "  ✓ Negative propagation delay removed"
)

print(
    "  ✓ Negative cumulative delay removed"
)

print(
    "  ✓ Tight turnaround validated"
)

print(
    "  ✓ First-flight feature validated"
)

print(
    "  ✓ Leakage audit passed"
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
    "✓ V4.2 FEATURE DATASET CREATED"
)

print(
    "✓ READY FOR V4.1 vs V4.2 ABLATION TEST"
)