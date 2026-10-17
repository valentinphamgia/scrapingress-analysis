"""Regression tests for partial days, dirty inputs and comparative evaluation."""
from dataclasses import replace
import json
from pathlib import Path
import tempfile
import unittest
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from scrapingress.features import compute_player_features, transform_features
from scrapingress.validation import validate_events
from scrapingress.sessions import identify_sessions
from scrapingress.clustering import ModelGrid, compare_models
from scrapingress.evaluation import partition_metrics, partition_agreement, subsample_stability, bootstrap_stability
from scrapingress.experiment import ExperimentConfig, run_experiment
from scrapingress.synthetic import generate_events


def sample():
    return pd.DataFrame({"player_id": ["fictional_p"] * 5, "site_id": ["fictional_site"] * 5,
                         "timestamp": pd.date_range("2024-01-01T08:00Z", periods=5, freq="min"),
                         "latitude": [0.] * 5, "longitude": [0.] * 5})


class WindowTests(unittest.TestCase):
    def test_one_hour_activity_fraction_is_one(self):
        result = compute_player_features(sample(), pd.Timestamp("2024-01-01T08:00Z"),
                                         pd.Timestamp("2024-01-01T09:00Z"))
        self.assertEqual(result.active_day_fraction.iloc[0], 1.)

    def test_partial_days_and_equivalent_timezones(self):
        frame = sample()
        frame.timestamp = pd.date_range("2024-01-01T23:59:00Z", periods=5, freq="min")
        start, end = pd.Timestamp("2024-01-01T23:58Z"), pd.Timestamp("2024-01-02T00:04Z")
        first = compute_player_features(frame, start, end)
        second = compute_player_features(frame, start.tz_convert("America/New_York"), end.tz_convert("America/New_York"))
        pd.testing.assert_frame_equal(first, second)
        self.assertEqual(first.active_day_fraction.iloc[0], 1.)

    def test_midnight_end_excludes_next_day(self):
        result = compute_player_features(sample(), pd.Timestamp("2024-01-01T00:00Z"),
                                         pd.Timestamp("2024-01-02T00:00Z"))
        self.assertEqual(result.active_day_fraction.iloc[0], 1.)

    def test_invalid_windows_and_minimum_count(self):
        for start, end in [("2024-01-01", "2024-01-02"), (pd.NaT, pd.Timestamp("2024-01-02T00:00Z")),
                           ("2024-01-02T00:00Z", "2024-01-01T00:00Z")]:
            with self.assertRaises(ValueError): compute_player_features(sample(), start, end)
        for count in [0, -1, 1.5, True]:
            with self.assertRaises(ValueError):
                compute_player_features(sample(), "2024-01-01T00:00Z", "2024-01-02T00:00Z", min_events=count)


class ValidationTests(unittest.TestCase):
    def test_blank_and_nonstring_identifiers_rejected(self):
        for column in ["player_id", "site_id"]:
            for value in ["", "   ", 123, None]:
                frame = sample(); frame.loc[0, column] = value
                with self.assertRaises(ValueError): validate_events(frame)

    def test_duplicates_rejected_without_mutating_input(self):
        frame = pd.concat([sample(), sample().iloc[[0]]], ignore_index=True)
        with self.assertRaises(ValueError): validate_events(frame)
        self.assertEqual(len(frame), 6)

    def test_simultaneous_colocated_actions_need_distinct_event_ids(self):
        frame = pd.concat([sample(), sample().iloc[[0]]], ignore_index=True)
        frame["event_id"] = ["fictional_" + str(i) for i in range(len(frame))]
        self.assertEqual(len(validate_events(frame)), 6)
        frame.loc[5, "event_id"] = frame.loc[0, "event_id"]
        with self.assertRaises(ValueError): validate_events(frame)

    def test_simultaneous_sites_are_explicitly_allowed_only_for_activity(self):
        frame = sample(); frame.loc[1, "timestamp"] = frame.loc[0, "timestamp"]
        frame.loc[1, "latitude"] = 1.
        with self.assertRaises(ValueError): identify_sessions(frame)
        result = identify_sessions(frame, include_path=False)
        self.assertNotIn("observed_step_km", result)
        features = compute_player_features(frame, "2024-01-01T00:00Z", "2024-01-02T00:00Z", include_path=False)
        self.assertNotIn("median_observed_path_km", features)
        self.assertEqual(features.events_per_active_day.iloc[0], 5)
        self.assertTrue(np.isfinite(transform_features(features, include_path=False)).all().all())


class EvaluationTests(unittest.TestCase):
    def setUp(self):
        events = generate_events(players=24, days=14)
        self.features = compute_player_features(events, "2024-01-01T00:00Z", "2024-01-15T00:00Z")

    def test_grid_validation(self):
        for args in [{"clusters": (1,)}, {"clusters": (2, 2)}, {"dbscan_eps": (0.,)},
                     {"dbscan_eps": (float("nan"),)}, {"min_samples": 1}]:
            with self.assertRaises(ValueError): ModelGrid(**args)

    def test_all_model_families_have_stability_and_gmm_fit_diagnostics(self):
        from scrapingress.clustering import candidate_models
        grid = ModelGrid((2,), (1.2,))
        _, rows, labels = compare_models(self.features, grid=grid)
        gmm = next(r for r in rows if r['model'].startswith('gmm'))
        self.assertTrue(np.isfinite(gmm['bic']))
        self.assertIn('converged', gmm)
        for _, model in candidate_models(42, grid):
            report = subsample_stability(self.features, model, repetitions=2)
            self.assertEqual(len(report['trials']), 2)
            self.assertTrue(0 <= report['jointly_assigned_fraction_mean'] <= 1)

    def test_noise_only_is_not_a_perfect_assigned_partition(self):
        report = partition_agreement([-1] * 5, [-1] * 5)
        self.assertEqual(report['ari_including_noise'], 1.)
        self.assertIsNone(report['ari_jointly_assigned'])
        self.assertEqual(report['jointly_assigned_fraction'], 0.)

    def test_invalid_metrics_and_resampling_arguments(self):
        with self.assertRaises(ValueError): partition_metrics(np.empty((0, 2)), [])
        with self.assertRaises(ValueError): partition_metrics(np.ones((4, 2)), [0, 1])
        with self.assertRaises(ValueError): bootstrap_stability(self.features, repetitions=0)
        with self.assertRaises(ValueError): subsample_stability(self.features, KMeans(2), repetitions=1)

    def test_full_cli_pipeline_reports_all_candidates_and_sensitivity(self):
        config = ExperimentConfig(players=24, days=14, repetitions=2,
                                  grid=ModelGrid((2,), (1.2,)), sensitivity=True)
        with tempfile.TemporaryDirectory() as directory:
            report = run_experiment(config, directory)
            names = set(report['subsample_stability'])
            self.assertEqual(names, {r['model'] for r in report['models']})
            self.assertEqual(names, set(report['temporal_stability']))
            self.assertEqual(len(report['sensitivity']['comparisons']), 18)
            self.assertTrue((Path(directory) / 'synthetic_clusters.png').exists())
            self.assertIn('SYNTHETIC', (Path(directory) / 'DATA_NOTICE.txt').read_text())
            json.dumps(report, allow_nan=False)
