# Scrapingress — Event Activity & Behavioural Clustering

A reproducible clustering study inspired by the collective Scrapingress project at Télécom Paris. It asks **how behavioural partitions change under model choice, resampling, observation windows, session thresholds and scaling**.

## Findings from the real-event reanalysis

[Read the conclusions and aggregate cluster profiles](reports/CONCLUSIONS.md). The study describes observed activity levels and frequency, with explicit coverage and stability limits. The public report contains aggregate statistics; the database and individual assignments remain private.

## Project context

The original work was a **four-student ARTISHOW project at Télécom Paris (2024–2025), conducted for Julien Morel**. This repository is a subsequently refactored and extended implementation. Its new empirical analysis is distinct from the original team's notebook findings; it does not claim that all new methods were used during ARTISHOW.

There are two deliberately distinct execution modes:

- **Public demo:** entirely synthetic events, with no original observations or real-data-fitted parameters.
- **Local private analysis:** real event records with keyed replacement identifiers. Coordinates and timestamps remain sensitive; this is **pseudonymisation, not anonymisation**. No private database or output is part of the source export.

See [DATA_NOTICE.md](DATA_NOTICE.md) for the distinction.

## Quick start: public synthetic demo

Tested with Python 3.9.6. The pinned dependencies support Python 3.9–3.12.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install pip==25.3
python -m pip install -r requirements-lock.txt
python -m pip install --no-deps --no-build-isolation -e .
python -m unittest discover -s tests -v
scrapingress-demo --seed 42 --output reports/demo
```

The synthetic CLI never reads a database. Configuration is explicit:

```bash
scrapingress-demo --clusters 2 3 4 --dbscan-eps 0.8 1.2 1.8 --repetitions 10 --gap-minutes 30
```

Use `--no-sensitivity` to skip the larger sensitivity experiment. Changing a comparison grid changes the experiment, not an automatically selected winner.

## Implemented workflow

1. Validate IDs, timestamps and coordinates. Reject blank IDs, duplicate event IDs and ambiguous duplicate observations. Distinct simultaneous actions are retained when distinct `event_id` values are present.
2. Segment sessions independently for each player at gaps **strictly greater than** the chosen threshold.
3. Build interpretable activity features inside `[start, end)`. The fraction of active days uses the **number of UTC calendar dates intersecting the window**, including partial dates, so it remains in `[0,1]` for one-hour and midnight-crossing windows.
4. Apply prespecified `log1p` transforms to count/duration/distance features, then standardise.
5. Compare K-means and Gaussian mixtures for configurable `k`, plus configurable DBSCAN radii. The default grid has twelve configurations.
6. Report coverage, silhouette, Davies–Bouldin and Calinski–Harabasz on assigned observations. GMM also reports AIC, BIC and convergence. Undefined scores are JSON null, not zero.
7. Evaluate **every candidate family** by repeated player subsampling, refitting preprocessing. Report ARI including noise and ARI restricted to players assigned by both partitions, with their coverage. The latter is undefined for all-noise or one-cluster comparisons.
8. Independently refit each candidate in the two halves of the observation window and compare common players.
9. Evaluate sensitivity to session gaps of 15/30/60 minutes and StandardScaler versus RobustScaler. These descriptive comparisons do not constitute a final test set.
10. Save metrics, profiles and a PCA visualisation. PCA is used only for plotting; clustering uses all selected transformed features.

## Activity features

- Fraction of observed UTC dates with activity.
- Events per active day.
- Mean distinct event sites per active day.
- Sessions per active day.
- Median observed session duration.
- Normalised entropy of visited event sites.
- Circular concentration of UTC activity hours.

The synthetic demo additionally measures median observed within-session path length using Haversine in kilometres. **The private real-event mode excludes this feature:** several sites may be associated with one player at one instant, and event sites are not verified successive player positions. No invented order or physical route is inferred.

## Outputs

Public demo outputs are written under the requested reports directory and ignored by Git:

| Artifact | Contents |
| --- | --- |
| `DATA_NOTICE.txt` | Explicit data-provenance notice |
| `metrics.json` | Configuration, versions, feature list, model diagnostics, resampling, temporal comparisons and sensitivity |
| `synthetic_features.csv` | Fictional player features |
| `synthetic_assignments.csv` | Candidate partitions |
| `synthetic_cluster_medians.csv` | Interpretable profile medians for the first prespecified K-means candidate |
| `synthetic_clusters.png` | Two-component PCA view |

Private-mode outputs use a `private_` prefix and must stay local. The reference K-means configuration shown in profiles/plots is chosen before fitting as the first configured cluster count, not claimed as a discovered truth.

## Local private data

The provided source archive is not needed for the public demo. For local pseudonymisation and analysis, follow [docs/PRIVATE_DATA.md](docs/PRIVATE_DATA.md).

The derivative database retains all source rows and event multiplicity, replacing original event/player/site identifiers with domain-separated HMAC-SHA256 codes. Names, addresses and free text are omitted. The secret key stays in a separate local file and is excluded from export.

Incomplete rows stay in the derivative database but are counted and excluded from analysis. Distinct simultaneous sites are preserved for activity analysis. The source archive is never modified. No server, public API or automatic upload is included.

## Interpretation and limitations

- Synthetic results demonstrate the method and code; they do not establish findings about Ingress or finance. The generator remains a toy model without a road network or calibrated travel speeds.
- Session duration is observed span, not continuous playing time. Collection downtime cannot be inferred from zero observations.
- Rejecting ambiguous duplicates is a policy, not proof that every duplicate in a source system is erroneous. Event IDs preserve legitimate simultaneous actions.
- Silhouette depends on distance and representation. Always interpret DBSCAN scores together with assigned coverage.
- All-noise assignments can yield ARI=1; jointly assigned ARI is intentionally null in that case. Stability alone does not establish useful behavioural categories.
- Resampling evaluates descriptive stability on overlapping players, not future predictive accuracy. Min/max across repetitions are not confidence intervals.
- Temporal comparisons independently refit each period; they do not score a frozen predictive model.
- AIC/BIC compare GMM alternatives within a fixed representation; they should not be used to rank different scalings or unrelated model families.
- No home/workplace inference, identity inference, supervised forecast, allocation optimiser or financial backtest is implemented.

## Organisation

```text
src/scrapingress/
  synthetic.py       fictional observations
  private_data.py    read-only local pseudonymised database loader
  validation.py      schema, IDs, duplicates and simultaneous-site policy
  geometry.py        Haversine in kilometres
  sessions.py        inactivity segmentation; optional observed path steps
  features.py        interpretable window-specific features
  clustering.py      validated model grid and comparative fitting
  evaluation.py      metrics, resampling and temporal agreement
  sensitivity.py     session-gap and scaling comparisons
  plotting.py        PCA visualisation
  reporting.py       results and data-provenance notices
  experiment.py      configuration, orchestration and public synthetic CLI
scripts/             local pseudonymisation/analysis and allowlist source export
tests/               regression, end-to-end, mathematical and export-boundary checks
docs/                methods, function guide, provenance and roadmap
```

See [docs/FUNCTIONS.md](docs/FUNCTIONS.md) for function inputs and outputs, and [reports/README.md](reports/README.md) for the checked synthetic run.

## Authorship and provenance

The original [Scrapingress project](https://gitlab.telecom-paris.fr/proj104/2024-2025/scrapingress) is collective work. Its log attributes session work to Valentin and other parts to Allan, Corine and Jean-Baptiste. This repository contains a refactored implementation and subsequent extensions of that work, with a separately documented empirical reanalysis.

No original license was found in the archive; original implementations and notebooks are not redistributed here. See [docs/PROVENANCE.md](docs/PROVENANCE.md).

## Source export

```bash
python scripts/export_public.py ../scrapingress-public-source-v3.zip
```

Only an explicit source/documentation allowlist is exported, with SHA-256 checksums. The exporter rejects symlinks and refuses to overwrite an existing archive. The database, key, original ZIP, environments and generated results are excluded. **Do not share the entire workspace as a substitute for this source export.**

## References

- [scikit-learn clustering and evaluation](https://scikit-learn.org/stable/modules/clustering.html)
- [StandardScaler](https://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.StandardScaler.html)
- [NumPy random Generator](https://numpy.org/doc/stable/reference/random/generator.html)

Forecasting and constrained allocation remain proposals in [docs/ROADMAP.md](docs/ROADMAP.md).
