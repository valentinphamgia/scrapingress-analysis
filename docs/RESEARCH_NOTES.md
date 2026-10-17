# Study design

This is descriptive clustering, not a predictive benchmark. The unit is a player profile within an explicit observation window. Synthetic demo results and private real-event results are distinct artifacts.

## Observation semantics and time windows

Real game events reference sites, not necessarily physical player positions. Simultaneous sites for one player are retained for activity and diversity metrics. The private mode therefore excludes sequential-path features entirely. It never sorts simultaneous locations into an invented route.

The fraction of active days is the number of active UTC dates divided by the number of UTC dates intersecting `[start,end)`. A one-hour observation window touches one date and can yield a fraction of one, never 24. A partial window crossing midnight touches two dates. This is a calendar-day proportion, not a proportion of observed hours.

The source may contain incomplete events. The derivative retains them; the loader reports how many are excluded from validated analysis. Distinct event IDs preserve legitimate action multiplicity. Repeated IDs and ambiguous duplicate observations are rejected, not silently deleted.

## Representation

Count, duration and optional synthetic-path features use `log1p`. Ratios, normalised site entropy and circular hour concentration do not. Standardisation is refitted for every resampling and temporal comparison. RobustScaler is evaluated separately in the sensitivity experiment. Feature definitions and scaling influence all geometric comparisons.

PCA is a two-dimensional visualisation only. Cluster estimators use all selected transformed features.

## Model diagnostics

K-means uses squared Euclidean inertia, GMM uses a Gaussian mixture with covariance regularisation, and DBSCAN identifies dense regions plus noise. DBSCAN eps is in transformed feature units, not kilometres.

Report silhouette, Davies–Bouldin and Calinski–Harabasz on non-noise observations alongside assigned coverage. Silhouette uses at most 2,000 assigned observations with a fixed sampling seed for bounded cost. Undefined partition metrics are null. GMM AIC/BIC and convergence are reported; information criteria only compare GMM alternatives within a fixed representation.

## Stability across every model family

Repeated subsampling without replacement uses 80% of eligible players. For each candidate the full-data reference is compared with a refit on the common subset, including a new scaler. DBSCAN is never asked to predict unseen observations. Report full ARI including noise, jointly assigned ARI, the joint coverage and the number of trials for which assigned ARI is defined. All-noise partitions can have full ARI=1 but jointly assigned ARI=null: they are not treated as a successful behavioural segmentation.

Temporal comparisons independently fit each candidate in the two halves of the window and compare common eligible players. These diagnostics measure descriptive consistency, not future predictive performance.

The supplementary K-means bootstrap routine remains available as a separate function. It is not substituted for evaluation of the other families.

## Sensitivity and interpretation

The fixed sensitivity design compares 15/30/60-minute session gaps and StandardScaler versus RobustScaler, relative to the 30-minute standard-scaled partition. It does not tune on or create a final test set. No candidate is automatically declared a winner from this grid.

A finding about real behaviour requires domain interpretation, observation-coverage analysis and repeatable empirical evidence. Stability on generated data cannot establish such a finding. No financial forecast, causal claim or true behavioural label is inferred.
