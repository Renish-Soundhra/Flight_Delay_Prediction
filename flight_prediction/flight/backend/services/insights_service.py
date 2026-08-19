import os

import numpy as np
from sklearn.inspection import permutation_importance
from sklearn.metrics import f1_score

from models.model_loader import model_loader
from utils.feature_processor import build_features, prepare_model_input
from utils.test_data_loader import get_test_feature_baselines, load_test_data


FEATURE_LABELS = {
    "AIRLINE": "Airline",
    "FLIGHT_NUMBER": "Flight Number",
    "TAIL_NUMBER": "Tail Number",
    "ORIGIN_AIRPORT": "Origin Airport",
    "DESTINATION_AIRPORT": "Destination Airport",
    "SCHEDULED_TIME": "Scheduled Flight Time",
    "DISTANCE": "Distance",
    "departure_hour": "Departure Hour",
    "departure_minute": "Departure Minute",
    "is_weekend": "Weekend Travel",
    "departure_hour_sin": "Departure Hour Pattern",
    "departure_hour_cos": "Departure Hour Pattern",
    "day_of_week_sin": "Day of Week Pattern",
    "day_of_week_cos": "Day of Week Pattern",
    "departure_day_of_week": "Day of Week",
    "departure_day": "Day of Month",
    "departure_month": "Departure Month",
    "departure_day_of_year": "Day of Year",
    "departure_week": "Week of Year",
    "AIRLINE_NAME": "Airline Name",
    "origin_state": "Origin State",
    "origin_latitude": "Origin Latitude",
    "origin_longitude": "Origin Longitude",
    "destination_state": "Destination State",
    "destination_latitude": "Destination Latitude",
    "destination_longitude": "Destination Longitude",
    "same_state": "Same State Route",
    "route_geographic_distance_km": "Geographic Route Distance",
    "distance_per_scheduled_min": "Distance per Scheduled Minute",
    "scheduled_speed_proxy": "Scheduled Speed",
    "ROUTE": "Route",
    "previous_flight_departure_delay": "Previous Flight Departure Delay",
    "previous_flight_delayed": "Previous Flight Delayed",
    "previous_delay_magnitude": "Previous Delay Magnitude",
    "time_since_previous_flight_min": "Time Since Previous Flight",
    "valid_aircraft_connection": "Valid Aircraft Connection",
    "scheduled_turnaround_min": "Scheduled Turnaround",
    "remaining_turnaround_min": "Remaining Turnaround",
    "turnaround_stress_min": "Turnaround Stress",
    "buffer_ratio": "Schedule Buffer Ratio",
    "propagation_pressure": "Delay Propagation Pressure",
    "propagation_risk": "Delay Propagation Risk",
    "aircraft_past_flights": "Aircraft Past Flights",
    "aircraft_delay_rate": "Aircraft Delay Rate",
    "aircraft_avg_departure_delay": "Aircraft Average Departure Delay",
    "airline_past_flights": "Airline Past Flights",
    "airline_delay_rate": "Airline Delay Rate",
    "airline_avg_departure_delay": "Airline Average Departure Delay",
    "route_past_flights": "Route Past Flights",
    "route_delay_rate": "Route Delay Rate",
    "route_avg_departure_delay": "Route Average Departure Delay",
    "origin_past_flights": "Origin Past Flights",
    "origin_delay_rate": "Origin Delay Rate",
    "origin_avg_departure_delay": "Origin Average Departure Delay",
    "destination_past_flights": "Destination Past Flights",
    "destination_delay_rate": "Destination Delay Rate",
    "destination_avg_departure_delay": "Destination Average Departure Delay",
    "route_vs_airline_delay_rate": "Route vs Airline Delay Rate",
    "origin_vs_airline_delay_rate": "Origin vs Airline Delay Rate",
    "destination_vs_airline_delay_rate": "Destination vs Airline Delay Rate",
    "route_history_strength": "Route History Strength",
    "airline_history_strength": "Airline History Strength",
    "origin_history_strength": "Origin History Strength",
    "destination_history_strength": "Destination History Strength",
    "previous_flight_arrival_delay": "Previous Flight Arrival Delay",
    "tight_turnaround": "Tight Turnaround",
    "is_first_flight_of_day": "First Flight of Day",
    "aircraft_cumulative_delay_today": "Aircraft Cumulative Delay Today",
}

DAY_NAMES = {
    1: "Monday",
    2: "Tuesday",
    3: "Wednesday",
    4: "Thursday",
    5: "Friday",
    6: "Saturday",
    7: "Sunday",
}

MONTH_NAMES = {
    1: "January",
    2: "February",
    3: "March",
    4: "April",
    5: "May",
    6: "June",
    7: "July",
    8: "August",
    9: "September",
    10: "October",
    11: "November",
    12: "December",
}

# Match the VS Code HistGradientBoosting evaluation:
# permutation_importance on 20,000 validation rows, n_repeats=3,
# scoring="average_precision" (PR-AUC). Do not use the reconstructed
# test_data.npz sample — that file zeros aircraft-history features.
PERMUTATION_REPEATS = 3
PERMUTATION_RANDOM_STATE = 42
PERMUTATION_MAX_SAMPLES = 20000
SCORING_METRIC = "average_precision"

_cached_permutation_importance = None
_cached_feature_baselines = None
_cached_permutation_error = None


def _feature_columns():
    if model_loader.preprocessing is None:
        raise RuntimeError("Preprocessing artifact is not loaded")
    return model_loader.preprocessing["feature_columns"]


def _feature_label(feature_name):
    return FEATURE_LABELS.get(
        feature_name,
        feature_name.replace("_", " ").title(),
    )


def _threshold_f1_scorer(estimator, X, y):
    probabilities = estimator.predict_proba(X)[:, 1]
    predictions = (probabilities >= model_loader.threshold).astype(int)
    return f1_score(y, predictions, zero_division=0)


def _compute_permutation_importance():
    if not model_loader.is_ready:
        raise RuntimeError(
            model_loader.load_error or "Prediction model is not loaded"
        )

    feature_columns = _feature_columns()
    X_eval, y_eval = load_test_data(
        max_samples=PERMUTATION_MAX_SAMPLES,
        random_state=PERMUTATION_RANDOM_STATE,
        prefer_permutation_sample=True,
    )

    if X_eval.shape[1] != len(feature_columns):
        raise RuntimeError(
            f"Permutation sample has {X_eval.shape[1]} columns but the "
            f"preprocessing artifact lists {len(feature_columns)} features."
        )

    n_jobs = -1 if os.name != "nt" else 1

    result = permutation_importance(
        model_loader.model,
        X_eval,
        y_eval,
        n_repeats=PERMUTATION_REPEATS,
        random_state=PERMUTATION_RANDOM_STATE,
        scoring=SCORING_METRIC,
        n_jobs=n_jobs,
    )

    ranked = sorted(
        [
            {
                "feature_index": index,
                "feature": feature_columns[index],
                "label": _feature_label(feature_columns[index]),
                "importance": float(result.importances_mean[index]),
                "importance_mean": float(result.importances_mean[index]),
                "importance_std": float(result.importances_std[index]),
                "std": float(result.importances_std[index]),
            }
            for index in range(len(feature_columns))
        ],
        key=lambda item: item["importance"],
        reverse=True,
    )

    print("Permutation importance verification (all 68 features)")
    print("Index | Feature | Importance Mean | Importance Std")
    for item in sorted(ranked, key=lambda row: row["feature_index"]):
        print(
            f"{item['feature_index']:02d} | {item['feature']} | "
            f"{item['importance_mean']:.6f} | {item['importance_std']:.6f}"
        )

    return {
        "ranked_features": ranked,
        "evaluation_samples": int(len(y_eval)),
        "evaluation_split": "validation",
        "scoring_metric": SCORING_METRIC,
        "n_repeats": PERMUTATION_REPEATS,
        "n_features": len(feature_columns),
        "feature_order_source": "preprocessing.pkl feature_columns",
        "sample_source": "permutation_sample.npz (X_val.dat, 20k, seed=42)",
    }


def get_global_feature_importance(top_n=20):
    global _cached_permutation_importance, _cached_permutation_error

    if _cached_permutation_importance is None and _cached_permutation_error is None:
        try:
            _cached_permutation_importance = _compute_permutation_importance()
        except Exception as exc:
            _cached_permutation_error = str(exc)
            raise

    if _cached_permutation_importance is None:
        raise RuntimeError(_cached_permutation_error or "Permutation importance unavailable")

    ranked = _cached_permutation_importance["ranked_features"]
    limit = len(ranked) if top_n is None else top_n

    return {
        "model_name": model_loader.model_name,
        "method": "permutation_importance",
        "scoring_metric": _cached_permutation_importance["scoring_metric"],
        "scoring_label": "Mean decrease in average precision (PR-AUC)",
        "n_repeats": _cached_permutation_importance["n_repeats"],
        "evaluation_dataset": _cached_permutation_importance.get(
            "evaluation_split", "validation"
        ),
        "evaluation_samples": _cached_permutation_importance["evaluation_samples"],
        "sample_source": _cached_permutation_importance.get("sample_source"),
        "feature_order_source": _cached_permutation_importance.get(
            "feature_order_source"
        ),
        "top_features": ranked[:limit],
        "all_features": ranked,
        "total_features": len(ranked),
    }


def _get_feature_baselines():
    global _cached_feature_baselines
    if _cached_feature_baselines is None:
        _cached_feature_baselines = get_test_feature_baselines(
            max_samples=PERMUTATION_MAX_SAMPLES
        )
    return _cached_feature_baselines


def _explain_feature(feature_name, raw_features, encoded_value):
    label = _feature_label(feature_name)

    if feature_name == "AIRLINE":
        airline = raw_features.get("AIRLINE", "the selected airline")
        return (
            f"The selected airline ({airline}) is associated with delay patterns "
            "learned by the model for this flight."
        )

    if feature_name == "ORIGIN_AIRPORT":
        origin = raw_features.get("ORIGIN_AIRPORT", "the origin")
        return (
            f"Departing from {origin} influences this prediction based on historical "
            "origin delay patterns."
        )

    if feature_name == "DESTINATION_AIRPORT":
        destination = raw_features.get("DESTINATION_AIRPORT", "the destination")
        return (
            f"The destination airport ({destination}) contributes to this prediction "
            "based on route and destination patterns."
        )

    if feature_name == "ROUTE":
        route = raw_features.get("ROUTE", "this route")
        return (
            f"The route ({route.replace('_', ' → ')}) is associated with delay risk "
            "for this flight in the model."
        )

    if feature_name == "departure_hour":
        hour = int(raw_features.get("departure_hour", 0))
        return (
            f"Departure hour ({hour:02d}:00) is associated with higher or lower "
            "delay risk depending on historical patterns."
        )

    if feature_name == "departure_day_of_week":
        day = int(raw_features.get("departure_day_of_week", 0))
        day_name = DAY_NAMES.get(day, f"day {day}")
        return (
            f"Travel on {day_name} influences this prediction based on day-of-week "
            "delay patterns."
        )

    if feature_name == "departure_month":
        month = int(raw_features.get("departure_month", 0))
        month_name = MONTH_NAMES.get(month, f"month {month}")
        return (
            f"Travel in {month_name} contributes to this prediction based on seasonal "
            "delay patterns."
        )

    if feature_name == "DISTANCE":
        distance = raw_features.get("DISTANCE", 0)
        return (
            f"Route distance ({float(distance):.0f} miles) influences the delay "
            "prediction for this flight."
        )

    if feature_name == "is_weekend":
        is_weekend = int(raw_features.get("is_weekend", 0))
        if is_weekend:
            return "Weekend travel is associated with different delay risk for this flight."
        return "Weekday travel patterns contribute to this prediction."

    if feature_name == "propagation_risk":
        if int(raw_features.get("propagation_risk", 0)) == 1:
            return (
                "The current departure is already delayed, which increases predicted "
                "downstream delay risk for this flight."
            )
        return "Current departure timing reduces propagated delay risk in this prediction."

    if feature_name == "propagation_pressure":
        return (
            "Delay propagation pressure from the current departure timing influences "
            "this prediction."
        )

    if feature_name == "tight_turnaround":
        if int(raw_features.get("tight_turnaround", 0)) == 1:
            return (
                "A tight scheduled turnaround is associated with higher delay risk "
                "for this flight."
            )
        return "Scheduled turnaround time contributes to the predicted delay risk."

    if feature_name == "scheduled_speed_proxy":
        return (
            "The scheduled speed profile for this flight influences the delay "
            "prediction."
        )

    if feature_name == "same_state":
        if int(raw_features.get("same_state", 0)) == 1:
            return "Same-state origin and destination patterns contribute to this prediction."
        return "Cross-state route characteristics contribute to this prediction."

    if feature_name.endswith("_delay_rate"):
        return (
            f"{label} ({encoded_value:.3f} encoded score) is associated with delay "
            "risk for this flight."
        )

    return (
        f"{label} contributes to this prediction based on patterns learned from "
        "historical flight data."
    )


def get_prediction_insights(data, probability, top_n=5):
    try:
        raw_features = build_features(data)
        encoded = prepare_model_input(raw_features, model_loader.preprocessing)[0]
        baselines = _get_feature_baselines()

        contributions = []
        for index, feature_name in enumerate(_feature_columns()):
            encoded_value = float(encoded[index])
            baseline_value = float(baselines[index])
            deviation = abs(encoded_value - baseline_value)

            contributions.append(
                {
                    "feature": feature_name,
                    "label": _feature_label(feature_name),
                    "importance": round(deviation, 6),
                    "contribution": round(deviation, 6),
                    "encoded_value": round(encoded_value, 6),
                    "explanation": _explain_feature(
                        feature_name,
                        raw_features,
                        encoded_value,
                    ),
                }
            )

        contributing_factors = sorted(
            contributions,
            key=lambda item: item["contribution"],
            reverse=True,
        )[:top_n]

        delay_probability = round(float(probability), 4)
        on_time_probability = round(1.0 - delay_probability, 4)

        return {
            "delay_probability": delay_probability,
            "on_time_probability": on_time_probability,
            "contributing_factors": contributing_factors,
            "explanation_available": True,
            "explanation_type": "local_input_deviation",
        }
    except Exception:
        delay_probability = round(float(probability), 4)
        return {
            "delay_probability": delay_probability,
            "on_time_probability": round(1.0 - delay_probability, 4),
            "contributing_factors": [],
            "explanation_available": False,
            "message": "Model explanation is currently unavailable.",
        }
