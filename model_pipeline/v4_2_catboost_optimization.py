# =============================================================================
# STEP 18 — CONTROLLED CATBOOST HYPERPARAMETER OPTIMIZATION
# =============================================================================
#
# PURPOSE
# -------
# Optimize the V4.2 CatBoost model after the successful V4.1 -> V4.2 ablation.
#
# V4.2 baseline:
#   ROC-AUC : 0.8040
#   PR-AUC  : 0.6333
#   F1      : 0.5538
#
# IMPORTANT EXPERIMENTAL RULES
# ----------------------------
# 1. V4.2 dataset only
# 2. Same chronological train/validation/test split
# 3. Test set NEVER used for hyperparameter selection
# 4. PR-AUC is the PRIMARY optimization metric
# 5. ROC-AUC is SECONDARY
# 6. No threshold optimization
# 7. No test tuning
# 8. Randomized controlled search
# 9. Final selected model evaluated ONCE on test
#
# =============================================================================


import os
import gc
import time
import json
import random

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

OPTIMIZED_MODEL_PATH = (
    r"D:\Cognizant\step18_catboost_v4_2_optimized.cbm"
)

TRIAL_RESULTS_PATH = (
    r"D:\Cognizant\step18_hyperparameter_trials.csv"
)

FINAL_RESULTS_PATH = (
    r"D:\Cognizant\step18_final_results.csv"
)

COMPARISON_PATH = (
    r"D:\Cognizant\step18_v4_2_baseline_vs_optimized.csv"
)

FEATURE_IMPORTANCE_PATH = (
    r"D:\Cognizant\step18_feature_importance.csv"
)

BEST_PARAMS_PATH = (
    r"D:\Cognizant\step18_best_parameters.json"
)


# =============================================================================
# DATA CONFIGURATION
# =============================================================================

EXPECTED_ROWS = 5_714_008

TARGET = "target"

EXPECTED_FEATURES = 68

TRAIN_RATIO = 0.70

VALIDATION_RATIO = 0.15

TEST_RATIO = 0.15

THRESHOLD = 0.50


# =============================================================================
# OPTIMIZATION CONFIGURATION
# =============================================================================
#
# We deliberately do NOT make this excessively large.
#
# Each CatBoost GPU trial takes several minutes on this dataset.
#
# =============================================================================

N_TRIALS = 12

RANDOM_SEED = 42

random.seed(
    RANDOM_SEED
)

np.random.seed(
    RANDOM_SEED
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
# V4.2 FEATURES
# =============================================================================

NEW_V4_2_FEATURES = [

    "previous_flight_arrival_delay",

    "tight_turnaround",

    "is_first_flight_of_day",

    "aircraft_cumulative_delay_today"

]


# =============================================================================
# BASELINE RESULTS FROM STEP 17
# =============================================================================
#
# These are the official V4.2 baseline results already obtained.
#
# =============================================================================

BASELINE_RESULTS = {

    "accuracy": 0.835924,

    "precision": 0.529978,

    "recall": 0.579875,

    "f1": 0.553805,

    "roc_auc": 0.803965,

    "pr_auc": 0.633322

}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def section(title):

    print()
    print("=" * 80)
    print(title)
    print("=" * 80)


def evaluate_predictions(
    y_true,
    probabilities,
    threshold=0.50
):

    predictions = (

        probabilities >= threshold

    ).astype(int)


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


    roc_auc = roc_auc_score(

        y_true,

        probabilities

    )


    pr_auc = average_precision_score(

        y_true,

        probabilities

    )


    cm = confusion_matrix(

        y_true,

        predictions

    )


    tn, fp, fn, tp = cm.ravel()


    return {

        "accuracy": accuracy,

        "precision": precision,

        "recall": recall,

        "f1": f1,

        "roc_auc": roc_auc,

        "pr_auc": pr_auc,

        "tn": int(tn),

        "fp": int(fp),

        "fn": int(fn),

        "tp": int(tp)

    }


# =============================================================================
# SEARCH SPACE
# =============================================================================
#
# These ranges are deliberately reasonable for CatBoost on this dataset.
#
# =============================================================================

SEARCH_SPACE = {

    "depth": [
        7,
        8,
        9,
        10
    ],

    "learning_rate": [
        0.03,
        0.05,
        0.07,
        0.10
    ],

    "l2_leaf_reg": [
        3,
        5,
        8,
        12,
        20
    ],

    "random_strength": [
        0.5,
        1.0,
        1.5,
        2.0
    ],

    "bagging_temperature": [
        0,
        0.5,
        1.0,
        2.0
    ],

    "border_count": [
        64,
        128,
        254
    ]

}


# =============================================================================
# GENERATE CONTROLLED TRIALS
# =============================================================================

def generate_trials():

    trials = []

    seen = set()

    while len(trials) < N_TRIALS:

        params = {

            "depth": random.choice(
                SEARCH_SPACE["depth"]
            ),

            "learning_rate": random.choice(
                SEARCH_SPACE["learning_rate"]
            ),

            "l2_leaf_reg": random.choice(
                SEARCH_SPACE["l2_leaf_reg"]
            ),

            "random_strength": random.choice(
                SEARCH_SPACE["random_strength"]
            ),

            "bagging_temperature": random.choice(
                SEARCH_SPACE["bagging_temperature"]
            ),

            "border_count": random.choice(
                SEARCH_SPACE["border_count"]
            )

        }


        key = tuple(
            params.items()
        )


        if key in seen:

            continue


        seen.add(key)

        trials.append(
            params
        )


    return trials


# =============================================================================
# START
# =============================================================================

section(
    "STEP 18 — CONTROLLED CATBOOST HYPERPARAMETER OPTIMIZATION"
)

print(
    "Dataset:",
    V4_2_PATH
)

print()

print(
    "V4.2 features:",
    EXPECTED_FEATURES
)

print(
    "Optimization trials:",
    N_TRIALS
)

print(
    "Primary metric: PR-AUC"
)

print(
    "Secondary metric: ROC-AUC"
)

print(
    "Threshold:",
    THRESHOLD
)

print(
    "Bayesian optimization: NO"
)

print(
    "Test tuning: NO"
)

print(
    "Test set usage during optimization: NONE"
)


# =============================================================================
# CHECK INPUT
# =============================================================================

section(
    "CHECKING INPUT DATASET"
)

if not os.path.exists(
    V4_2_PATH
):

    raise FileNotFoundError(
        V4_2_PATH
    )

print(
    "V4.2 dataset found. ✓"
)


# =============================================================================
# LOAD DATA
# =============================================================================

section(
    "LOADING V4.2 DATASET"
)

start = time.time()

df = pd.read_csv(

    V4_2_PATH,

    low_memory=False

)

load_time = (

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
    "Loading time:",
    f"{load_time:.2f} minutes"
)


# =============================================================================
# ROW VALIDATION
# =============================================================================

if len(df) != EXPECTED_ROWS:

    raise ValueError(

        f"Expected {EXPECTED_ROWS:,} rows "
        f"but found {len(df):,}"

    )

print(
    "Row count confirmed. ✓"
)


# =============================================================================
# TARGET VALIDATION
# =============================================================================

section(
    "TARGET VALIDATION"
)

if TARGET not in df.columns:

    raise ValueError(
        "Target column missing."
    )


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
# FEATURE IDENTIFICATION
# =============================================================================

section(
    "IDENTIFYING MODEL FEATURES"
)

model_features = [

    c
    for c in df.columns
    if c != TARGET

]


print(
    "Total model features:",
    len(model_features)
)


if len(model_features) != EXPECTED_FEATURES:

    raise ValueError(

        f"Expected {EXPECTED_FEATURES} "
        f"features but found "
        f"{len(model_features)}"

    )

print(
    "68 features confirmed. ✓"
)


# =============================================================================
# VALIDATE V4.2 FEATURES
# =============================================================================

section(
    "VALIDATING V4.2 FEATURES"
)

for feature in NEW_V4_2_FEATURES:

    if feature not in model_features:

        raise ValueError(
            f"Missing V4.2 feature: {feature}"
        )

    print(
        f"✓ {feature}"
    )


# =============================================================================
# PREPARE CATEGORICAL FEATURES
# =============================================================================

section(
    "PREPARING CATEGORICAL FEATURES"
)

for feature in CATEGORICAL_FEATURES:

    df[feature] = (

        df[feature]

        .astype("string")

        .fillna("__MISSING__")

        .astype(str)

    )


print(
    "Categorical preparation complete. ✓"
)


# =============================================================================
# CHRONOLOGICAL SPLIT
# =============================================================================

section(
    "CREATING CHRONOLOGICAL TRAIN / VALIDATION / TEST SPLIT"
)

train_end = int(

    len(df)
    *
    TRAIN_RATIO

)

validation_end = int(

    len(df)
    *
    (
        TRAIN_RATIO
        +
        VALIDATION_RATIO
    )

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
    "Training rows:",
    f"{len(train_df):,}"
)

print(
    "Validation rows:",
    f"{len(validation_df):,}"
)

print(
    "Test rows:",
    f"{len(test_df):,}"
)


# =============================================================================
# EXACT SPLIT VALIDATION
# =============================================================================

if len(train_df) != 3_999_805:

    raise ValueError(
        "Training split mismatch."
    )


if len(validation_df) != 857_101:

    raise ValueError(
        "Validation split mismatch."
    )


if len(test_df) != 857_102:

    raise ValueError(
        "Test split mismatch."
    )


print(
    "Chronological split confirmed. ✓"
)


# =============================================================================
# TARGET ARRAYS
# =============================================================================

y_train = train_df[
    TARGET
]

y_validation = validation_df[
    TARGET
]

y_test = test_df[
    TARGET
]


# =============================================================================
# CLASS WEIGHT
# =============================================================================

section(
    "CALCULATING CLASS WEIGHT"
)

negative_count = int(

    (y_train == 0).sum()

)

positive_count = int(

    (y_train == 1).sum()

)


scale_positive_weight = (

    negative_count
    /
    positive_count

)


print(
    "Not delayed:",
    f"{negative_count:,}"
)

print(
    "Delayed:",
    f"{positive_count:,}"
)

print(
    "Scale positive weight:",
    f"{scale_positive_weight:.6f}"
)


# =============================================================================
# TRAINING MATRICES
# =============================================================================

section(
    "CREATING TRAINING MATRICES"
)

X_train = train_df[
    model_features
]

X_validation = validation_df[
    model_features
]

X_test = test_df[
    model_features
]


print(
    "X_train:",
    X_train.shape
)

print(
    "X_validation:",
    X_validation.shape
)

print(
    "X_test:",
    X_test.shape
)


# =============================================================================
# GENERATE TRIALS
# =============================================================================

section(
    "GENERATING CONTROLLED HYPERPARAMETER TRIALS"
)

trials = generate_trials()


# Always include the existing V4.2 baseline as Trial 0.

baseline_params = {

    "depth": 9,

    "learning_rate": 0.07,

    "l2_leaf_reg": 5,

    "random_strength": 1.0,

    "bagging_temperature": 0.0,

    "border_count": 128

}


trials.insert(
    0,
    baseline_params
)


# Remove duplicate baseline if random search generated it.

unique_trials = []

seen = set()

for params in trials:

    key = tuple(
        sorted(
            params.items()
        )
    )

    if key not in seen:

        seen.add(key)

        unique_trials.append(
            params
        )


trials = unique_trials


print(
    "Total trials:",
    len(trials)
)


# =============================================================================
# DISPLAY TRIALS
# =============================================================================

for i, params in enumerate(
    trials
):

    print()

    print(
        f"Trial {i}"
    )

    print(
        params
    )


# =============================================================================
# OPTIMIZATION LOOP
# =============================================================================

section(
    "STARTING HYPERPARAMETER OPTIMIZATION"
)

trial_results = []

best_pr_auc = -np.inf

best_roc_auc = -np.inf

best_trial_id = None

best_params = None

best_model = None


for trial_id, params in enumerate(
    trials
):

    print()
    print(
        "=" * 80
    )

    print(
        f"TRIAL {trial_id + 1}/{len(trials)}"
    )

    print(
        "=" * 80
    )

    print(
        "Parameters:"
    )

    for key, value in params.items():

        print(
            f"  {key}: {value}"
        )


    model = CatBoostClassifier(

        iterations=1000,

        depth=params[
            "depth"
        ],

        learning_rate=params[
            "learning_rate"
        ],

        l2_leaf_reg=params[
            "l2_leaf_reg"
        ],

        random_strength=params[
            "random_strength"
        ],

        bagging_temperature=params[
            "bagging_temperature"
        ],

        border_count=params[
            "border_count"
        ],

        random_seed=42,

        loss_function="Logloss",

        eval_metric="AUC",

        class_weights=[

            1.0,

            scale_positive_weight

        ],

        task_type="GPU",

        verbose=100

    )


    start_trial = time.time()


    try:

        model.fit(

            X_train,

            y_train,

            cat_features=CATEGORICAL_FEATURES,

            eval_set=(

                X_validation,

                y_validation

            ),

            use_best_model=True

        )


        trial_time = (

            time.time()
            -
            start_trial

        ) / 60


        validation_probabilities = (

            model.predict_proba(

                X_validation

            )[:, 1]

        )


        validation_metrics = evaluate_predictions(

            y_validation,

            validation_probabilities,

            THRESHOLD

        )


        trial_result = {

            "trial":

                trial_id,

            "depth":

                params[
                    "depth"
                ],

            "learning_rate":

                params[
                    "learning_rate"
                ],

            "l2_leaf_reg":

                params[
                    "l2_leaf_reg"
                ],

            "random_strength":

                params[
                    "random_strength"
                ],

            "bagging_temperature":

                params[
                    "bagging_temperature"
                ],

            "border_count":

                params[
                    "border_count"
                ],

            "best_iteration":

                model.get_best_iteration(),

            "validation_accuracy":

                validation_metrics[
                    "accuracy"
                ],

            "validation_precision":

                validation_metrics[
                    "precision"
                ],

            "validation_recall":

                validation_metrics[
                    "recall"
                ],

            "validation_f1":

                validation_metrics[
                    "f1"
                ],

            "validation_roc_auc":

                validation_metrics[
                    "roc_auc"
                ],

            "validation_pr_auc":

                validation_metrics[
                    "pr_auc"
                ],

            "training_time_minutes":

                trial_time,

            "status":

                "SUCCESS"

        }


        trial_results.append(
            trial_result
        )


        print()

        print(
            "Trial validation results:"
        )

        print(
            f"  PR-AUC  : "
            f"{validation_metrics['pr_auc']:.6f}"
        )

        print(
            f"  ROC-AUC : "
            f"{validation_metrics['roc_auc']:.6f}"
        )

        print(
            f"  F1      : "
            f"{validation_metrics['f1']:.6f}"
        )

        print(
            f"  Time    : "
            f"{trial_time:.2f} min"
        )


        # =============================================================
        # PRIMARY SELECTION:
        # PR-AUC
        #
        # SECONDARY:
        # ROC-AUC
        # =============================================================

        is_better = (

            validation_metrics[
                "pr_auc"
            ]
            >
            best_pr_auc

        )


        if is_better:

            best_pr_auc = (

                validation_metrics[
                    "pr_auc"
                ]

            )

            best_roc_auc = (

                validation_metrics[
                    "roc_auc"
                ]

            )

            best_trial_id = trial_id

            best_params = params.copy()

            best_model = model

            print()

            print(
                "✓ NEW BEST TRIAL"
            )

            print(
                f"Best validation PR-AUC: "
                f"{best_pr_auc:.6f}"
            )

            print(
                f"Best validation ROC-AUC: "
                f"{best_roc_auc:.6f}"
            )


        else:

            del model

            gc.collect()


    except Exception as e:

        trial_time = (

            time.time()
            -
            start_trial

        ) / 60


        print()

        print(
            "❌ TRIAL FAILED"
        )

        print(
            str(e)
        )


        trial_results.append(

            {

                "trial":
                    trial_id,

                **params,

                "best_iteration":
                    np.nan,

                "validation_accuracy":
                    np.nan,

                "validation_precision":
                    np.nan,

                "validation_recall":
                    np.nan,

                "validation_f1":
                    np.nan,

                "validation_roc_auc":
                    np.nan,

                "validation_pr_auc":
                    np.nan,

                "training_time_minutes":
                    trial_time,

                "status":
                    "FAILED"

            }

        )

        gc.collect()


# =============================================================================
# OPTIMIZATION RESULTS
# =============================================================================

section(
    "HYPERPARAMETER OPTIMIZATION COMPLETE"
)

trial_results_df = pd.DataFrame(
    trial_results
)


successful_trials = (

    trial_results_df[
        trial_results_df[
            "status"
        ]
        ==
        "SUCCESS"
    ]

)


print(
    "Successful trials:",
    len(successful_trials)
)

print(
    "Failed trials:",
    len(trial_results_df)
    -
    len(successful_trials)
)


if len(successful_trials) == 0:

    raise RuntimeError(
        "No successful optimization trials."
    )


successful_trials = (

    successful_trials

    .sort_values(

        [
            "validation_pr_auc",
            "validation_roc_auc"

        ],

        ascending=False

    )

)


print()

print(
    "TOP TRIALS:"
)

print(

    successful_trials.head(
        10
    ).to_string(
        index=False
    )

)


# =============================================================================
# BEST PARAMETERS
# =============================================================================

section(
    "BEST HYPERPARAMETERS"
)

best_row = (

    successful_trials
    .iloc[0]
)


best_trial_id = int(
    best_row["trial"]
)


best_params = {

    "depth":
        int(best_row["depth"]),

    "learning_rate":
        float(best_row["learning_rate"]),

    "l2_leaf_reg":
        float(best_row["l2_leaf_reg"]),

    "random_strength":
        float(best_row["random_strength"]),

    "bagging_temperature":
        float(best_row["bagging_temperature"]),

    "border_count":
        int(best_row["border_count"])

}


for key, value in best_params.items():

    print(
        f"{key}: {value}"
    )


print()

print(
    "Best validation PR-AUC:",
    f"{best_row['validation_pr_auc']:.6f}"
)

print(
    "Best validation ROC-AUC:",
    f"{best_row['validation_roc_auc']:.6f}"
)

print(
    "Best validation F1:",
    f"{best_row['validation_f1']:.6f}"
)

print(
    "Best iteration:",
    int(
        best_row["best_iteration"]
    )
)


# =============================================================================
# SAVE TRIAL RESULTS
# =============================================================================

trial_results_df.to_csv(

    TRIAL_RESULTS_PATH,

    index=False

)

print()

print(
    "Trial results saved:"
)

print(
    TRIAL_RESULTS_PATH
)


# =============================================================================
# SAVE BEST PARAMETERS
# =============================================================================

best_parameters_output = {

    "best_trial":
        best_trial_id,

    "selection_metric":
        "validation_pr_auc",

    "secondary_metric":
        "validation_roc_auc",

    "best_validation_pr_auc":
        float(
            best_row[
                "validation_pr_auc"
            ]
        ),

    "best_validation_roc_auc":
        float(
            best_row[
                "validation_roc_auc"
            ]
        ),

    "best_iteration":
        int(
            best_row[
                "best_iteration"
            ]
        ),

    "parameters":
        best_params

}


with open(

    BEST_PARAMS_PATH,

    "w",

    encoding="utf-8"

) as f:

    json.dump(

        best_parameters_output,

        f,

        indent=4

    )


print(
    "Best parameters saved:"
)

print(
    BEST_PARAMS_PATH
)


# =============================================================================
# SAVE BEST MODEL
# =============================================================================

section(
    "SAVING BEST OPTIMIZED MODEL"
)

if best_model is None:

    raise RuntimeError(
        "Best model object unavailable."
    )


best_model.save_model(

    OPTIMIZED_MODEL_PATH

)


print(
    "Optimized model saved:"
)

print(
    OPTIMIZED_MODEL_PATH
)


# =============================================================================
# VALIDATION EVALUATION OF BEST MODEL
# =============================================================================

section(
    "BEST MODEL VALIDATION EVALUATION"
)

best_validation_probabilities = (

    best_model.predict_proba(

        X_validation

    )[:, 1]

)


best_validation_metrics = evaluate_predictions(

    y_validation,

    best_validation_probabilities,

    THRESHOLD

)


print(
    f"Accuracy  : "
    f"{best_validation_metrics['accuracy']:.4f}"
)

print(
    f"Precision : "
    f"{best_validation_metrics['precision']:.4f}"
)

print(
    f"Recall    : "
    f"{best_validation_metrics['recall']:.4f}"
)

print(
    f"F1        : "
    f"{best_validation_metrics['f1']:.4f}"
)

print(
    f"ROC-AUC   : "
    f"{best_validation_metrics['roc_auc']:.4f}"
)

print(
    f"PR-AUC    : "
    f"{best_validation_metrics['pr_auc']:.4f}"
)


# =============================================================================
# IMPORTANT:
# FINAL TEST EVALUATION
#
# The test set has NOT been used in ANY optimization decision.
#
# This is the FIRST time the selected optimized model sees test data.
# =============================================================================

section(
    "FINAL TEST EVALUATION — UNTOUCHED TEST SET"
)

print(
    "IMPORTANT:"
)

print(
    "The test set was NOT used during hyperparameter selection."
)

print(
    "Threshold remains fixed at 0.50."
)

print(
    "This is the final unbiased V4.2 optimized evaluation."
)


test_probabilities = (

    best_model.predict_proba(

        X_test

    )[:, 1]

)


test_metrics = evaluate_predictions(

    y_test,

    test_probabilities,

    THRESHOLD

)


print()

print(
    "FINAL V4.2 OPTIMIZED TEST RESULTS"
)

print()

print(
    f"Accuracy  : "
    f"{test_metrics['accuracy']:.4f}"
)

print(
    f"Precision : "
    f"{test_metrics['precision']:.4f}"
)

print(
    f"Recall    : "
    f"{test_metrics['recall']:.4f}"
)

print(
    f"F1 Score  : "
    f"{test_metrics['f1']:.4f}"
)

print(
    f"ROC-AUC   : "
    f"{test_metrics['roc_auc']:.4f}"
)

print(
    f"PR-AUC    : "
    f"{test_metrics['pr_auc']:.4f}"
)


# =============================================================================
# CONFUSION MATRIX
# =============================================================================

section(
    "FINAL TEST CONFUSION MATRIX"
)

cm = confusion_matrix(

    y_test,

    (
        test_probabilities
        >=
        THRESHOLD
    ).astype(int)

)


print(
    cm
)


tn, fp, fn, tp = cm.ravel()


print()

print(
    "TP:",
    tp
)

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


# =============================================================================
# CLASSIFICATION REPORT
# =============================================================================

section(
    "FINAL TEST CLASSIFICATION REPORT"
)

print(

    classification_report(

        y_test,

        (
            test_probabilities
            >=
            THRESHOLD
        ).astype(int),

        target_names=[

            "Not Delayed",

            "Delayed >15 min"

        ],

        digits=4,

        zero_division=0

    )

)


# =============================================================================
# BASELINE VS OPTIMIZED
# =============================================================================

section(
    "V4.2 BASELINE VS OPTIMIZED MODEL"
)

comparison_rows = [

    {

        "model":
            "V4.2 Baseline",

        "features":
            68,

        "accuracy":
            BASELINE_RESULTS[
                "accuracy"
            ],

        "precision":
            BASELINE_RESULTS[
                "precision"
            ],

        "recall":
            BASELINE_RESULTS[
                "recall"
            ],

        "f1":
            BASELINE_RESULTS[
                "f1"
            ],

        "roc_auc":
            BASELINE_RESULTS[
                "roc_auc"
            ],

        "pr_auc":
            BASELINE_RESULTS[
                "pr_auc"
            ]

    },

    {

        "model":
            "V4.2 Optimized",

        "features":
            68,

        "accuracy":
            test_metrics[
                "accuracy"
            ],

        "precision":
            test_metrics[
                "precision"
            ],

        "recall":
            test_metrics[
                "recall"
            ],

        "f1":
            test_metrics[
                "f1"
            ],

        "roc_auc":
            test_metrics[
                "roc_auc"
            ],

        "pr_auc":
            test_metrics[
                "pr_auc"
            ]

    }

]


comparison_df = pd.DataFrame(
    comparison_rows
)


print(
    comparison_df.to_string(
        index=False
    )
)


# =============================================================================
# CALCULATE CHANGES
# =============================================================================

section(
    "OPTIMIZATION PERFORMANCE CHANGE"
)

metrics = [

    "accuracy",

    "precision",

    "recall",

    "f1",

    "roc_auc",

    "pr_auc"

]


change_rows = []


for metric in metrics:

    baseline = (

        BASELINE_RESULTS[
            metric
        ]

    )

    optimized = (

        test_metrics[
            metric
        ]

    )

    absolute_change = (

        optimized
        -
        baseline

    )

    relative_change = (

        absolute_change
        /
        baseline
        *
        100

    )


    change_rows.append(

        {

            "metric":
                metric,

            "baseline":
                baseline,

            "optimized":
                optimized,

            "absolute_change":
                absolute_change,

            "relative_change_percent":
                relative_change

        }

    )


change_df = pd.DataFrame(
    change_rows
)


print(
    change_df.to_string(
        index=False
    )
)


# =============================================================================
# FEATURE IMPORTANCE
# =============================================================================

section(
    "OPTIMIZED MODEL FEATURE IMPORTANCE"
)

importance = (

    best_model
    .get_feature_importance()

)


feature_importance_df = pd.DataFrame(

    {

        "feature":
            model_features,

        "importance":
            importance

    }

)


feature_importance_df = (

    feature_importance_df

    .sort_values(

        "importance",

        ascending=False

    )

    .reset_index(
        drop=True
    )

)


print(

    feature_importance_df.head(
        30
    ).to_string(
        index=False
    )

)


# =============================================================================
# V4.2 FEATURE IMPORTANCE
# =============================================================================

section(
    "V4.2 NEW FEATURE IMPORTANCE"
)

new_importance = (

    feature_importance_df[

        feature_importance_df[
            "feature"
        ].isin(
            NEW_V4_2_FEATURES
        )

    ]

)


print(
    new_importance.to_string(
        index=False
    )
)


# =============================================================================
# SAVE FEATURE IMPORTANCE
# =============================================================================

feature_importance_df.to_csv(

    FEATURE_IMPORTANCE_PATH,

    index=False

)


print()

print(
    "Feature importance saved:"
)

print(
    FEATURE_IMPORTANCE_PATH
)


# =============================================================================
# SAVE FINAL RESULTS
# =============================================================================

section(
    "SAVING FINAL STEP 18 RESULTS"
)

final_results = pd.DataFrame(

    [

        {

            "model":
                "V4.2 Optimized",

            "features":
                68,

            "threshold":
                THRESHOLD,

            "accuracy":
                test_metrics[
                    "accuracy"
                ],

            "precision":
                test_metrics[
                    "precision"
                ],

            "recall":
                test_metrics[
                    "recall"
                ],

            "f1":
                test_metrics[
                    "f1"
                ],

            "roc_auc":
                test_metrics[
                    "roc_auc"
                ],

            "pr_auc":
                test_metrics[
                    "pr_auc"
                ],

            "tp":
                test_metrics[
                    "tp"
                ],

            "tn":
                test_metrics[
                    "tn"
                ],

            "fp":
                test_metrics[
                    "fp"
                ],

            "fn":
                test_metrics[
                    "fn"
                ],

            "best_trial":
                best_trial_id,

            "best_iteration":
                int(
                    best_row[
                        "best_iteration"
                    ]
                )

        }

    ]

)


final_results.to_csv(

    FINAL_RESULTS_PATH,

    index=False

)


comparison_df.to_csv(

    COMPARISON_PATH,

    index=False

)


print(
    "Final results saved:"
)

print(
    FINAL_RESULTS_PATH
)

print()

print(
    "Baseline comparison saved:"
)

print(
    COMPARISON_PATH
)


# =============================================================================
# FINAL DECISION
# =============================================================================

section(
    "STEP 18 — FINAL DECISION"
)

baseline_pr = (

    BASELINE_RESULTS[
        "pr_auc"
    ]

)

optimized_pr = (

    test_metrics[
        "pr_auc"
    ]

)


baseline_roc = (

    BASELINE_RESULTS[
        "roc_auc"
    ]

)

optimized_roc = (

    test_metrics[
        "roc_auc"
    ]

)


baseline_f1 = (

    BASELINE_RESULTS[
        "f1"
    ]

)

optimized_f1 = (

    test_metrics[
        "f1"
    ]

)


print(
    f"Baseline PR-AUC : {baseline_pr:.4f}"
)

print(
    f"Optimized PR-AUC: {optimized_pr:.4f}"
)

print()

print(
    f"Baseline ROC-AUC : {baseline_roc:.4f}"
)

print(
    f"Optimized ROC-AUC: {optimized_roc:.4f}"
)

print()

print(
    f"Baseline F1 : {baseline_f1:.4f}"
)

print(
    f"Optimized F1: {optimized_f1:.4f}"
)

print()


if optimized_pr > baseline_pr:

    print(
        "✓ Optimized model improved PR-AUC."
    )

else:

    print(
        "⚠ Optimized model did not improve PR-AUC."
    )


if optimized_roc > baseline_roc:

    print(
        "✓ Optimized model improved ROC-AUC."
    )

else:

    print(
        "⚠ Optimized model did not improve ROC-AUC."
    )


if optimized_f1 > baseline_f1:

    print(
        "✓ Optimized model improved F1."
    )

else:

    print(
        "⚠ Optimized model did not improve F1."
    )


# =============================================================================
# CLEANUP
# =============================================================================

del X_train
del X_validation
del X_test

del y_train
del y_validation
del y_test

del train_df
del validation_df
del test_df

gc.collect()


# =============================================================================
# FINAL SUMMARY
# =============================================================================

section(
    "STEP 18 COMPLETE"
)

print(
    "V4.2 features:",
    68
)

print(
    "Optimization trials:",
    len(trial_results_df)
)

print(
    "Best trial:",
    best_trial_id
)

print()

print(
    "FINAL TEST RESULTS"
)

print(
    f"Accuracy  : {test_metrics['accuracy']:.4f}"
)

print(
    f"Precision : {test_metrics['precision']:.4f}"
)

print(
    f"Recall    : {test_metrics['recall']:.4f}"
)

print(
    f"F1        : {test_metrics['f1']:.4f}"
)

print(
    f"ROC-AUC   : {test_metrics['roc_auc']:.4f}"
)

print(
    f"PR-AUC    : {test_metrics['pr_auc']:.4f}"
)

print()

print(
    "OPTIMIZED MODEL:"
)

print(
    OPTIMIZED_MODEL_PATH
)

print()

print(
    "TRIAL RESULTS:"
)

print(
    TRIAL_RESULTS_PATH
)

print()

print(
    "BEST PARAMETERS:"
)

print(
    BEST_PARAMS_PATH
)

print()

print(
    "✓ HYPERPARAMETER OPTIMIZATION COMPLETE"
)

print(
    "✓ TEST SET WAS KEPT UNTOUCHED DURING SEARCH"
)

print(
    "✓ FINAL OPTIMIZED MODEL EVALUATED ON TEST"
)