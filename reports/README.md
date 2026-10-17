# Checked synthetic run — current implementation

This page summarises the synthetic run. The separately labelled [real-event conclusions](CONCLUSIONS.md) contain selected aggregate statistics; the database and individual outputs remain private.

Command: `scrapingress-demo --seed 42 --repetitions 10 --output reports/updated-demo`

- Generated events in the observation window: 27417.
- Eligible fictional players: 120.
- Candidate configurations: 12.
- Every candidate has ten player-subsampling trials and a temporal partition comparison.
- The sensitivity study contains 72 comparisons across session gaps and scaling methods.
- Twenty-four tests passed, including partial UTC dates, duplicate policies, simultaneous sites, private pseudonymisation, all-family stability, end-to-end output and source export boundaries.

| Model | Clusters excluding noise | Assigned coverage | Assigned-only silhouette |
| --- | --- | --- | --- |
| kmeans_k2 | 2 | 100.0% | 0.250 |
| gmm_k2 | 2 | 100.0% | 0.201 |
| kmeans_k3 | 3 | 100.0% | 0.266 |
| gmm_k3 | 3 | 100.0% | 0.141 |
| kmeans_k4 | 4 | 100.0% | 0.242 |
| gmm_k4 | 4 | 100.0% | 0.199 |
| kmeans_k5 | 5 | 100.0% | 0.238 |
| gmm_k5 | 5 | 100.0% | 0.196 |
| dbscan_eps0.8 | 0 | 0.0% | undefined |
| dbscan_eps1.2 | 2 | 35.0% | 0.414 |
| dbscan_eps1.8 | 1 | 89.2% | undefined |
| dbscan_eps2.4 | 1 | 96.7% | undefined |

No winning model or verified number of real behavioural categories is inferred. Read every DBSCAN score with its coverage. All-noise comparisons have no jointly assigned ARI, even if full ARI equals one. The displayed profile/plot uses the first configured K-means candidate, a prespecified illustration.

The active-day denominator and validation policies have changed after regression review. Previous demonstration snapshots should not be used as the report for this version. Synthetic plotting remains a toy demonstration, without calibrated physical movement speeds. Numerical versions and detailed diagnostics are recorded in regenerated `metrics.json`.
