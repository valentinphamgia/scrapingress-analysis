"""Generate fictional events without reading or fitting to real player records."""
import numpy as np
import pandas as pd


def generate_events(seed=42, players=120, days=42):
    if players < 12 or days < 14:
        raise ValueError("Use at least 12 players and 14 days.")
    rng = np.random.default_rng(seed)
    # Arbitrary fictional sites, not copied from the source archive.
    sites = np.column_stack((12 + rng.uniform(0, .12, 36),
                             -35 + rng.uniform(0, .12, 36)))
    start = pd.Timestamp("2024-01-01", tz="UTC")
    rows = []
    for player in range(players):
        # Continuous latent traits: there is no imposed 'correct' cluster count.
        frequency = rng.uniform(.12, .94)
        roaming = rng.uniform(0, 1)
        length = rng.uniform(2, 12)
        preferred_hour = rng.choice([8, 13, 19])
        favourites = rng.choice(len(sites), size=int(2 + 9 * roaming), replace=False)
        for day in range(days):
            if rng.random() > frequency:
                continue
            previous_end = None
            day_end = start + pd.Timedelta(days=day + 1)
            for session in range(1 + int(rng.random() < roaming * .6)):
                hour = int(np.clip(preferred_hour + rng.normal(0, 1.5), 1, 21))
                minutes = hour * 60 + session * 90 + rng.integers(0, 20)
                timestamp = start + pd.Timedelta(days=day, minutes=int(minutes))
                if previous_end is not None:
                    timestamp = max(timestamp, previous_end + pd.Timedelta(minutes=31))
                count = int(rng.poisson(length) + 1)
                for _ in range(count):
                    site = int(rng.choice(favourites if rng.random() > roaming * .3
                                          else np.arange(len(sites))))
                    timestamp += pd.Timedelta(seconds=int(rng.integers(70, 240)))
                    if timestamp >= day_end:
                        break
                    rows.append((f"synthetic_{player:04d}", timestamp,
                                 f"fictional_site_{site:02d}", *sites[site]))
                previous_end = timestamp
    return pd.DataFrame(rows, columns=["player_id", "timestamp", "site_id",
                                      "latitude", "longitude"]).sort_values(
                                          ["player_id", "timestamp"]).reset_index(drop=True)
