# Functions and module map

There is an entirely synthetic public demo and a separate local, private workflow for pseudonymised real events. See `PRIVATE_DATA.md`. All source exports exclude the database, key and private results.

| Module | Main function/class | Responsibility |
| --- | --- | --- |
| `synthetic.py` | `generate_events(seed, players, days)` | Generate fictional observations; no real-data calibration |
| `private_data.py` | `load_private_events(database)` | Open the reduced local database read-only; count incomplete rows; retain distinct event IDs |
| `validation.py` | `validate_events(events, allow_simultaneous_sites=False)` | Reject blank IDs, invalid coordinates, duplicate events and—by default—simultaneous conflicting positions |
| `geometry.py` | `haversine_km(...)` | Great-circle distance from degrees to kilometres |
| `sessions.py` | `identify_sessions(events, gap_minutes=30, include_path=True)` | Session boundaries; optional observed path steps |
| `features.py` | `compute_player_features(..., include_path=True)` | Eight synthetic-demo features, or seven activity-only real-event features |
| `features.py` | `transform_features(features, include_path=True)` | Validate feature ranges and apply prespecified log transforms |
| `clustering.py` | `ModelGrid`, `candidate_models`, `compare_models` | Validated parameter grid, Standard/Robust scaling, K-means/GMM/DBSCAN, convergence and GMM AIC/BIC |
| `evaluation.py` | `partition_metrics` | Coverage, silhouette, Davies–Bouldin and Calinski–Harabasz on assigned observations |
| `evaluation.py` | `partition_agreement` | ARI with noise, jointly assigned ARI and joint assignment coverage |
| `evaluation.py` | `subsample_stability` | Refit all three model families on repeated player subsets, including refitted scaling |
| `evaluation.py` | `temporal_model_stability` | Independently fit a candidate in two time windows and compare common players |
| `evaluation.py` | `bootstrap_stability`, `temporal_stability` | Supplementary K-means-only diagnostics; not the comparative experiment's primary evaluation |
| `sensitivity.py` | `sensitivity_study` | Compare 15/30/60-minute gaps and StandardScaler/RobustScaler for all configured candidates |
| `plotting.py` | `plot_clusters` | PCA visualisation, separate from clustering |
| `reporting.py` | `save_results` | Explicit synthetic/private notices, metrics and profile exports |
| `experiment.py` | `ExperimentConfig`, `analyse_events`, `run_experiment`, `main` | Validated configuration, shared orchestration and synthetic CLI |
| `scripts/pseudonymize_database.py` | `pseudonymize` | Create a fresh local derivative with keyed replacement IDs and reduced schema |
| `scripts/analyse_private.py` | `main` | Run the activity-only private workflow |
| `scripts/export_public.py` | `export` | Source/documentation allowlist and checksums; never package private observations |

## Input policies

`[start, end)` windows are converted to UTC. Active-day fraction divides by the number of UTC calendar dates touched by the window, including partial dates. The minimum event count must be a positive integer. Missing/invalid identifiers are rejected. Exact observation duplicates without event IDs are rejected; distinct co-located simultaneous actions are retained if their event IDs differ. A duplicated event ID is rejected even if other fields differ.

Multiple simultaneous event sites are rejected in path mode. Activity-only mode explicitly allows them and produces no path feature. It does not invent routes or discard these valid game events.

## Implemented versus proposed

Implemented: descriptive clustering, comparison, resampling and temporal/sensitivity diagnostics, synthetic visualisation, local real-event activity analysis and source export.

Not implemented: HDBSCAN, DTW, supervised prediction, financial backtests, live collection or constrained request-allocation optimisation. K-means and GMM optimise their own objectives; that does not make this a resource-allocation optimiser.
