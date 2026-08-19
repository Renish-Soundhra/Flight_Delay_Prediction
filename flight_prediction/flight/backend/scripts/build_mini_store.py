import sys
from pathlib import Path
BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime

from models.model_loader import ModelLoader
from utils.feature_processor import build_features, prepare_model_input
from scripts.export_test_data import _enrich_delay_rates, _csv_row_to_payload

def build_mini_store(raw_path, db_path, max_rows=50000):
    loader = ModelLoader()
    if not loader.is_ready:
        raise RuntimeError(loader.load_error or "Model not loaded")

    db_path = Path(db_path)
    if db_path.exists():
        db_path.unlink()
    
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA journal_mode=OFF")
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
    
    # Load airlines and airports for metadata
    airlines_df = pd.read_csv("C:\\Users\\ASUS\\Downloads\\archive (2)\\airlines.csv")
    airline_map = dict(zip(airlines_df['IATA_CODE'], airlines_df['AIRLINE']))
    
    airports_df = pd.read_csv("C:\\Users\\ASUS\\Downloads\\archive (2)\\airports.csv")
    airport_lat_map = dict(zip(airports_df['IATA_CODE'], airports_df['LATITUDE']))
    airport_lon_map = dict(zip(airports_df['IATA_CODE'], airports_df['LONGITUDE']))

    usecols = [
        "YEAR", "MONTH", "DAY", "DAY_OF_WEEK", "AIRLINE", "FLIGHT_NUMBER",
        "TAIL_NUMBER", "ORIGIN_AIRPORT", "DESTINATION_AIRPORT",
        "SCHEDULED_DEPARTURE", "DEPARTURE_TIME", "DEPARTURE_DELAY", "SCHEDULED_ARRIVAL",
        "ARRIVAL_TIME", "ARRIVAL_DELAY", "DISTANCE", "CANCELLED", "DIVERTED"
    ]
    
    df = pd.read_csv(raw_path, usecols=usecols, nrows=max_rows, low_memory=True)
    df = df[(df["CANCELLED"] == 0) & (df["DIVERTED"] == 0)].copy()
    
    rows_to_insert = []
    
    def hhmm_to_min(val):
        if pd.isna(val): return None
        v = int(val)
        return (v // 100) * 60 + (v % 100)
        
    for idx, row in df.iterrows():
        try:
            payload = _csv_row_to_payload(row)
            features = build_features(payload)
            features = _enrich_delay_rates(features, loader.preprocessing)
            encoded = prepare_model_input(features, loader.preprocessing)[0]
            
            # Predict
            X = np.asarray([encoded], dtype=np.float32)
            prob = float(loader.model.predict_proba(X)[0, 1])
            pred = 1 if prob >= loader.threshold else 0
            
            sch_dep = hhmm_to_min(row['SCHEDULED_DEPARTURE'])
            sch_arr = hhmm_to_min(row['SCHEDULED_ARRIVAL'])
            sch_time = sch_arr - sch_dep if sch_arr and sch_dep else None
            if sch_time and sch_time < 0: sch_time += 1440
            
            try:
                dt = datetime(int(row['YEAR']), int(row['MONTH']), int(row['DAY']), 
                              int(row['SCHEDULED_DEPARTURE']) // 100, int(row['SCHEDULED_DEPARTURE']) % 100)
                ts = dt.isoformat(timespec="minutes")
            except:
                ts = None
                
            arr_delay = float(row['ARRIVAL_DELAY']) if pd.notna(row['ARRIVAL_DELAY']) else None
            dep_delay = float(row['DEPARTURE_DELAY']) if pd.notna(row['DEPARTURE_DELAY']) else None
            act_delayed = 1 if arr_delay and arr_delay >= 15 else 0
            
            origin = str(row['ORIGIN_AIRPORT'])
            dest = str(row['DESTINATION_AIRPORT'])
            
            r = (
                int(row['FLIGHT_NUMBER']),
                str(row['AIRLINE']),
                airline_map.get(str(row['AIRLINE']), str(row['AIRLINE'])),
                str(row['TAIL_NUMBER']),
                origin,
                dest,
                airport_lat_map.get(origin),
                airport_lon_map.get(origin),
                airport_lat_map.get(dest),
                airport_lon_map.get(dest),
                sch_dep,
                sch_arr,
                sch_time,
                int(row['YEAR']),
                int(row['MONTH']),
                int(row['DAY']),
                int(row['DAY_OF_WEEK']),
                None, # day of year
                None, # week
                ts,
                act_delayed,
                dep_delay,
                arr_delay,
                hhmm_to_min(row['ARRIVAL_TIME']),
                prob,
                pred,
                None, None, None, None, None, None, None, None # Prev flight details
            )
            rows_to_insert.append(r)
        except Exception as e:
            continue
            
    conn.executemany(
        """
        INSERT INTO flights (
            flight_number, airline, airline_name, tail_number, origin, destination,
            origin_lat, origin_lon, dest_lat, dest_lon, scheduled_dep_min, scheduled_arr_min,
            scheduled_time, year, month, day, day_of_week, day_of_year, week, scheduled_ts,
            actual_delayed, departure_delay, arrival_delay, actual_arrival_min,
            probability, prediction, prev_dep_delay, prev_arr_delay, time_since_prev,
            scheduled_turnaround, remaining_turnaround, turnaround_stress, buffer_ratio,
            propagation_pressure
        ) VALUES (
            ?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?
        )
        """, rows_to_insert
    )
    conn.commit()
    conn.execute("CREATE INDEX idx_flights_scheduled_ts ON flights(scheduled_ts)")
    conn.execute("CREATE INDEX idx_flights_probability ON flights(probability DESC)")
    conn.execute("CREATE INDEX idx_flights_origin ON flights(origin)")
    conn.execute("CREATE INDEX idx_flights_dest ON flights(destination)")
    conn.execute("CREATE INDEX idx_flights_airline ON flights(airline)")
    conn.close()
    print(f"Built store with {len(rows_to_insert)} flights.")

if __name__ == "__main__":
    build_mini_store(
        "C:\\Users\\ASUS\\Downloads\\archive (2)\\flights.csv",
        BACKEND_DIR / "artifacts" / "dashboard.sqlite",
        max_rows=100000
    )
