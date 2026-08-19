import math
from datetime import datetime


AIRLINE_NAMES = {
    "AA": "American Airlines",
    "DL": "Delta Air Lines",
    "UA": "United Airlines",
    "WN": "Southwest Airlines",
    "B6": "JetBlue Airways",
    "AS": "Alaska Airlines",
    "NK": "Spirit Airlines",
    "F9": "Frontier Airlines",
    "HA": "Hawaiian Airlines",
    "G4": "Allegiant Air",
    "OO": "SkyWest Airlines",
    "MQ": "Envoy Air",
    "YX": "Republic Airways",
    "9E": "Endeavor Air",
    "EV": "ExpressJet Airlines",
    "VX": "Virgin America"
}


AIRPORT_DATA = {
    "JFK": {"lat": 40.6413, "lon": -73.7781, "state": "NY"},
    "LGA": {"lat": 40.7769, "lon": -73.8740, "state": "NY"},
    "EWR": {"lat": 40.6895, "lon": -74.1745, "state": "NJ"},
    "ATL": {"lat": 33.6407, "lon": -84.4277, "state": "GA"},
    "ORD": {"lat": 41.9742, "lon": -87.9073, "state": "IL"},
    "LAX": {"lat": 33.9416, "lon": -118.4085, "state": "CA"},
    "DFW": {"lat": 32.8998, "lon": -97.0403, "state": "TX"},
    "DEN": {"lat": 39.8561, "lon": -104.6737, "state": "CO"},
    "SFO": {"lat": 37.6213, "lon": -122.3790, "state": "CA"},
    "SEA": {"lat": 47.4502, "lon": -122.3088, "state": "WA"},
    "MIA": {"lat": 25.7959, "lon": -80.2870, "state": "FL"},
    "BOS": {"lat": 42.3656, "lon": -71.0096, "state": "MA"},
    "PHX": {"lat": 33.4373, "lon": -112.0078, "state": "AZ"},
    "IAH": {"lat": 29.9902, "lon": -95.3368, "state": "TX"},
    "LAS": {"lat": 36.0840, "lon": -115.1537, "state": "NV"},
    "MSP": {"lat": 44.8848, "lon": -93.2223, "state": "MN"},
    "DTW": {"lat": 42.2162, "lon": -83.3554, "state": "MI"},
    "PHL": {"lat": 39.8744, "lon": -75.2424, "state": "PA"},
    "CLT": {"lat": 35.2140, "lon": -80.9431, "state": "NC"},
    "DCA": {"lat": 38.8512, "lon": -77.0402, "state": "VA"},
    "IAD": {"lat": 38.9531, "lon": -77.4565, "state": "VA"},
    "BWI": {"lat": 39.1774, "lon": -76.6684, "state": "MD"},
    "SLC": {"lat": 40.7899, "lon": -111.9791, "state": "UT"},
    "PDX": {"lat": 45.5898, "lon": -122.5951, "state": "OR"},
    "SAN": {"lat": 32.7336, "lon": -117.1897, "state": "CA"},
    "TPA": {"lat": 27.9755, "lon": -82.5332, "state": "FL"},
    "MCO": {"lat": 28.4312, "lon": -81.3081, "state": "FL"},
    "AUS": {"lat": 30.1975, "lon": -97.6664, "state": "TX"},
    "DAL": {"lat": 32.8471, "lon": -96.8518, "state": "TX"},
    "STL": {"lat": 38.7487, "lon": -90.3700, "state": "MO"},
    "BNA": {"lat": 36.1263, "lon": -86.6774, "state": "TN"},
    "RDU": {"lat": 35.8776, "lon": -78.7875, "state": "NC"},
    "MDW": {"lat": 41.7868, "lon": -87.7522, "state": "IL"},
    "FLL": {"lat": 26.0742, "lon": -80.1506, "state": "FL"},
    "HOU": {"lat": 29.6454, "lon": -95.2789, "state": "TX"},
    "OAK": {"lat": 37.7213, "lon": -122.2207, "state": "CA"},
    "SMF": {"lat": 38.6954, "lon": -121.5908, "state": "CA"},
    "SJC": {"lat": 37.3626, "lon": -121.9290, "state": "CA"},
    "MSY": {"lat": 29.9934, "lon": -90.2580, "state": "LA"},
    "CLE": {"lat": 41.4117, "lon": -81.8498, "state": "OH"},
    "PIT": {"lat": 40.4915, "lon": -80.2329, "state": "PA"},
    "CMH": {"lat": 39.9980, "lon": -82.8919, "state": "OH"},
    "IND": {"lat": 39.7173, "lon": -86.2944, "state": "IN"},
    "MCI": {"lat": 39.2976, "lon": -94.7139, "state": "MO"},
    "JAX": {"lat": 30.4941, "lon": -81.6879, "state": "FL"},
    "RSW": {"lat": 26.5362, "lon": -81.7552, "state": "FL"},
    "SJU": {"lat": 18.4394, "lon": -66.0018, "state": "PR"}
}


def time_to_minutes(value):
    value = int(value)
    hours = value // 100
    minutes = value % 100
    return hours * 60 + minutes


def haversine_distance(lat1, lon1, lat2, lon2):
    radius = 6371.0

    lat1 = math.radians(lat1)
    lon1 = math.radians(lon1)
    lat2 = math.radians(lat2)
    lon2 = math.radians(lon2)

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1)
        * math.cos(lat2)
        * math.sin(dlon / 2) ** 2
    )

    return 2 * radius * math.asin(math.sqrt(a))


def get_airport_data(code):
    return AIRPORT_DATA.get(
        code,
        {
            "lat": 0.0,
            "lon": 0.0,
            "state": "UNKNOWN"
        }
    )


def build_features(data):
    airline = data["airline"].upper()
    origin = data["origin"].upper()
    destination = data["destination"].upper()

    month = int(data["month"])
    day = int(data["day_of_month"])
    day_of_week = int(data["day_of_week"])

    scheduled_departure = time_to_minutes(
        data["scheduled_dep_time"]
    )

    scheduled_arrival = time_to_minutes(
        data["scheduled_arrival_time"]
    )

    origin_data = get_airport_data(origin)
    destination_data = get_airport_data(destination)

    departure_hour = scheduled_departure // 60
    departure_minute = scheduled_departure % 60

    departure_datetime = datetime(
        2024,
        month,
        min(day, 28)
    )

    departure_day_of_year = departure_datetime.timetuple().tm_yday
    departure_week = departure_datetime.isocalendar().week

    # Scheduled flight duration.
    # This uses only scheduled times and does NOT use actual departure.
    scheduled_time = scheduled_arrival - scheduled_departure

    if scheduled_time <= 0:
        scheduled_time += 24 * 60

    distance = float(data["distance"])

    distance_per_scheduled_min = (
        distance / scheduled_time
        if scheduled_time > 0
        else 0.0
    )

    scheduled_speed_proxy = distance_per_scheduled_min * 60

    buffer_ratio = (
        scheduled_time / max(distance, 1.0)
    )

    is_weekend = int(day_of_week in [6, 7])

    same_state = int(
        origin_data["state"] == destination_data["state"]
        and origin_data["state"] != "UNKNOWN"
    )

    route = f"{origin}_{destination}"

    route_distance = haversine_distance(
        origin_data["lat"],
        origin_data["lon"],
        destination_data["lat"],
        destination_data["lon"]
    )

    tight_turnaround = int(
        scheduled_time < 90
    )

    # No actual departure information is available.
    # Therefore these current-flight delay/propagation values
    # must not be derived from actual departure.
    #
    # Keep the feature names because the existing HistGradientBoosting
    # model expects the existing 68-feature schema.
    previous_flight_departure_delay = 0.0
    previous_flight_arrival_delay = 0.0
    previous_delay_magnitude = 0.0
    previous_flight_delayed = 0

    scheduled_turnaround_min = 0.0
    remaining_turnaround_min = 0.0
    turnaround_stress_min = max(
        0,
        90 - scheduled_time
    )

    propagation_pressure = 0.0
    propagation_risk = 0

    historical_rate = 0.0

    features = {
        "origin_delay_rate": historical_rate,
        "departure_month": month,
        "valid_aircraft_connection": 0,
        "scheduled_turnaround_min": scheduled_turnaround_min,
        "origin_past_flights": 0,
        "aircraft_delay_rate": historical_rate,
        "is_weekend": is_weekend,
        "buffer_ratio": buffer_ratio,
        "airline_delay_rate": historical_rate,

        "ORIGIN_AIRPORT": origin,

        "departure_hour_cos": math.cos(
            2 * math.pi * departure_hour / 24
        ),

        "origin_vs_airline_delay_rate": 0.0,

        "departure_hour_sin": math.sin(
            2 * math.pi * departure_hour / 24
        ),

        "departure_day_of_week": day_of_week,

        "airline_avg_departure_delay": 0.0,

        "scheduled_speed_proxy": scheduled_speed_proxy,

        "destination_latitude": destination_data["lat"],

        "TAIL_NUMBER": "UNKNOWN",

        "SCHEDULED_TIME": scheduled_time,

        "airline_history_strength": 0.0,

        "day_of_week_cos": math.cos(
            2 * math.pi * day_of_week / 7
        ),

        "aircraft_cumulative_delay_today": 0.0,

        "time_since_previous_flight_min": 0.0,

        "departure_hour": departure_hour,

        "origin_history_strength": 0.0,

        "departure_minute": departure_minute,

        "origin_longitude": origin_data["lon"],

        "propagation_pressure": propagation_pressure,

        "route_past_flights": 0,

        "day_of_week_sin": math.sin(
            2 * math.pi * day_of_week / 7
        ),

        "departure_day_of_year": departure_day_of_year,

        "origin_state": origin_data["state"],

        "same_state": same_state,

        "is_first_flight_of_day": 1,

        "destination_vs_airline_delay_rate": 0.0,

        "tight_turnaround": tight_turnaround,

        "route_avg_departure_delay": 0.0,

        "AIRLINE_NAME": AIRLINE_NAMES.get(
            airline,
            airline
        ),

        "previous_flight_delayed": previous_flight_delayed,

        "airline_past_flights": 0,

        "turnaround_stress_min": turnaround_stress_min,

        "DESTINATION_AIRPORT": destination,

        "departure_week": departure_week,

        "ROUTE": route,

        "distance_per_scheduled_min": distance_per_scheduled_min,

        "destination_history_strength": 0.0,

        "previous_flight_departure_delay":
            previous_flight_departure_delay,

        "route_history_strength": 0.0,

        "route_vs_airline_delay_rate": 0.0,

        "destination_past_flights": 0,

        "previous_delay_magnitude":
            previous_delay_magnitude,

        "destination_delay_rate": historical_rate,

        "destination_state": destination_data["state"],

        "destination_longitude": destination_data["lon"],

        "remaining_turnaround_min":
            remaining_turnaround_min,

        "aircraft_past_flights": 0,

        "aircraft_avg_departure_delay": 0.0,

        "route_delay_rate": historical_rate,

        "origin_avg_departure_delay": 0.0,

        "previous_flight_arrival_delay":
            previous_flight_arrival_delay,

        "departure_day": day,

        "FLIGHT_NUMBER": int(data["flight_number"]),

        "AIRLINE": airline,

        "propagation_risk": propagation_risk,

        "origin_latitude": origin_data["lat"],

        "route_geographic_distance_km": route_distance,

        "destination_avg_departure_delay": 0.0,

        "DISTANCE": distance
    }

    return features


def _encode_categorical(value, column, preprocessing):
    frequency_maps = preprocessing["frequency_maps"]
    missing_key = preprocessing["missing_category_key"]
    unknown_frequency = preprocessing["unknown_category_frequency"]

    if value is None or value == "":
        lookup_key = missing_key
    else:
        lookup_key = str(value)

    column_map = frequency_maps.get(column, {})
    return column_map.get(lookup_key, unknown_frequency)


def prepare_model_input(features, preprocessing):
    if preprocessing is None:
        raise ValueError("Preprocessing artifact is not loaded")

    feature_columns = preprocessing["feature_columns"]
    categorical_columns = set(preprocessing["categorical_columns"])
    feature_dtype = preprocessing.get("feature_dtype", "float32")

    encoded_row = []

    for column in feature_columns:
        raw_value = features.get(column)

        if column in categorical_columns:
            encoded_row.append(
                _encode_categorical(raw_value, column, preprocessing)
            )
        elif raw_value is None:
            encoded_row.append(0.0)
        else:
            encoded_row.append(float(raw_value))

    import numpy as np

    return np.array([encoded_row], dtype=feature_dtype)
