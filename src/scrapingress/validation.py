"""Validate observations without repairing or disclosing invalid player records."""
import numpy as np
import pandas as pd

REQUIRED_COLUMNS = ["player_id", "timestamp", "site_id", "latitude", "longitude"]


def validate_events(events, allow_simultaneous_sites=False):
    """Return a sorted copy, rejecting missing IDs, duplicates and contradictions.

    When present, event_id distinguishes legitimate simultaneous actions at one
    place. Without event_id, identical observation rows are ambiguous and rejected.
    Naive timestamp inputs are explicitly interpreted as UTC.
    """
    if not isinstance(events, pd.DataFrame) or events.empty:
        raise ValueError("A non-empty event DataFrame is required.")
    if not set(REQUIRED_COLUMNS).issubset(events.columns):
        raise ValueError("Missing required event columns.")
    columns = REQUIRED_COLUMNS + (["event_id"] if "event_id" in events else [])
    df = events[columns].copy()
    if df.isna().any().any():
        raise ValueError("Missing event values are not accepted.")
    for name in ["player_id", "site_id"] + (["event_id"] if "event_id" in df else []):
        if not df[name].map(lambda value: isinstance(value, str)).all():
            raise ValueError(f"{name} must contain strings.")
        if df[name].str.strip().eq("").any():
            raise ValueError(f"Blank {name} values are not accepted.")
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, errors="raise")
    if df["timestamp"].isna().any():
        raise ValueError("Invalid timestamp.")
    for name, bound in [("latitude", 90), ("longitude", 180)]:
        df[name] = pd.to_numeric(df[name], errors="raise")
        if not np.isfinite(df[name]).all() or not df[name].between(-bound, bound).all():
            raise ValueError(f"Invalid {name}.")
    duplicates = df.event_id.duplicated() if "event_id" in df else df.duplicated()
    if duplicates.any():
        raise ValueError("Duplicate observations or event IDs require an explicit upstream decision.")
    locations = df.groupby(["player_id", "timestamp"])[["latitude", "longitude"]].nunique()
    if not allow_simultaneous_sites and locations.gt(1).any(axis=1).any():
        raise ValueError("Conflicting locations for a player at the same timestamp.")
    # Stable ordering preserves the order of legitimate simultaneous co-located actions.
    return df.sort_values(["player_id", "timestamp"], kind="stable").reset_index(drop=True)
