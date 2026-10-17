"""Identify player-specific sessions from validated timestamped events."""
import numpy as np
from .geometry import haversine_km
from .validation import validate_events


def identify_sessions(events, gap_minutes=30, include_path=True):
    """Start a new session on a gap strictly greater than the threshold."""
    if not np.isfinite(gap_minutes) or gap_minutes <= 0:
        raise ValueError("gap_minutes must be finite and positive.")
    df = validate_events(events, allow_simultaneous_sites=not include_path)
    groups = df.groupby("player_id", sort=False)
    gaps = groups["timestamp"].diff().dt.total_seconds() / 60
    starts = gaps.isna() | (gaps > gap_minutes)
    df["session_id"] = starts.groupby(df["player_id"]).cumsum().astype(int)
    if include_path:
        previous = groups[["latitude", "longitude"]].shift()
        distances = haversine_km(previous["latitude"], previous["longitude"],
                                df["latitude"], df["longitude"])
        # Do not connect separate players or separate sessions.
        df["observed_step_km"] = np.where(starts, 0.0, distances)
    return df

