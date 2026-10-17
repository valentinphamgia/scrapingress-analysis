"""Export explicitly selected aggregate statistics, never player-level rows."""
import argparse
import json
from pathlib import Path
import pandas as pd

PROFILE_FEATURES = ["active_day_fraction", "events_per_active_day", "sites_per_active_day",
                    "sessions_per_active_day", "median_session_minutes", "site_entropy",
                    "hour_concentration"]
MODEL_FIELDS = ["model", "clusters", "coverage", "silhouette_assigned_only",
                "davies_bouldin_assigned_only", "calinski_harabasz_assigned_only",
                "bic", "aic", "converged", "convergence_warning"]
AGREEMENT_FIELDS = ["ari_including_noise", "jointly_assigned_fraction", "ari_jointly_assigned"]
STABILITY_FIELDS = ["repetitions", "subsample_fraction", "ari_including_noise_mean",
                    "jointly_assigned_fraction_mean", "ari_jointly_assigned_mean", "defined_assigned_trials"]


def pick(values, keys):
    return {key: values[key] for key in keys if key in values}


def build_report(directory):
    directory = Path(directory)
    metrics = json.loads((directory / "metrics.json").read_text())
    if metrics.get("data_kind") != "private_pseudonymised":
        raise ValueError("Expected a labelled private pseudonymised analysis.")
    features = pd.read_csv(directory / "private_features.csv", index_col=0)
    assignments = pd.read_csv(directory / "private_assignments.csv", index_col=0)
    if not features.index.is_unique or not assignments.index.equals(features.index):
        raise ValueError("Unique, aligned player indices are required.")
    if not set(PROFILE_FEATURES).issubset(features.columns):
        raise ValueError("Missing activity features.")
    profiles = {}
    for model in ("kmeans_k2", "kmeans_k3"):
        if model not in assignments:
            continue
        groups = features[PROFILE_FEATURES].groupby(assignments[model])
        if int(groups.size().min()) < 10:
            raise ValueError("Do not export profiles for groups smaller than ten players.")
        profiles[model] = [
            {"cluster": int(label), "players": int(len(group)),
             "share_percent": round(100 * len(group) / len(features), 1),
             "medians": {name: round(float(group[name].median()), 3) for name in PROFILE_FEATURES}}
            for label, group in groups
        ]
    report = {
        "provenance": "Aggregate output from local real-event reanalysis; database remains private.",
        "public_contents": "Global counts, candidate metrics and medians for groups of at least ten; no members, IDs, coordinates or individual timestamps.",
        "window": pick(metrics["window"], ["start_inclusive", "end_exclusive"]),
        "events_in_window": metrics["events_in_window"],
        "eligible_players": metrics["eligible_players"],
        "quality": pick(metrics["quality"], ["database_rows", "excluded_incomplete_rows", "simultaneous_site_groups", "validated_rows"]),
        "model_grid": metrics["configuration"]["grid"],
        "seed": metrics["configuration"]["seed"],
        "session_gap_minutes": metrics["configuration"]["gap_minutes"],
        "models": [pick(row, MODEL_FIELDS) for row in metrics["models"]],
        "subsample_stability": {name: pick(row, STABILITY_FIELDS) for name, row in metrics["subsample_stability"].items()},
        "temporal_stability": {name: pick(row, ["common_players", "status"] + AGREEMENT_FIELDS)
                               for name, row in metrics["temporal_stability"].items()},
        "cluster_profiles": profiles,
        "versions": metrics["versions"], "python": metrics["python"],
    }
    if "sensitivity" in metrics:
        report["sensitivity"] = {"reference": metrics["sensitivity"]["reference"],
            "comparisons": [pick(row, MODEL_FIELDS + AGREEMENT_FIELDS + ["session_gap_minutes", "scaling", "common_players"])
                            for row in metrics["sensitivity"]["comparisons"]]}
    # Only whitelisted schema fields can leave this function; no source dictionary is copied wholesale.
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--analysis", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = build_report(args.analysis)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print("Wrote aggregate-only report; no player-level observations exported.")
