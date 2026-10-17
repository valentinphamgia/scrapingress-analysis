# Research progression

## Implemented: synthetic clustering study

The current runnable version provides features, configurable candidate comparisons, all-family resampling and temporal agreement, sensitivity experiments, and an optional local private activity workflow. It intentionally reports no real-world conclusions and does not select a winning configuration from the same exploratory metric grid.

## Implemented: sensitivity study

The current sensitivity experiment sweeps session gaps (15/30/60 minutes) and StandardScaler/RobustScaler for every model family. Further work can examine feature ablations and eligible-player thresholds. Report changes in coverage and partitions. Explain K-means inertia, GMM likelihood, DBSCAN density assumptions and ARI before adding more estimators. Define reasonable perturbations before observing their scores.

## Proposed: activity forecasting

Forecast zone-level next-day event counts. Start with previous-day and seasonal-mean baselines, then Poisson regression and gradient boosting. Use chronological train/validation/test windows and past-only transformations. If clustering-derived features are used, fit the partition on training data only; the current exploratory clustering code is not a forecasting preprocessing pipeline. Compare errors and uncertainty, including performance during activity shifts.

Prerequisite: a synthetic observation generator with explicit collection uptime and predictable zone-level temporal dynamics. Real collection gaps are not genuine zero-activity observations.

## Proposed: constrained collection allocation

Given forecast activity, allocate a fixed number of hypothetical requests under per-zone limits and coverage constraints. Compare uniform allocation, historical-activity allocation and an integer-linear optimisation model. Define the relationship between a request and captured events, account for repeated observations and evaluate on held-out simulated outcomes. Compare against an oracle only as an upper reference, not an achievable baseline.

This stage is an offline simulator, not a live scraping service. Do not claim increased real-world collection performance from a toy simulation.

## Optional: finance transfer

A separate dataset and repository could study clustering of assets or activity regimes. State the financial question, information availability, universe construction, survivorship issues and train/test boundaries. Mobility clusters alone do not demonstrate financial forecasting ability.
