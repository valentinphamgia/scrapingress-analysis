"""Mathematical properties and data-boundary checks for the public demo."""
import unittest
import numpy as np
import pandas as pd
from scrapingress.geometry import haversine_km
from scrapingress.sessions import identify_sessions
from scrapingress.features import compute_player_features, FEATURES
from scrapingress.synthetic import generate_events
from scrapingress.evaluation import partition_metrics, temporal_stability


def events():
    return pd.DataFrame({
        "player_id": ["synthetic_0000"] * 4 + ["synthetic_0001"],
        "timestamp": ["2024-01-01T00:00:00Z", "2024-01-01T00:30:00Z",
                      "2024-01-01T01:01:00Z", "2024-01-02T00:00:00Z",
                      "2024-01-01T00:00:00Z"],
        "site_id": ["a", "b", "c", "a", "z"],
        "latitude": [0., 0., 0., 0., 20.],
        "longitude": [0., 1., 2., 0., 20.]})


class GeometryTests(unittest.TestCase):
    def test_distance_units_symmetry_and_date_line(self):
        self.assertEqual(float(haversine_km(0, 0, 0, 0)), 0.)
        self.assertAlmostEqual(float(haversine_km(0, 0, 0, 1)), 111.195, places=3)
        self.assertAlmostEqual(float(haversine_km(30, 40, 50, 60)),
                               float(haversine_km(50, 60, 30, 40)), places=10)
        self.assertAlmostEqual(float(haversine_km(0, 179.5, 0, -179.5)), 111.195, places=3)

    def test_session_boundary_and_no_cross_player_or_cross_session_distance(self):
        frame = identify_sessions(events().sample(frac=1, random_state=4))
        a = frame[frame.player_id == "synthetic_0000"]
        self.assertEqual(a.session_id.tolist(), [1, 1, 2, 3])
        self.assertAlmostEqual(a.observed_step_km.sum(), 111.195, places=3)
        b = frame[frame.player_id == "synthetic_0001"]
        self.assertEqual(b.observed_step_km.sum(), 0.)

    def test_invalid_location_and_threshold_rejected(self):
        bad = events(); bad.loc[0, "latitude"] = 95
        with self.assertRaises(ValueError): identify_sessions(bad)
        with self.assertRaises(ValueError): identify_sessions(events(), gap_minutes=0)
        bad = events(); bad.loc[0, "longitude"] = np.nan
        with self.assertRaises(ValueError): identify_sessions(bad)


class FeatureTests(unittest.TestCase):
    def test_future_events_do_not_change_earlier_features(self):
        bounds = (pd.Timestamp("2024-01-01", tz="UTC"), pd.Timestamp("2024-01-02", tz="UTC"))
        all_events = events()
        without_future = all_events.iloc[[0, 1, 2, 4]]
        first = compute_player_features(all_events, *bounds, min_events=1)
        second = compute_player_features(without_future, *bounds, min_events=1)
        pd.testing.assert_frame_equal(first, second)
        self.assertEqual(first.loc["synthetic_0000", "active_day_fraction"], 1.)
        self.assertEqual(first.loc["synthetic_0000", "sessions_per_active_day"], 2.)
        self.assertEqual(first.loc["synthetic_0001", "site_entropy"], 0.)

    def test_generator_is_reproducible_and_features_are_finite(self):
        first = generate_events(seed=19, players=12, days=14)
        pd.testing.assert_frame_equal(first, generate_events(seed=19, players=12, days=14))
        self.assertTrue(first.player_id.str.startswith("synthetic_").all())
        frame = compute_player_features(first, pd.Timestamp("2024-01-01", tz="UTC"),
                               pd.Timestamp("2024-01-15", tz="UTC"))
        self.assertTrue(np.isfinite(frame[FEATURES]).all().all())
        self.assertTrue(frame.active_day_fraction.between(0, 1).all())
        self.assertTrue(frame.site_entropy.between(0, 1.00000001).all())

    def test_uninformative_clusterings_report_no_silhouette(self):
        matrix = np.array([[0.], [1.], [2.], [3.]])
        for labels in [[-1]*4, [0]*4, [0, 1, 2, 3]]:
            self.assertIsNone(partition_metrics(matrix, labels)["silhouette_assigned_only"])
        result = partition_metrics(matrix, [-1, -1, 0, 0])
        self.assertEqual(result["coverage"], .5)
        self.assertEqual(result["clusters"], 1)

    def test_temporal_comparison_with_disjoint_players(self):
        first = pd.DataFrame(columns=FEATURES, index=["a"])
        second = pd.DataFrame(columns=FEATURES, index=["b"])
        self.assertIsNone(temporal_stability(first, second)["ari"])


if __name__ == "__main__":
    unittest.main()
