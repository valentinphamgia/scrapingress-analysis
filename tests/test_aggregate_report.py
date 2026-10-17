"""Ensure aggregate export cannot copy IDs, positions or private report extras."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import pandas as pd

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts' / 'build_aggregate_report.py'
spec = importlib.util.spec_from_file_location('aggregate_report', SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class AggregateReportTests(unittest.TestCase):
    def test_only_approved_aggregates_leave_private_inputs(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            players = ['PRIVATE_SENTINEL_' + str(i) for i in range(30)]
            frame = pd.DataFrame({feature: [.5] * 30 for feature in module.PROFILE_FEATURES}, index=players)
            frame['latitude'] = [88.123456] * 30
            frame.to_csv(root / 'private_features.csv')
            pd.DataFrame({'kmeans_k2': [0] * 15 + [1] * 15}, index=players).to_csv(root / 'private_assignments.csv')
            metrics = {'data_kind': 'private_pseudonymised', 'window': {'start_inclusive': 'study start', 'end_exclusive': 'study end'},
                       'events_in_window': 100, 'eligible_players': 30, 'quality': {'database_rows': 100, 'SECRET_KEY': 'PRIVATE_SENTINEL_KEY'},
                       'configuration': {'grid': {}, 'seed': 42, 'gap_minutes': 30, 'output': 'PRIVATE_SENTINEL_PATH'},
                       'models': [], 'subsample_stability': {}, 'temporal_stability': {}, 'versions': {}, 'python': '3.9'}
            (root / 'metrics.json').write_text(json.dumps(metrics))
            report = module.build_report(root)
            encoded = json.dumps(report)
            self.assertNotIn('PRIVATE_SENTINEL', encoded)
            self.assertNotIn('latitude', encoded)
            self.assertEqual(report['cluster_profiles']['kmeans_k2'][0]['players'], 15)
            self.assertEqual(report['cluster_profiles']['kmeans_k2'][0]['share_percent'], 50.)
            pd.DataFrame({'kmeans_k2': [0] * 5 + [1] * 25}, index=players).to_csv(root / 'private_assignments.csv')
            with self.assertRaises(ValueError): module.build_report(root)
