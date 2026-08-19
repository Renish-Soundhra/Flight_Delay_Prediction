from datetime import datetime

from models.model_loader import model_loader
from services.dashboard_store import get_connection, visualization_risk

VIS_CLAUSE = """
CASE
    WHEN probability >= 0.90 THEN 'HIGH'
    WHEN probability >= 0.70 THEN 'MEDIUM'
    ELSE 'LOW'
END
"""


def _minutes_to_hhmm(value):
    if value is None:
        return None
    minutes = int(value) % (24 * 60)
    hours = minutes // 60
    mins = minutes % 60
    return f"{hours:02d}:{mins:02d}"


def _row_to_flight(row, include_rotation=False):
    probability = None if row["probability"] is None else float(row["probability"])
    prediction = None if row["prediction"] is None else int(row["prediction"])
    payload = {
        "id": row["id"],
        "flight_number": row["flight_number"],
        "airline": row["airline"],
        "airline_name": row["airline_name"],
        "tail_number": row["tail_number"],
        "origin": row["origin"],
        "destination": row["destination"],
        "origin_lat": row["origin_lat"],
        "origin_lon": row["origin_lon"],
        "dest_lat": row["dest_lat"],
        "dest_lon": row["dest_lon"],
        "scheduled_departure": _minutes_to_hhmm(row["scheduled_dep_min"]),
        "scheduled_arrival": _minutes_to_hhmm(row["scheduled_arr_min"]),
        "scheduled_flight_duration": row["scheduled_time"],
        "year": row["year"],
        "month": row["month"],
        "day": row["day"],
        "day_of_week": row["day_of_week"],
        "scheduled_ts": row["scheduled_ts"],
        "actual_delayed": row["actual_delayed"],
        "departure_delay": row["departure_delay"],
        "arrival_delay": row["arrival_delay"],
        "actual_arrival": _minutes_to_hhmm(row["actual_arrival_min"]),
        "probability": probability,
        "prediction": prediction,
        "predicted_class_label": (
            "Delayed" if prediction == 1 else "On Time" if prediction == 0 else None
        ),
        "risk": visualization_risk(probability),
        "ml_threshold": float(model_loader.threshold),
    }
    if include_rotation:
        payload.update(
            {
                "previous_flight_departure_delay": row["prev_dep_delay"],
                "previous_flight_arrival_delay": row["prev_arr_delay"],
                "time_since_previous_flight_min": row["time_since_prev"],
                "scheduled_turnaround_min": row["scheduled_turnaround"],
                "remaining_turnaround_min": row["remaining_turnaround"],
                "turnaround_stress_min": row["turnaround_stress"],
                "buffer_ratio": row["buffer_ratio"],
                "propagation_pressure": row["propagation_pressure"],
            }
        )
    return payload


def _filters(params):
    clauses = ["1=1"]
    values = []

    if params.get("date_from"):
        clauses.append("scheduled_ts >= ?")
        values.append(params["date_from"])
    if params.get("date_to"):
        clauses.append("scheduled_ts <= ?")
        values.append(params["date_to"])
    if params.get("as_of"):
        clauses.append("scheduled_ts <= ?")
        values.append(params["as_of"])
    if params.get("airline"):
        clauses.append("airline = ?")
        values.append(params["airline"].upper())
    if params.get("origin"):
        clauses.append("origin = ?")
        values.append(params["origin"].upper())
    if params.get("destination"):
        clauses.append("destination = ?")
        values.append(params["destination"].upper())
    if params.get("flight_number"):
        clauses.append("CAST(flight_number AS TEXT) LIKE ?")
        values.append(f"%{params['flight_number']}%")
    if params.get("tail_number"):
        clauses.append("tail_number LIKE ?")
        values.append(f"%{params['tail_number'].upper()}%")
    if params.get("prediction") in ("0", "1", 0, 1):
        clauses.append("prediction = ?")
        values.append(int(params["prediction"]))
    if params.get("risk"):
        risk = params["risk"].upper()
        if risk == "HIGH":
            clauses.append("probability >= 0.90")
        elif risk == "MEDIUM":
            clauses.append("probability >= 0.70 AND probability < 0.90")
        elif risk == "LOW":
            clauses.append("probability < 0.70")
    if params.get("prob_min") not in (None, ""):
        clauses.append("probability >= ?")
        values.append(float(params["prob_min"]))
    if params.get("prob_max") not in (None, ""):
        clauses.append("probability <= ?")
        values.append(float(params["prob_max"]))
    return " AND ".join(clauses), values


def get_filter_options():
    conn = get_connection()
    airlines = [
        {"code": row["airline"], "name": row["airline_name"]}
        for row in conn.execute(
            """
            SELECT airline, MAX(airline_name) AS airline_name
            FROM flights
            WHERE airline IS NOT NULL
            GROUP BY airline
            ORDER BY airline
            """
        )
    ]
    origins = [row[0] for row in conn.execute(
        "SELECT DISTINCT origin FROM flights WHERE origin IS NOT NULL ORDER BY origin"
    )]
    destinations = [row[0] for row in conn.execute(
        "SELECT DISTINCT destination FROM flights WHERE destination IS NOT NULL ORDER BY destination"
    )]
    bounds = conn.execute(
        "SELECT MIN(scheduled_ts) AS min_ts, MAX(scheduled_ts) AS max_ts, COUNT(*) AS n FROM flights"
    ).fetchone()
    return {
        "airlines": airlines,
        "origins": origins,
        "destinations": destinations,
        "min_ts": bounds["min_ts"],
        "max_ts": bounds["max_ts"],
        "total_rows": bounds["n"],
        "dataset_label": "Historical",
        "year_note": "Source data is the existing engineered 2015 US flight dataset, not a live feed.",
        "ml_threshold": float(model_loader.threshold),
        "visualization_risk": {
            "LOW": "probability < 0.70",
            "MEDIUM": "0.70 <= probability < 0.90",
            "HIGH": "probability >= 0.90",
            "note": "Visualization categories only. They do not change the HistGradientBoosting decision threshold.",
        },
    }


def get_summary(params):
    where, values = _filters(params)
    conn = get_connection()
    row = conn.execute(
        f"""
        SELECT
            COUNT(*) AS total_flights,
            SUM(CASE WHEN actual_delayed = 1 THEN 1 ELSE 0 END) AS delayed_flights,
            AVG(CASE WHEN actual_delayed IS NOT NULL THEN actual_delayed END) AS delay_rate,
            AVG(departure_delay) AS avg_departure_delay,
            SUM(CASE WHEN probability >= 0.90 THEN 1 ELSE 0 END) AS high_risk_flights,
            AVG(probability) AS avg_prediction_probability,
            AVG(prediction) AS predicted_delay_rate,
            MIN(scheduled_ts) AS min_ts,
            MAX(scheduled_ts) AS max_ts
        FROM flights
        WHERE {where}
        """,
        values,
    ).fetchone()
    return {
        "actual": {
            "total_flights": int(row["total_flights"] or 0),
            "delayed_flights": int(row["delayed_flights"] or 0),
            "delay_rate": float(row["delay_rate"] or 0),
            "avg_departure_delay": row["avg_departure_delay"],
            "definition": "Delayed = target 1 (arrival delay >= 15 minutes) from the existing engineered dataset.",
        },
        "model": {
            "high_risk_flights": int(row["high_risk_flights"] or 0),
            "avg_prediction_probability": row["avg_prediction_probability"],
            "predicted_delay_rate": row["predicted_delay_rate"],
            "ml_threshold": float(model_loader.threshold),
            "high_risk_definition": "Visualization HIGH: existing HistGradientBoosting P(delay) >= 0.90",
        },
        "time_range": {"min_ts": row["min_ts"], "max_ts": row["max_ts"]},
        "as_of": params.get("as_of"),
    }


def get_trends(params, aggregation="daily"):
    where, values = _filters(params)
    if aggregation == "weekly":
        bucket = "substr(scheduled_ts, 1, 4) || '-W' || printf('%02d', week)"
    elif aggregation == "monthly":
        bucket = "substr(scheduled_ts, 1, 7)"
    else:
        bucket = "substr(scheduled_ts, 1, 10)"
        aggregation = "daily"

    conn = get_connection()
    rows = conn.execute(
        f"""
        SELECT
            {bucket} AS bucket,
            COUNT(*) AS total_flights,
            AVG(actual_delayed) AS actual_delay_rate,
            AVG(prediction) AS predicted_delay_rate
        FROM flights
        WHERE {where} AND scheduled_ts IS NOT NULL
        GROUP BY bucket
        ORDER BY bucket
        """,
        values,
    ).fetchall()
    return {
        "aggregation": aggregation,
        "points": [dict(row) for row in rows],
        "note": "No future dates are fabricated. Points exist only where the historical dataset has flights.",
    }


def get_airports(params):
    where, values = _filters(params)
    conn = get_connection()
    rows = conn.execute(
        f"""
        SELECT
            origin AS airport,
            COUNT(*) AS total_flights,
            SUM(CASE WHEN actual_delayed = 1 THEN 1 ELSE 0 END) AS delayed_flights,
            AVG(actual_delayed) AS delay_rate,
            AVG(departure_delay) AS avg_departure_delay,
            AVG(probability) AS avg_prediction_probability,
            AVG(origin_lat) AS lat,
            AVG(origin_lon) AS lon
        FROM flights
        WHERE {where} AND origin IS NOT NULL
        GROUP BY origin
        ORDER BY delay_rate DESC
        """,
        values,
    ).fetchall()
    return [dict(row) for row in rows]


def get_airlines(params):
    where, values = _filters(params)
    conn = get_connection()
    rows = conn.execute(
        f"""
        SELECT
            airline,
            MAX(airline_name) AS airline_name,
            COUNT(*) AS total_flights,
            SUM(CASE WHEN actual_delayed = 1 THEN 1 ELSE 0 END) AS delayed_flights,
            AVG(actual_delayed) AS delay_rate,
            AVG(departure_delay) AS avg_departure_delay,
            AVG(probability) AS avg_prediction_probability
        FROM flights
        WHERE {where} AND airline IS NOT NULL
        GROUP BY airline
        ORDER BY delay_rate DESC
        """,
        values,
    ).fetchall()
    return [dict(row) for row in rows]


def get_routes(params, limit=10):
    where, values = _filters(params)
    search = params.get("route_search")
    extra = ""
    if search:
        extra = " AND (origin || ' → ' || destination) LIKE ?"
        values = list(values) + [f"%{search.upper()}%"]
    conn = get_connection()
    rows = conn.execute(
        f"""
        SELECT
            origin || ' → ' || destination AS route,
            origin,
            destination,
            COUNT(*) AS total_flights,
            SUM(CASE WHEN actual_delayed = 1 THEN 1 ELSE 0 END) AS delayed_flights,
            AVG(actual_delayed) AS delay_rate,
            AVG(departure_delay) AS avg_departure_delay,
            AVG(probability) AS avg_prediction_probability
        FROM flights
        WHERE {where} {extra}
        GROUP BY origin, destination
        ORDER BY avg_prediction_probability DESC
        LIMIT ?
        """,
        list(values) + [int(limit)],
    ).fetchall()
    return [dict(row) for row in rows]


def get_high_risk_flights(params, page=1, page_size=20, sort="probability", order="desc"):
    where, values = _filters(params)
    allowed_sort = {
        "probability": "probability",
        "scheduled_ts": "scheduled_ts",
        "airline": "airline",
        "origin": "origin",
        "destination": "destination",
        "flight_number": "flight_number",
        "scheduled_time": "scheduled_time",
    }
    sort_col = allowed_sort.get(sort, "probability")
    direction = "ASC" if str(order).lower() == "asc" else "DESC"
    page = max(int(page), 1)
    page_size = min(max(int(page_size), 1), 50)
    offset = (page - 1) * page_size

    conn = get_connection()
    total = conn.execute(
        f"SELECT COUNT(*) FROM flights WHERE {where}",
        values,
    ).fetchone()[0]
    rows = conn.execute(
        f"""
        SELECT *
        FROM flights
        WHERE {where}
        ORDER BY {sort_col} {direction}, id ASC
        LIMIT ? OFFSET ?
        """,
        list(values) + [page_size, offset],
    ).fetchall()
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [_row_to_flight(row, include_rotation=True) for row in rows],
    }


def get_map_payload(params, max_routes=800, max_airports=400):
    where, values = _filters(params)
    conn = get_connection()
    routes = conn.execute(
        f"""
        SELECT
            origin,
            destination,
            AVG(origin_lat) AS origin_lat,
            AVG(origin_lon) AS origin_lon,
            AVG(dest_lat) AS dest_lat,
            AVG(dest_lon) AS dest_lon,
            COUNT(*) AS flight_count,
            AVG(probability) AS avg_probability,
            MAX(probability) AS max_probability,
            MIN(id) AS sample_flight_id
        FROM flights
        WHERE {where}
          AND origin_lat IS NOT NULL AND origin_lon IS NOT NULL
          AND dest_lat IS NOT NULL AND dest_lon IS NOT NULL
        GROUP BY origin, destination
        ORDER BY max_probability DESC, flight_count DESC
        LIMIT ?
        """,
        list(values) + [int(max_routes)],
    ).fetchall()

    airports = conn.execute(
        f"""
        SELECT
            origin AS airport,
            AVG(origin_lat) AS lat,
            AVG(origin_lon) AS lon,
            COUNT(*) AS flight_count,
            AVG(probability) AS avg_probability
        FROM flights
        WHERE {where} AND origin_lat IS NOT NULL AND origin_lon IS NOT NULL
        GROUP BY origin
        ORDER BY flight_count DESC
        LIMIT ?
        """,
        list(values) + [int(max_airports)],
    ).fetchall()

    sample_flights = conn.execute(
        f"""
        SELECT *
        FROM flights
        WHERE {where}
          AND origin_lat IS NOT NULL AND dest_lat IS NOT NULL
        ORDER BY probability DESC
        LIMIT 40
        """,
        values,
    ).fetchall()

    return {
        "routes": [
            {
                **dict(row),
                "risk": visualization_risk(row["max_probability"]),
            }
            for row in routes
        ],
        "airports": [dict(row) for row in airports],
        "sample_flights": [_row_to_flight(row) for row in sample_flights],
        "capped_routes": int(max_routes),
        "note": "Routes are aggregated origin→destination pairs. Individual flight rows are not sent in bulk.",
    }


def get_flight(flight_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM flights WHERE id = ?", (int(flight_id),)).fetchone()
    if row is None:
        return None
    return _row_to_flight(row, include_rotation=True)


def get_aircraft(tail_number, params=None):
    params = dict(params or {})
    params["tail_number"] = tail_number
    where, values = _filters(params)
    conn = get_connection()
    rows = conn.execute(
        f"""
        SELECT *
        FROM flights
        WHERE {where}
        ORDER BY scheduled_ts ASC, scheduled_dep_min ASC, id ASC
        LIMIT 80
        """,
        values,
    ).fetchall()
    return {
        "tail_number": tail_number.upper(),
        "flights": [_row_to_flight(row, include_rotation=True) for row in rows],
        "note": "Turnaround and previous-flight fields come from the existing feature-engineering output. They are not recalculated.",
    }


def get_delay_distribution(params):
    where, values = _filters(params)
    conn = get_connection()
    row = conn.execute(
        f"""
        SELECT
            SUM(CASE WHEN departure_delay < 0 THEN 1 ELSE 0 END) AS lt0,
            SUM(CASE WHEN departure_delay >= 0 AND departure_delay < 15 THEN 1 ELSE 0 END) AS b0_15,
            SUM(CASE WHEN departure_delay >= 15 AND departure_delay < 30 THEN 1 ELSE 0 END) AS b15_30,
            SUM(CASE WHEN departure_delay >= 30 AND departure_delay < 60 THEN 1 ELSE 0 END) AS b30_60,
            SUM(CASE WHEN departure_delay >= 60 AND departure_delay < 120 THEN 1 ELSE 0 END) AS b60_120,
            SUM(CASE WHEN departure_delay >= 120 THEN 1 ELSE 0 END) AS gt120,
            SUM(CASE WHEN departure_delay IS NOT NULL THEN 1 ELSE 0 END) AS with_delay,
            SUM(CASE WHEN actual_delayed = 0 THEN 1 ELSE 0 END) AS not_delayed,
            SUM(CASE WHEN actual_delayed = 1 THEN 1 ELSE 0 END) AS delayed
        FROM flights
        WHERE {where}
        """,
        values,
    ).fetchone()
    return {
        "buckets": [
            {"label": "< 0 min", "count": int(row["lt0"] or 0)},
            {"label": "0–15 min", "count": int(row["b0_15"] or 0)},
            {"label": "15–30 min", "count": int(row["b15_30"] or 0)},
            {"label": "30–60 min", "count": int(row["b30_60"] or 0)},
            {"label": "60–120 min", "count": int(row["b60_120"] or 0)},
            {"label": "> 120 min", "count": int(row["gt120"] or 0)},
        ],
        "class_split": {
            "not_delayed": int(row["not_delayed"] or 0),
            "delayed": int(row["delayed"] or 0),
            "definition": "Not Delayed: target 0 (arrival delay < 15). Delayed: target 1 (arrival delay >= 15).",
        },
        "rows_with_departure_delay": int(row["with_delay"] or 0),
        "source": "DEPARTURE_DELAY joined from the raw flights.csv using airline, flight number, tail, origin, destination, month, and day.",
    }


def get_probability_distribution(params):
    where, values = _filters(params)
    conn = get_connection()
    row = conn.execute(
        f"""
        SELECT
            COUNT(*) AS total,
            SUM(CASE WHEN probability >= 0.0 AND probability < 0.1 THEN 1 ELSE 0 END) AS b0,
            SUM(CASE WHEN probability >= 0.1 AND probability < 0.2 THEN 1 ELSE 0 END) AS b1,
            SUM(CASE WHEN probability >= 0.2 AND probability < 0.3 THEN 1 ELSE 0 END) AS b2,
            SUM(CASE WHEN probability >= 0.3 AND probability < 0.4 THEN 1 ELSE 0 END) AS b3,
            SUM(CASE WHEN probability >= 0.4 AND probability < 0.5 THEN 1 ELSE 0 END) AS b4,
            SUM(CASE WHEN probability >= 0.5 AND probability < 0.6 THEN 1 ELSE 0 END) AS b5,
            SUM(CASE WHEN probability >= 0.6 AND probability < 0.7 THEN 1 ELSE 0 END) AS b6,
            SUM(CASE WHEN probability >= 0.7 AND probability < 0.8 THEN 1 ELSE 0 END) AS b7,
            SUM(CASE WHEN probability >= 0.8 AND probability < 0.9 THEN 1 ELSE 0 END) AS b8,
            SUM(CASE WHEN probability >= 0.9 AND probability <= 1.0 THEN 1 ELSE 0 END) AS b9
        FROM flights
        WHERE {where}
        """,
        values,
    ).fetchone()
    total = int(row["total"] or 0)
    labels = [
        "0.0–0.1", "0.1–0.2", "0.2–0.3", "0.3–0.4", "0.4–0.5",
        "0.5–0.6", "0.6–0.7", "0.7–0.8", "0.8–0.9", "0.9–1.0",
    ]
    counts = [int(row[f"b{i}"] or 0) for i in range(10)]
    return {
        "total": total,
        "buckets": [
            {
                "label": labels[i],
                "count": counts[i],
                "percent": (counts[i] / total) if total else 0,
            }
            for i in range(10)
        ],
        "source": "Existing HistGradientBoosting predict_proba[:, 1]",
    }


def get_timeline_bounds():
    conn = get_connection()
    row = conn.execute(
        "SELECT MIN(scheduled_ts) AS min_ts, MAX(scheduled_ts) AS max_ts FROM flights"
    ).fetchone()
    return {"min_ts": row["min_ts"], "max_ts": row["max_ts"], "generated_at": datetime.utcnow().isoformat()}
