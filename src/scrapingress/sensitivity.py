"""Predefined sensitivity experiments, without selecting a claimed winner."""
import pandas as pd
from .features import compute_player_features
from .clustering import compare_models
from .evaluation import partition_agreement


def sensitivity_study(events, start, end, seed=42, grid=None, gaps=(15, 30, 60), include_path=True):
    baseline_features = compute_player_features(events, start, end, gap_minutes=30, include_path=include_path)
    _, _, reference = compare_models(baseline_features, seed, grid, include_path=include_path)
    reference = pd.DataFrame(reference, index=baseline_features.index)
    rows = []
    for gap in gaps:
        features = compute_player_features(events, start, end, gap_minutes=gap, include_path=include_path)
        for scaling in ("standard", "robust"):
            _, metrics, assignments = compare_models(features, seed, grid, scaling=scaling, include_path=include_path)
            assignments = pd.DataFrame(assignments, index=features.index)
            common = reference.index.intersection(assignments.index)
            for row in metrics:
                name = row["model"]
                rows.append({"session_gap_minutes": gap, "scaling": scaling,
                             "common_players": len(common), **row,
                             **partition_agreement(reference.loc[common, name], assignments.loc[common, name])})
    return {"reference": "30-minute sessions and standard scaling",
            "interpretation": "Descriptive parameter sensitivity, not test-set model selection.",
            "comparisons": rows}
