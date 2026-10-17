"""Run descriptive clustering experiments with explicit data provenance."""
import argparse
from dataclasses import dataclass, asdict, field
from importlib.metadata import version
from pathlib import Path
import math
import platform
import pandas as pd
from .synthetic import generate_events
from .features import compute_player_features
from .clustering import ModelGrid, compare_models, candidate_models
from .evaluation import subsample_stability, temporal_model_stability
from .sensitivity import sensitivity_study
from .plotting import plot_clusters
from .reporting import DATA_NOTICE, PRIVATE_NOTICE, save_results


@dataclass(frozen=True)
class ExperimentConfig:
    seed: int = 42
    players: int = 120
    days: int = 42
    gap_minutes: float = 30
    repetitions: int = 10
    grid: ModelGrid = field(default_factory=ModelGrid)
    sensitivity: bool = True

    def __post_init__(self):
        if self.players < 12 or self.days < 14:
            raise ValueError("Use at least 12 players and 14 days.")
        if not math.isfinite(self.gap_minutes) or self.gap_minutes <= 0:
            raise ValueError("gap_minutes must be finite and positive.")
        if not isinstance(self.repetitions, int) or self.repetitions < 2:
            raise ValueError("At least two repetitions are required.")


def analyse_events(events, start, end, config, output, synthetic=True, quality=None):
    """Analyse observations locally; private event-site data exclude path features.

    No HTTP service or upload is involved. Private results must remain private.
    """
    output = Path(output)
    start, end = pd.Timestamp(start), pd.Timestamp(end)
    middle = start + (end - start) / 2
    include_path = synthetic
    def features(a, b):
        return compute_player_features(events, a, b, config.gap_minutes, include_path=include_path)
    full, early, late = features(start, end), features(start, middle), features(middle, end)
    matrix, comparison, labels = compare_models(full, config.seed, config.grid, include_path=include_path)
    models = list(candidate_models(config.seed, config.grid))
    reference = next(name for name, _ in models if name.startswith("kmeans_"))
    report = {
        "data_kind": "synthetic" if synthetic else "private_pseudonymised",
        "data_notice": DATA_NOTICE if synthetic else PRIVATE_NOTICE,
        "configuration": {**asdict(config), "output": str(output)},
        "window": {"start_inclusive": str(start), "end_exclusive": str(end)},
        "events_in_window": int(((events.timestamp >= start) & (events.timestamp < end)).sum()),
        "eligible_players": len(full), "features": full.columns.tolist(),
        "quality": quality or {}, "reference_model": reference,
        "models": comparison,
        "subsample_stability": {
            name: subsample_stability(full, model, config.seed, config.repetitions, include_path=include_path)
            for name, model in models},
        "temporal_stability": {
            name: temporal_model_stability(early, late, model, include_path=include_path)
            for name, model in models},
        "versions": {name: version(name) for name in
                     ["numpy", "pandas", "scipy", "scikit-learn", "matplotlib"]},
        "python": platform.python_version(),
    }
    if config.sensitivity:
        report["sensitivity"] = sensitivity_study(events, start, end, config.seed, config.grid,
                                                  include_path=include_path)
    save_results(full, labels, report, output)
    plot_clusters(matrix, labels[reference], output / ("synthetic_clusters.png" if synthetic else "private_clusters.png"),
                  title=("Synthetic players" if synthetic else "Private event-activity profiles") + " · " + reference)
    return report


def run_experiment(config, output):
    """Generate entirely fictional events and run the shared analysis."""
    events = generate_events(config.seed, config.players, config.days)
    start = pd.Timestamp("2024-01-01", tz="UTC")
    end = start + pd.Timedelta(days=config.days)
    return analyse_events(events, start, end, config, output)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Synthetic-only mobility clustering demo.")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--players", type=int, default=120)
    parser.add_argument("--days", type=int, default=42)
    parser.add_argument("--gap-minutes", type=float, default=30)
    parser.add_argument("--repetitions", type=int, default=10)
    parser.add_argument("--clusters", nargs="+", type=int, default=[2, 3, 4, 5])
    parser.add_argument("--dbscan-eps", nargs="+", type=float, default=[.8, 1.2, 1.8, 2.4])
    parser.add_argument("--no-sensitivity", action="store_true")
    parser.add_argument("--output", type=Path, default=Path("reports/demo"))
    args = parser.parse_args(argv)
    try:
        grid = ModelGrid(tuple(args.clusters), tuple(args.dbscan_eps))
        config = ExperimentConfig(args.seed, args.players, args.days, args.gap_minutes,
                                  args.repetitions, grid, not args.no_sensitivity)
    except ValueError as exc:
        parser.error(str(exc))
    print(DATA_NOTICE)
    report = run_experiment(config, args.output)
    print(f"Synthetic-only experiment completed: {args.output}")
    print(f"{report['events_in_window']} events; {report['eligible_players']} eligible fictional players; "
          f"{len(report['models'])} model configurations")


if __name__ == "__main__":
    main()
