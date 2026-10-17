"""Compute interpretable player features inside explicit observation windows."""
import numpy as np
import pandas as pd
from .sessions import identify_sessions
from .validation import validate_events

FEATURES = ["active_day_fraction", "events_per_active_day", "sites_per_active_day",
            "sessions_per_active_day", "median_session_minutes",
            "median_observed_path_km", "site_entropy", "hour_concentration"]
ACTIVITY_FEATURES = [name for name in FEATURES if name != "median_observed_path_km"]
LOG_FEATURES = ["events_per_active_day", "sites_per_active_day",
                "sessions_per_active_day", "median_session_minutes",
                "median_observed_path_km"]



def compute_player_features(events, start, end, gap_minutes=30, min_events=5, include_path=True):
    """Features for [start, end), using only observations inside this window."""
    start, end = pd.Timestamp(start), pd.Timestamp(end)
    if pd.isna(start) or pd.isna(end) or start.tzinfo is None or end.tzinfo is None or end <= start:
        raise ValueError("Provide increasing, timezone-aware window bounds.")
    start, end = start.tz_convert("UTC"), end.tz_convert("UTC")
    if isinstance(min_events, bool) or not isinstance(min_events, (int, np.integer)) or min_events < 1:
        raise ValueError("min_events must be a positive integer.")
    # Count UTC calendar dates intersecting the half-open window, including partial dates.
    observed_days = ((end - pd.Timedelta(nanoseconds=1)).floor("D") - start.floor("D")).days + 1
    df = validate_events(events, allow_simultaneous_sites=not include_path)
    df = df[(df.timestamp >= start) & (df.timestamp < end)]
    if df.empty:
        raise ValueError("No observations inside the requested window.")
    df = identify_sessions(df, gap_minutes, include_path=include_path)
    df["day"] = df.timestamp.dt.floor("D")
    rows = []
    for player, group in df.groupby("player_id", sort=True):
        if len(group) < min_events:
            continue
        active_days = group.day.nunique()
        daily_sites = group.groupby("day").site_id.nunique().mean()
        aggregations = {"first": ("timestamp", "min"), "last": ("timestamp", "max")}
        if include_path:
            aggregations["path"] = ("observed_step_km", "sum")
        sessions = group.groupby("session_id").agg(**aggregations)
        duration = (sessions["last"] - sessions["first"]).dt.total_seconds() / 60
        probabilities = group.site_id.value_counts(normalize=True).to_numpy()
        entropy = -(probabilities * np.log(probabilities)).sum()
        # Normalise entropy to [0, 1]; a single visited site has entropy zero.
        entropy = entropy / np.log(len(probabilities)) if len(probabilities) > 1 else 0
        angles = group.timestamp.dt.hour.to_numpy() * 2 * np.pi / 24
        concentration = np.abs(np.exp(1j * angles).mean())
        row = {"player_id": player, "active_day_fraction": active_days / observed_days,
               "events_per_active_day": len(group) / active_days,
               "sites_per_active_day": daily_sites,
               "sessions_per_active_day": len(sessions) / active_days,
               "median_session_minutes": float(duration.median()),
               "site_entropy": entropy, "hour_concentration": concentration}
        if include_path:
            row["median_observed_path_km"] = float(sessions.path.median())
        rows.append(row)
    if not rows:
        raise ValueError("No players meet the minimum observation count.")
    names = FEATURES if include_path else ACTIVITY_FEATURES
    return pd.DataFrame(rows, columns=["player_id"] + names).set_index("player_id")



def transform_features(features, include_path=True):
    names = FEATURES if include_path else ACTIVITY_FEATURES
    if not isinstance(features, pd.DataFrame) or features.empty or not set(names).issubset(features):
        raise ValueError("A non-empty table containing all defined features is required.")
    if not features.index.is_unique:
        raise ValueError("Player feature indices must be unique.")
    matrix = features[names].astype(float).copy()
    if not np.isfinite(matrix.to_numpy()).all() or (matrix < 0).any().any():
        raise ValueError("Features must be finite and non-negative.")
    for name in ["active_day_fraction", "site_entropy", "hour_concentration"]:
        if (matrix[name] > 1 + 1e-12).any():
            raise ValueError(f"{name} must lie between zero and one.")
    logarithmic = [name for name in LOG_FEATURES if name in names]
    matrix[logarithmic] = np.log1p(matrix[logarithmic])
    return matrix

