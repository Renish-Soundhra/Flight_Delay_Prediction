# =============================================================================
# STEP 15.1 — REAL FLIGHT PREDICTION SANITY TEST
# =============================================================================

import os
import numpy as np
import pandas as pd

from catboost import CatBoostClassifier


# =============================================================================
# PATHS
# =============================================================================

DATA_PATH = r"D:\Cognizant\flights_features_v4_1.csv"

MODEL_PATH = r"D:\Cognizant\step15_catboost_v4_1.cbm"

RESULTS_PATH = (
    r"D:\Cognizant\step15_1_real_flight_predictions.csv"
)


# =============================================================================
# CONFIGURATION
# =============================================================================

TARGET = "target"

N_SAMPLES = 20

RANDOM_SEED = 42

THRESHOLD = 0.50


# =============================================================================
# HELPER
# =============================================================================

def section(title):

    print()
    print("=" * 80)
    print(title)
    print("=" * 80)


# =============================================================================
# START
# =============================================================================

section(
    "STEP 15.1 — REAL FLIGHT PREDICTION SANITY TEST"
)

print("Purpose: Check individual real-flight predictions")
print("Training: NO")
print("Retraining: NO")
print("Threshold optimization: NO")
print("Threshold:", THRESHOLD)


# =============================================================================
# CHECK FILES
# =============================================================================

section("CHECKING FILES")

if not os.path.exists(DATA_PATH):
    raise FileNotFoundError(
        f"Dataset not found:\n{DATA_PATH}"
    )

print("V4.1 dataset found. ✓")


if not os.path.exists(MODEL_PATH):
    raise FileNotFoundError(
        f"CatBoost model not found:\n{MODEL_PATH}"
    )

print("CatBoost model found. ✓")


# =============================================================================
# LOAD MODEL
# =============================================================================

section("LOADING CATBOOST MODEL")

model = CatBoostClassifier()

model.load_model(MODEL_PATH)

print("Model loaded successfully. ✓")


# -----------------------------------------------------------------------------
# COMPATIBLE FEATURE COUNT
# -----------------------------------------------------------------------------

try:

    model_feature_names = model.feature_names_

except Exception:

    model_feature_names = []


print(
    "Model feature count:",
    len(model_feature_names)
)

if len(model_feature_names) > 0:

    print("Model features loaded successfully. ✓")

else:

    print(
        "Warning: Model feature names were not returned."
    )


# =============================================================================
# LOAD DATASET
# =============================================================================

section("LOADING V4.1 DATASET")

df = pd.read_csv(
    DATA_PATH,
    low_memory=False
)

print(
    "Rows:",
    f"{len(df):,}"
)

print(
    "Columns:",
    len(df.columns)
)


# =============================================================================
# IDENTIFY FEATURES
# =============================================================================

section("IDENTIFYING MODEL FEATURES")

MODEL_FEATURES = [
    c
    for c in df.columns
    if c != TARGET
]

print(
    "Dataset model features:",
    len(MODEL_FEATURES)
)

if len(MODEL_FEATURES) != 64:

    raise ValueError(
        f"Expected 64 model features, "
        f"found {len(MODEL_FEATURES)}"
    )

print("64 features confirmed. ✓")


# =============================================================================
# CHECK MODEL / DATASET FEATURE MATCH
# =============================================================================

section("VALIDATING MODEL / DATASET FEATURES")

if len(model_feature_names) > 0:

    missing_from_dataset = [
        c
        for c in model_feature_names
        if c not in df.columns
    ]

    extra_in_dataset = [
        c
        for c in MODEL_FEATURES
        if c not in model_feature_names
    ]

    if missing_from_dataset:

        print(
            "Features missing from dataset:"
        )

        for c in missing_from_dataset:
            print("  ", c)

        raise ValueError(
            "Model features do not match dataset."
        )

    if extra_in_dataset:

        print(
            "Features present in dataset but not model:"
        )

        for c in extra_in_dataset:
            print("  ", c)

    print(
        "Model/dataset feature compatibility checked. ✓"
    )


# =============================================================================
# CATEGORICAL FEATURES
# =============================================================================

CATEGORICAL_FEATURES = [

    "AIRLINE",
    "AIRLINE_NAME",
    "TAIL_NUMBER",
    "ORIGIN_AIRPORT",
    "DESTINATION_AIRPORT",
    "ROUTE",
    "origin_state",
    "destination_state"

]


# =============================================================================
# PREPARE CATEGORICAL FEATURES
# =============================================================================

section(
    "PREPARING CATEGORICAL FEATURES"
)

for col in CATEGORICAL_FEATURES:

    if col in df.columns:

        df[col] = (
            df[col]
            .astype("string")
            .fillna("__MISSING__")
            .astype(str)
        )


print(
    "Categorical features prepared. ✓"
)


# =============================================================================
# RECREATE TEST SPLIT
# =============================================================================

section(
    "RECREATING TEST SET"
)

n = len(df)

train_end = int(
    n * 0.70
)

validation_end = int(
    n * 0.85
)

test_df = df.iloc[
    validation_end:
].copy()

print(
    "Training boundary:",
    f"{train_end:,}"
)

print(
    "Validation boundary:",
    f"{validation_end:,}"
)

print(
    "Test rows:",
    f"{len(test_df):,}"
)

print(
    "Test set recreated. ✓"
)


# =============================================================================
# RANDOM SAMPLE
# =============================================================================

section(
    "SELECTING REAL TEST FLIGHTS"
)

sample_df = test_df.sample(
    n=N_SAMPLES,
    random_state=RANDOM_SEED
).copy()

print(
    f"Selected {N_SAMPLES} real flights. ✓"
)


# =============================================================================
# CREATE INPUT MATRIX
# =============================================================================

X_sample = sample_df[
    MODEL_FEATURES
]


# =============================================================================
# GENERATE PROBABILITIES
# =============================================================================

section(
    "GENERATING INDIVIDUAL FLIGHT PREDICTIONS"
)

probabilities = (
    model.predict_proba(
        X_sample
    )[:, 1]
)

predictions = (
    probabilities >= THRESHOLD
).astype(int)

print(
    "Predictions generated successfully. ✓"
)


# =============================================================================
# BUILD RESULT TABLE
# =============================================================================

results = pd.DataFrame({

    "AIRLINE":
        sample_df["AIRLINE"].values,

    "TAIL_NUMBER":
        sample_df["TAIL_NUMBER"].values,

    "ORIGIN_AIRPORT":
        sample_df["ORIGIN_AIRPORT"].values,

    "DESTINATION_AIRPORT":
        sample_df["DESTINATION_AIRPORT"].values,

    "departure_hour":
        sample_df["departure_hour"].values,

    "route_delay_rate":
        sample_df["route_delay_rate"].values,

    "previous_flight_delayed":
        sample_df["previous_flight_delayed"].values,

    "buffer_ratio":
        sample_df["buffer_ratio"].values,

    "previous_delay_magnitude":
        sample_df["previous_delay_magnitude"].values,

    "actual_target":
        sample_df[TARGET].values,

    "delay_probability":
        probabilities,

    "predicted_target":
        predictions

})


# =============================================================================
# HUMAN-READABLE RESULTS
# =============================================================================

results["actual_result"] = (
    results["actual_target"]
    .map({
        0: "WILL NOT DELAY",
        1: "WILL DELAY >15 MIN"
    })
)


results["predicted_result"] = (
    results["predicted_target"]
    .map({
        0: "WILL NOT DELAY",
        1: "WILL DELAY >15 MIN"
    })
)


results["correct"] = (
    results["actual_target"]
    ==
    results["predicted_target"]
)


results["status"] = np.where(
    results["correct"],
    "✓ CORRECT",
    "✗ WRONG"
)


results["delay_probability_percent"] = (
    results["delay_probability"] * 100
)


# =============================================================================
# DISPLAY INDIVIDUAL PREDICTIONS
# =============================================================================

section(
    "INDIVIDUAL FLIGHT PREDICTIONS"
)

for i, (_, row) in enumerate(
    results.iterrows(),
    start=1
):

    print()
    print("-" * 80)

    print(
        f"FLIGHT {i}"
    )

    print(
        f"Airline        : {row['AIRLINE']}"
    )

    print(
        f"Tail Number    : {row['TAIL_NUMBER']}"
    )

    print(
        f"Route          : "
        f"{row['ORIGIN_AIRPORT']} "
        f"→ "
        f"{row['DESTINATION_AIRPORT']}"
    )

    print(
        f"Departure Hour : "
        f"{row['departure_hour']}"
    )

    print(
        f"Route Delay Rate : "
        f"{row['route_delay_rate']:.4f}"
    )

    print(
        f"Previous Flight Delayed : "
        f"{row['previous_flight_delayed']}"
    )

    print(
        f"Buffer Ratio : "
        f"{row['buffer_ratio']:.4f}"
    )

    print(
        f"Previous Delay Magnitude : "
        f"{row['previous_delay_magnitude']:.2f}"
    )

    print()

    print(
        f"DELAY PROBABILITY : "
        f"{row['delay_probability_percent']:.2f}%"
    )

    print(
        f"PREDICTION : "
        f"{row['predicted_result']}"
    )

    print(
        f"ACTUAL     : "
        f"{row['actual_result']}"
    )

    print(
        f"RESULT     : "
        f"{row['status']}"
    )


# =============================================================================
# SUMMARY
# =============================================================================

section(
    "SANITY TEST SUMMARY"
)

correct_count = int(
    results["correct"].sum()
)

wrong_count = (
    len(results)
    -
    correct_count
)

sanity_accuracy = (
    correct_count
    /
    len(results)
)


print(
    "Flights tested:",
    len(results)
)

print(
    "Correct:",
    correct_count
)

print(
    "Wrong:",
    wrong_count
)

print(
    "Sanity-test accuracy:",
    f"{sanity_accuracy * 100:.2f}%"
)


# =============================================================================
# HIGH-CONFIDENCE PREDICTIONS
# =============================================================================

section(
    "HIGH-CONFIDENCE PREDICTIONS"
)

high_confidence = results[
    (
        results["delay_probability"] >= 0.80
    )
    |
    (
        results["delay_probability"] <= 0.20
    )
].copy()


if len(high_confidence) == 0:

    print(
        "No predictions with probability <=20% or >=80%."
    )

else:

    print(
        high_confidence[
            [
                "AIRLINE",
                "ORIGIN_AIRPORT",
                "DESTINATION_AIRPORT",
                "delay_probability_percent",
                "predicted_result",
                "actual_result",
                "status"
            ]
        ].to_string(
            index=False
        )
    )


# =============================================================================
# TOP DELAY RISK
# =============================================================================

section(
    "TOP DELAY-RISK FLIGHTS"
)

top_risk = (
    results
    .sort_values(
        "delay_probability",
        ascending=False
    )
    .head(10)
)


print(
    top_risk[
        [
            "AIRLINE",
            "ORIGIN_AIRPORT",
            "DESTINATION_AIRPORT",
            "delay_probability_percent",
            "predicted_result",
            "actual_result",
            "status"
        ]
    ].to_string(
        index=False
    )
)


# =============================================================================
# LOWEST DELAY RISK
# =============================================================================

section(
    "LOWEST DELAY-RISK FLIGHTS"
)

low_risk = (
    results
    .sort_values(
        "delay_probability",
        ascending=True
    )
    .head(10)
)


print(
    low_risk[
        [
            "AIRLINE",
            "ORIGIN_AIRPORT",
            "DESTINATION_AIRPORT",
            "delay_probability_percent",
            "predicted_result",
            "actual_result",
            "status"
        ]
    ].to_string(
        index=False
    )
)


# =============================================================================
# SAVE
# =============================================================================

section(
    "SAVING PREDICTIONS"
)

results.to_csv(
    RESULTS_PATH,
    index=False
)

print(
    "Saved:"
)

print(
    RESULTS_PATH
)


# =============================================================================
# COMPLETE
# =============================================================================

section(
    "STEP 15.1 COMPLETE"
)

print(
    "✓ Model loaded"
)

print(
    "✓ 20 real test flights evaluated"
)

print(
    "✓ Delay probabilities generated"
)

print(
    "✓ WILL DELAY / WILL NOT DELAY predictions generated"
)

print(
    "✓ Actual outcomes compared"
)

print(
    "✓ No training performed"
)

print(
    "✓ No model modification performed"
)