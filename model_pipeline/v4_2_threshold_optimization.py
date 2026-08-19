# =============================================================================
# STEP 19 — LEAKAGE-SAFE THRESHOLD OPTIMIZATION
# =============================================================================
#
# PURPOSE
# -------
# Find the best classification threshold for the FINAL V4.2 BASELINE MODEL.
#
# IMPORTANT:
#   - NO retraining
#   - NO hyperparameter optimization
#   - Threshold selected using VALIDATION ONLY
#   - TEST SET remains completely untouched during threshold selection
#   - Final test evaluation is performed only AFTER threshold is frozen
#
# V4.2 BASELINE:
#   Test ROC-AUC : ~0.8040
#   Test PR-AUC  : ~0.6333
#   Test F1      : ~0.5538 at threshold 0.50
#
# =============================================================================

import os
import gc
import time

import numpy as np
import pandas as pd

from catboost import CatBoostClassifier

from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    average_precision_score,
    confusion_matrix,
    classification_report
)


# =============================================================================
# PATHS
# =============================================================================

V4_2_PATH = (
    r"D:\Cognizant\flights_features_v4_2.csv"
)

BASELINE_MODEL_PATH = (
    r"D:\Cognizant\step17_catboost_v4_2.cbm"
)

OUTPUT_RESULTS_PATH = (
    r"D:\Cognizant\step19_threshold_results.csv"
)

THRESHOLD_RESULTS_PATH = (
    r"D:\Cognizant\step19_all_threshold_results.csv"
)

FINAL_THRESHOLD_PATH = (
    r"D:\Cognizant\step19_selected_threshold.txt"
)


# =============================================================================
# CONFIGURATION
# =============================================================================

TARGET = "target"

EXPECTED_ROWS = 5_714_008

EXPECTED_FEATURES = 68

RANDOM_SEED = 42


# =============================================================================
# SPLIT
# =============================================================================

TRAIN_ROWS = 3_999_805

VALIDATION_ROWS = 857_101

TEST_ROWS = 857_102


# =============================================================================
# THRESHOLD SEARCH
# =============================================================================
#
# Fine-grained search around the useful classification range.
#
# We are NOT optimizing ROC-AUC or PR-AUC here.
# Those metrics are threshold-independent.
#
# Primary threshold-selection metric:
#     F1
#
# We will also report:
#     Precision
#     Recall
#     Accuracy
#
# =============================================================================

THRESHOLDS = np.round(

    np.arange(
        0.10,
        0.901,
        0.01
    ),

    2

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
# HELPER
# =============================================================================

def calculate_threshold_metrics(

    y_true,
    probabilities,
    threshold

):

    predictions = (

        probabilities >= threshold

    ).astype(np.int8)


    accuracy = accuracy_score(

        y_true,

        predictions

    )


    precision = precision_score(

        y_true,

        predictions,

        zero_division=0

    )


    recall = recall_score(

        y_true,

        predictions,

        zero_division=0

    )


    f1 = f1_score(

        y_true,

        predictions,

        zero_division=0

    )


    cm = confusion_matrix(

        y_true,

        predictions

    )


    tn, fp, fn, tp = cm.ravel()


    return {

        "threshold":
            threshold,

        "accuracy":
            accuracy,

        "precision":
            precision,

        "recall":
            recall,

        "f1":
            f1,

        "tn":
            int(tn),

        "fp":
            int(fp),

        "fn":
            int(fn),

        "tp":
            int(tp)

    }


# =============================================================================
# START
# =============================================================================

print()

print("=" * 80)

print(
    "STEP 19 — LEAKAGE-SAFE THRESHOLD OPTIMIZATION"
)

print("=" * 80)

print()

print(
    "Model:",
    BASELINE_MODEL_PATH
)

print(
    "Dataset:",
    V4_2_PATH
)

print()

print(
    "Training: NO"
)

print(
    "Retraining: NO"
)

print(
    "Hyperparameter optimization: NO"
)

print(
    "Threshold optimization: YES"
)

print(
    "Threshold selection set: VALIDATION ONLY"
)

print(
    "Test set used during selection: NO"
)

print(
    "Initial threshold: 0.50"
)

print()


# =============================================================================
# CHECK FILES
# =============================================================================

print("=" * 80)

print(
    "CHECKING INPUT FILES"
)

print("=" * 80)

print()


if not os.path.exists(

    V4_2_PATH

):

    raise FileNotFoundError(

        f"V4.2 dataset not found:\n{V4_2_PATH}"

    )


print(
    "V4.2 dataset found. ✓"
)


if not os.path.exists(

    BASELINE_MODEL_PATH

):

    raise FileNotFoundError(

        f"CatBoost baseline model not found:\n"
        f"{BASELINE_MODEL_PATH}"

    )


print(
    "V4.2 baseline CatBoost model found. ✓"
)


# =============================================================================
# LOAD DATASET
# =============================================================================

print()

print("=" * 80)

print(
    "LOADING V4.2 DATASET"
)

print("=" * 80)

print()

start = time.time()


df = pd.read_csv(

    V4_2_PATH,

    low_memory=False

)


elapsed = (

    time.time()
    -
    start

) / 60


print(
    "Rows:",
    f"{len(df):,}"
)

print(
    "Columns:",
    len(df.columns)
)

print(
    f"Loading time: {elapsed:.2f} minutes"
)


# =============================================================================
# DATASET VALIDATION
# =============================================================================

print()

print("=" * 80)

print(
    "DATASET VALIDATION"
)

print("=" * 80)

print()


if len(df) != EXPECTED_ROWS:

    raise ValueError(

        f"Expected {EXPECTED_ROWS:,} rows "
        f"but found {len(df):,}"

    )


print(
    "Row count confirmed. ✓"
)


if TARGET not in df.columns:

    raise ValueError(
        "Target column missing."
    )


model_features = [

    c

    for c in df.columns

    if c != TARGET

]


print(
    "Model features:",
    len(model_features)
)


if len(model_features) != EXPECTED_FEATURES:

    raise ValueError(

        f"Expected {EXPECTED_FEATURES} model features "
        f"but found {len(model_features)}"

    )


print(
    "68 model features confirmed. ✓"
)


# =============================================================================
# TARGET VALIDATION
# =============================================================================

print()

print("=" * 80)

print(
    "TARGET DISTRIBUTION"
)

print("=" * 80)

print()


print(
    df[TARGET].value_counts()
)

print()

print(
    df[TARGET].value_counts(
        normalize=True
    )
)


# =============================================================================
# CATEGORICAL PREPARATION
# =============================================================================

print()

print("=" * 80)

print(
    "PREPARING CATEGORICAL FEATURES"
)

print("=" * 80)

print()


for feature in CATEGORICAL_FEATURES:

    if feature not in model_features:

        raise ValueError(

            f"Categorical feature missing: {feature}"

        )


    df[feature] = (

        df[feature]

        .astype("string")

        .fillna("__MISSING__")

        .astype(str)

    )


print(
    "Categorical features prepared. ✓"
)


# =============================================================================
# CREATE CHRONOLOGICAL SPLIT
# =============================================================================

print()

print("=" * 80)

print(
    "CREATING CHRONOLOGICAL SPLIT"
)

print("=" * 80)

print()


train_end = TRAIN_ROWS

validation_end = (

    TRAIN_ROWS
    +
    VALIDATION_ROWS

)


train_df = df.iloc[
    :train_end
]

validation_df = df.iloc[
    train_end:validation_end
]

test_df = df.iloc[
    validation_end:
]


print(
    "Training rows   :",
    f"{len(train_df):,}"
)

print(
    "Validation rows :",
    f"{len(validation_df):,}"
)

print(
    "Test rows       :",
    f"{len(test_df):,}"
)


if len(train_df) != TRAIN_ROWS:

    raise ValueError(
        "Training row count mismatch."
    )


if len(validation_df) != VALIDATION_ROWS:

    raise ValueError(
        "Validation row count mismatch."
    )


if len(test_df) != TEST_ROWS:

    raise ValueError(
        "Test row count mismatch."
    )


print()

print(
    "Chronological split confirmed. ✓"
)


# =============================================================================
# TARGET ARRAYS
# =============================================================================

y_train = train_df[
    TARGET
].values


y_validation = validation_df[
    TARGET
].values


y_test = test_df[
    TARGET
].values


# =============================================================================
# TRAIN / VALIDATION / TEST TARGET CHECK
# =============================================================================

print()

print("=" * 80)

print(
    "SPLIT TARGET DISTRIBUTIONS"
)

print("=" * 80)

print()


print(
    "TRAIN"
)

print(
    pd.Series(
        y_train
    ).value_counts()
)

print()


print(
    "VALIDATION"
)

print(
    pd.Series(
        y_validation
    ).value_counts()
)

print()


print(
    "TEST"
)

print(
    pd.Series(
        y_test
    ).value_counts()
)


# =============================================================================
# LOAD BASELINE MODEL
# =============================================================================

print()

print("=" * 80)

print(
    "LOADING V4.2 BASELINE CATBOOST MODEL"
)

print("=" * 80)

print()


model = CatBoostClassifier()

model.load_model(

    BASELINE_MODEL_PATH

)


print(
    "Model loaded successfully. ✓"
)


# =============================================================================
# MODEL VALIDATION
# =============================================================================

print()

print("=" * 80)

print(
    "MODEL VALIDATION"
)

print("=" * 80)

print()


try:

    feature_count = (

        model.get_feature_importance()
        .shape[0]

    )

except Exception:

    feature_count = None


print(
    "Model feature count:",
    feature_count
)


if feature_count is not None:

    if feature_count != EXPECTED_FEATURES:

        raise ValueError(

            f"Model expects {feature_count} features "
            f"but dataset contains {EXPECTED_FEATURES}."

        )


print(
    "Model feature validation passed. ✓"
)


# =============================================================================
# CREATE VALIDATION MATRIX
# =============================================================================

print()

print("=" * 80)

print(
    "CREATING VALIDATION MATRIX"
)

print("=" * 80)

print()


X_validation = validation_df[
    model_features
]


X_test = test_df[
    model_features
]


print(
    "X_validation:",
    X_validation.shape
)

print(
    "X_test:",
    X_test.shape
)


# =============================================================================
# VALIDATION PREDICTIONS
# =============================================================================
#
# IMPORTANT:
# We generate probabilities ONCE.
#
# Threshold optimization does NOT retrain the model.
#
# =============================================================================

print()

print("=" * 80)

print(
    "GENERATING VALIDATION PROBABILITIES"
)

print("=" * 80)

print()


start = time.time()


validation_probabilities = (

    model.predict_proba(

        X_validation

    )[:, 1]

)


elapsed = (

    time.time()
    -
    start

) / 60


print(
    f"Prediction time: {elapsed:.2f} minutes"
)


# =============================================================================
# PROBABILITY SANITY CHECK
# =============================================================================

print()

print("=" * 80)

print(
    "VALIDATION PROBABILITY SANITY CHECK"
)

print("=" * 80)

print()


print(
    "Minimum :",
    float(
        np.min(
            validation_probabilities
        )
    )
)

print(
    "Maximum :",
    float(
        np.max(
            validation_probabilities
        )
    )
)

print(
    "Mean    :",
    float(
        np.mean(
            validation_probabilities
        )
    )
)

print(
    "Median  :",
    float(
        np.median(
            validation_probabilities
        )
    )
)

print(
    "P90     :",
    float(
        np.percentile(
            validation_probabilities,
            90
        )
    )
)

print(
    "P95     :",
    float(
        np.percentile(
            validation_probabilities,
            95
        )
    )
)

print(
    "P99     :",
    float(
        np.percentile(
            validation_probabilities,
            99
        )
    )
)


# =============================================================================
# THRESHOLD-INDEPENDENT VALIDATION METRICS
# =============================================================================

print()

print("=" * 80)

print(
    "THRESHOLD-INDEPENDENT VALIDATION METRICS"
)

print("=" * 80)

print()


validation_roc_auc = roc_auc_score(

    y_validation,

    validation_probabilities

)


validation_pr_auc = average_precision_score(

    y_validation,

    validation_probabilities

)


print(
    f"ROC-AUC : {validation_roc_auc:.6f}"
)

print(
    f"PR-AUC  : {validation_pr_auc:.6f}"
)


print()

print(
    "NOTE:"
)

print(
    "ROC-AUC and PR-AUC do not change when the classification"
)

print(
    "threshold changes. Only threshold-dependent metrics change."
)


# =============================================================================
# THRESHOLD SEARCH
# =============================================================================

print()

print("=" * 80)

print(
    "SEARCHING CLASSIFICATION THRESHOLDS"
)

print("=" * 80)

print()


threshold_results = []


for threshold in THRESHOLDS:

    metrics = calculate_threshold_metrics(

        y_validation,

        validation_probabilities,

        threshold

    )

    threshold_results.append(
        metrics
    )


threshold_df = pd.DataFrame(

    threshold_results

)


# =============================================================================
# FIND BEST THRESHOLD
# =============================================================================
#
# PRIMARY:
#     F1
#
# TIE BREAKER:
#     Precision
#
# SECOND TIE BREAKER:
#     Recall
#
# =============================================================================

threshold_df = (

    threshold_df

    .sort_values(

        [

            "f1",

            "precision",

            "recall"

        ],

        ascending=False

    )

    .reset_index(
        drop=True
    )

)


best_threshold_row = (

    threshold_df.iloc[0]

)


best_threshold = float(

    best_threshold_row[
        "threshold"
    ]

)


# =============================================================================
# DISPLAY ALL RESULTS
# =============================================================================

print()

print("=" * 80)

print(
    "THRESHOLD SEARCH RESULTS"
)

print("=" * 80)

print()


display_columns = [

    "threshold",

    "accuracy",

    "precision",

    "recall",

    "f1"

]


print(

    threshold_df[
        display_columns
    ].to_string(
        index=False
    )

)


# =============================================================================
# BEST THRESHOLD
# =============================================================================

print()

print("=" * 80)

print(
    "BEST VALIDATION THRESHOLD"
)

print("=" * 80)

print()


print(
    f"Selected threshold: {best_threshold:.2f}"
)

print(
    f"Validation Accuracy : "
    f"{best_threshold_row['accuracy']:.6f}"
)

print(
    f"Validation Precision: "
    f"{best_threshold_row['precision']:.6f}"
)

print(
    f"Validation Recall   : "
    f"{best_threshold_row['recall']:.6f}"
)

print(
    f"Validation F1       : "
    f"{best_threshold_row['f1']:.6f}"
)


# =============================================================================
# BASELINE THRESHOLD COMPARISON
# =============================================================================

print()

print("=" * 80)

print(
    "VALIDATION: THRESHOLD 0.50 VS OPTIMIZED THRESHOLD"
)

print("=" * 80)

print()


baseline_threshold_row = (

    threshold_df[

        np.isclose(

            threshold_df[
                "threshold"
            ],

            0.50

        )

    ]

)


if len(baseline_threshold_row) == 1:

    baseline_threshold_row = (

        baseline_threshold_row.iloc[0]

    )

    print(
        "Threshold 0.50:"
    )

    print(
        f"  Accuracy : "
        f"{baseline_threshold_row['accuracy']:.6f}"
    )

    print(
        f"  Precision: "
        f"{baseline_threshold_row['precision']:.6f}"
    )

    print(
        f"  Recall   : "
        f"{baseline_threshold_row['recall']:.6f}"
    )

    print(
        f"  F1       : "
        f"{baseline_threshold_row['f1']:.6f}"
    )


print()

print(
    f"Optimized threshold ({best_threshold:.2f}):"
)

print(
    f"  Accuracy : "
    f"{best_threshold_row['accuracy']:.6f}"
)

print(
    f"  Precision: "
    f"{best_threshold_row['precision']:.6f}"
)

print(
    f"  Recall   : "
    f"{best_threshold_row['recall']:.6f}"
)

print(
    f"  F1       : "
    f"{best_threshold_row['f1']:.6f}"
)


# =============================================================================
# SAVE ALL VALIDATION THRESHOLD RESULTS
# =============================================================================

threshold_df.to_csv(

    THRESHOLD_RESULTS_PATH,

    index=False

)


print()

print(
    "All threshold results saved:"
)

print(
    THRESHOLD_RESULTS_PATH
)


# =============================================================================
# SAVE SELECTED THRESHOLD
# =============================================================================

with open(

    FINAL_THRESHOLD_PATH,

    "w",

    encoding="utf-8"

) as f:

    f.write(
        f"{best_threshold:.2f}\n"
    )


print()

print(
    "Selected threshold saved:"
)

print(
    FINAL_THRESHOLD_PATH
)


# =============================================================================
# IMPORTANT
# =============================================================================
#
# From this point onward the threshold is FROZEN.
#
# We now evaluate it ONCE on the untouched TEST SET.
#
# =============================================================================

print()

print("=" * 80)

print(
    "FREEZING THRESHOLD"
)

print("=" * 80)

print()

print(
    f"FINAL THRESHOLD = {best_threshold:.2f}"
)

print()

print(
    "This threshold was selected using VALIDATION ONLY. ✓"
)

print(
    "Test data has NOT been used for threshold selection. ✓"
)


# =============================================================================
# GENERATE TEST PROBABILITIES
# =============================================================================

print()

print("=" * 80)

print(
    "GENERATING TEST PROBABILITIES"
)

print("=" * 80)

print()

print(
    "IMPORTANT:"
)

print(
    "The test set is being evaluated for the first time"
)

print(
    "after the threshold has been frozen."
)

print()


start = time.time()


test_probabilities = (

    model.predict_proba(

        X_test

    )[:, 1]

)


elapsed = (

    time.time()
    -
    start

) / 60


print(
    f"Test prediction time: {elapsed:.2f} minutes"
)


# =============================================================================
# FINAL TEST METRICS
# =============================================================================

print()

print("=" * 80)

print(
    "FINAL TEST EVALUATION"
)

print("=" * 80)

print()


test_predictions = (

    test_probabilities
    >=
    best_threshold

).astype(np.int8)


test_accuracy = accuracy_score(

    y_test,

    test_predictions

)


test_precision = precision_score(

    y_test,

    test_predictions,

    zero_division=0

)


test_recall = recall_score(

    y_test,

    test_predictions,

    zero_division=0

)


test_f1 = f1_score(

    y_test,

    test_predictions,

    zero_division=0

)


test_roc_auc = roc_auc_score(

    y_test,

    test_probabilities

)


test_pr_auc = average_precision_score(

    y_test,

    test_probabilities

)


print(
    f"Threshold : {best_threshold:.2f}"
)

print()

print(
    f"Accuracy  : {test_accuracy:.4f}"
)

print(
    f"Precision : {test_precision:.4f}"
)

print(
    f"Recall    : {test_recall:.4f}"
)

print(
    f"F1 Score  : {test_f1:.4f}"
)

print(
    f"ROC-AUC   : {test_roc_auc:.4f}"
)

print(
    f"PR-AUC    : {test_pr_auc:.4f}"
)


# =============================================================================
# TEST CONFUSION MATRIX
# =============================================================================

print()

print("=" * 80)

print(
    "FINAL TEST CONFUSION MATRIX"
)

print("=" * 80)

print()


test_cm = confusion_matrix(

    y_test,

    test_predictions

)


print(
    test_cm
)


tn, fp, fn, tp = test_cm.ravel()


print()

print(
    "TN:",
    tn
)

print(
    "FP:",
    fp
)

print(
    "FN:",
    fn
)

print(
    "TP:",
    tp
)


# =============================================================================
# TEST CLASSIFICATION REPORT
# =============================================================================

print()

print("=" * 80)

print(
    "FINAL TEST CLASSIFICATION REPORT"
)

print("=" * 80)

print()


print(

    classification_report(

        y_test,

        test_predictions,

        target_names=[

            "Not Delayed",

            "Delayed >15 min"

        ],

        digits=4,

        zero_division=0

    )

)


# =============================================================================
# COMPARE TEST THRESHOLD 0.50 VS OPTIMIZED
# =============================================================================

print()

print("=" * 80)

print(
    "TEST: THRESHOLD 0.50 VS SELECTED THRESHOLD"
)

print("=" * 80)

print()


test_predictions_050 = (

    test_probabilities
    >=
    0.50

).astype(np.int8)


test_050_accuracy = accuracy_score(

    y_test,

    test_predictions_050

)


test_050_precision = precision_score(

    y_test,

    test_predictions_050,

    zero_division=0

)


test_050_recall = recall_score(

    y_test,

    test_predictions_050,

    zero_division=0

)


test_050_f1 = f1_score(

    y_test,

    test_predictions_050,

    zero_division=0

)


print(
    "TEST THRESHOLD 0.50"
)

print(
    f"Accuracy  : {test_050_accuracy:.4f}"
)

print(
    f"Precision : {test_050_precision:.4f}"
)

print(
    f"Recall    : {test_050_recall:.4f}"
)

print(
    f"F1        : {test_050_f1:.4f}"
)


print()

print(
    f"TEST SELECTED THRESHOLD {best_threshold:.2f}"
)

print(
    f"Accuracy  : {test_accuracy:.4f}"
)

print(
    f"Precision : {test_precision:.4f}"
)

print(
    f"Recall    : {test_recall:.4f}"
)

print(
    f"F1        : {test_f1:.4f}"
)


# =============================================================================
# SAVE FINAL RESULTS
# =============================================================================

print()

print("=" * 80)

print(
    "SAVING STEP 19 RESULTS"
)

print("=" * 80)

print()


final_results = pd.DataFrame(

    [

        {

            "model":
                "V4.2 Baseline",

            "threshold":
                best_threshold,

            "validation_accuracy":
                float(
                    best_threshold_row[
                        "accuracy"
                    ]
                ),

            "validation_precision":
                float(
                    best_threshold_row[
                        "precision"
                    ]
                ),

            "validation_recall":
                float(
                    best_threshold_row[
                        "recall"
                    ]
                ),

            "validation_f1":
                float(
                    best_threshold_row[
                        "f1"
                    ]
                ),

            "validation_roc_auc":
                float(
                    validation_roc_auc
                ),

            "validation_pr_auc":
                float(
                    validation_pr_auc
                ),

            "test_accuracy":
                float(
                    test_accuracy
                ),

            "test_precision":
                float(
                    test_precision
                ),

            "test_recall":
                float(
                    test_recall
                ),

            "test_f1":
                float(
                    test_f1
                ),

            "test_roc_auc":
                float(
                    test_roc_auc
                ),

            "test_pr_auc":
                float(
                    test_pr_auc
                ),

            "tn":
                int(tn),

            "fp":
                int(fp),

            "fn":
                int(fn),

            "tp":
                int(tp)

        }

    ]

)


final_results.to_csv(

    OUTPUT_RESULTS_PATH,

    index=False

)


print(
    "Final results saved:"
)

print(
    OUTPUT_RESULTS_PATH
)


# =============================================================================
# FINAL SUMMARY
# =============================================================================

print()

print("=" * 80)

print(
    "STEP 19 COMPLETE"
)

print("=" * 80)

print()

print(
    "BASE MODEL:"
)

print(
    BASELINE_MODEL_PATH
)

print()

print(
    "SELECTED THRESHOLD:"
)

print(
    f"{best_threshold:.2f}"
)

print()

print(
    "FINAL TEST RESULTS:"
)

print(
    f"Accuracy  : {test_accuracy:.4f}"
)

print(
    f"Precision : {test_precision:.4f}"
)

print(
    f"Recall    : {test_recall:.4f}"
)

print(
    f"F1        : {test_f1:.4f}"
)

print(
    f"ROC-AUC   : {test_roc_auc:.4f}"
)

print(
    f"PR-AUC    : {test_pr_auc:.4f}"
)

print()

print(
    "TEST SET STATUS:"
)

print(
    "✓ NOT USED FOR THRESHOLD SELECTION"
)

print(
    "✓ USED ONLY AFTER THRESHOLD WAS FROZEN"
)

print()

print(
    "OUTPUT:"
)

print(
    OUTPUT_RESULTS_PATH
)

print()

print(
    "✓ LEAKAGE-SAFE THRESHOLD OPTIMIZATION COMPLETE"
)

print(
    "✓ V4.2 BASELINE MODEL RETAINED"
)

print(
    "✓ THRESHOLD FROZEN"
)

print(
    "✓ READY FOR REAL-FLIGHT SANITY TESTING"
)


# =============================================================================
# CLEANUP
# =============================================================================

del X_validation
del X_test

del validation_probabilities
del test_probabilities

del y_train
del y_validation
del y_test

del train_df
del validation_df
del test_df

gc.collect()