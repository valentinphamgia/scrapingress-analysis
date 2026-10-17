# Provenance and selection decisions

Source inspected locally: `scrapingress-main.zip`. The archive remains outside this new folder and was not altered or uploaded. Initial source selection inspected code without loading records. Following the user’s explicit request, a later local-only workflow read the source SQLite records to build a pseudonymised reduced-schema derivative. Cookies were not used. Neither source records nor the derivative are part of the source export.

The original README is empty and no LICENSE file was present in the archive listing. The original notebooks have overlapping exploratory implementations and depend on local databases or CSV files. The goal here is a small, independently implemented methodology demonstration, not an exact archive copy.

## Retained concepts, newly implemented

- Timestamped event schema, reduced to the five fields required for the synthetic demonstration.
- Player-specific session segmentation with a 30-minute inactivity threshold.
- Behavioural features, standardisation, K-means, DBSCAN and PCA visualisation.
- Added Gaussian mixture comparison, noise coverage, bootstrap stability and temporal partition agreement.

## Excluded artifacts

- SQLite databases and source JSON exports are excluded from the source export. A separate local pseudonymised SQLite derivative is available for private analysis.
- Cookies, collection scripts, servers and credential-bearing connection code: unnecessary for a reproducible offline demo.
- Notebooks and their outputs, player heatmaps, addresses, portal lists, posters and screenshots: may reveal player-level data or contain unverified claims; no outputs were copied.
- Blender files, meshes, map images and nested site archives: unnecessary to the first research question.
- Source summary CSV: includes real example-agent identifiers, so even an aggregate-looking file was not reused.

## Observed issues motivating the rewrite

These are static inspection findings, not an exhaustive executed audit:

1. A notebook describes spatial zones as 5 km, while a Haversine DBSCAN call uses `eps=0.05 / R_EARTH_KM`, which is 0.05 km (50 m). The new demo avoids this ambiguity: spatial distance has explicit km units, and DBSCAN operates in standardised behavioural feature space.
2. Some session-distance code approximates longitude/latitude steps with one degrees-to-km multiplier. The new code uses Haversine and does not connect independent sessions.
3. Number of visited zones does not directly determine travelled kilometres. The new feature names explicitly refer to observed path length.
4. In the source, silhouette calculations can exclude DBSCAN noise without foregrounding the coverage. Both quantities are reported here.
5. Original trajectory routines contain random distance substitutions and interpolation edge cases. Those routines were not copied into this first release.

## Collective work

The source activity log attributes session-related work to Valentin, clustering-related work to Corine, trajectory-comparison work to Allan, and collection/infrastructure/3D work to Jean-Baptiste, with additional overlapping contributions. This summary is partial and must not replace the team's full attribution.

This version reorganises and extends the original project. The contribution summary above concerns the original collective work; subsequent extensions and the new empirical analysis are documented separately.

## Module refactoring

The new implementation separates schema validation, geometry, sessions, feature computation, model fitting, evaluation, plotting and exports. `experiment.py` is the orchestrator. The function guide records what is implemented and what is still proposed; no original notebook is required to run this study.

## Real-event semantics and quality corrections

The local real database contains simultaneous event sites for some player/timestamp groups. Those are not automatically labelled invalid physical positions: the activity-only mode preserves the events and omits path features. Missing observations are retained in the derivative and counted if excluded from analysis. Calendar-day fractions, identifier validation, duplicate policies, configurable grids, diagnostics for all model families and regression/end-to-end tests were added after review.
