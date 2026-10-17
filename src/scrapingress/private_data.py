"""Read the pseudonymised local database, never serve it through a public API."""
from pathlib import Path
import sqlite3
from contextlib import closing
import pandas as pd
from .validation import validate_events


def load_private_events(database):
    path = Path(database).resolve(strict=True)
    with closing(sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)) as connection:
        frame = pd.read_sql_query(
            "SELECT event_id, player_id, timestamp, site_id, latitude, longitude FROM events", connection)
    quality = {"database_rows": len(frame)}
    valid = frame.notna().all(axis=1)
    quality["excluded_incomplete_rows"] = int((~valid).sum())
    frame = frame.loc[valid].copy()
    frame["timestamp"] = pd.to_datetime(frame.timestamp, unit="ms", utc=True, errors="raise")
    # Retain event IDs so distinct simultaneous actions at the same place are counted.
    quality["simultaneous_site_groups"] = int(
        frame.groupby(["player_id", "timestamp"])[["latitude", "longitude"]].nunique().gt(1).any(axis=1).sum())
    frame = validate_events(frame, allow_simultaneous_sites=True)
    quality["validated_rows"] = len(frame)
    return frame, quality
