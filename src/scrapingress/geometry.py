"""Geodesic calculations with explicit input and output units."""
import numpy as np


def haversine_km(lat1, lon1, lat2, lon2):
    """Great-circle distance; inputs are degrees, output is kilometres."""
    lat1, lon1, lat2, lon2 = [np.radians(np.asarray(x, dtype=float))
                             for x in (lat1, lon1, lat2, lon2)]
    a = np.sin((lat2 - lat1) / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin((lon2 - lon1) / 2) ** 2
    return 6371.0088 * 2 * np.arcsin(np.sqrt(np.clip(a, 0, 1)))

