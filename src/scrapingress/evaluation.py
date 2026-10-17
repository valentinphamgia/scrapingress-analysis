"""Clustering diagnostics and stability; no model-selection winner is inferred."""
import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics import (adjusted_rand_score, silhouette_score,
                             davies_bouldin_score, calinski_harabasz_score)
from sklearn.preprocessing import StandardScaler
from .features import transform_features


def partition_metrics(matrix, labels):
    matrix, labels = np.asarray(matrix, dtype=float), np.asarray(labels)
    if matrix.ndim != 2 or len(matrix) == 0 or not np.isfinite(matrix).all():
        raise ValueError("A non-empty finite feature matrix is required.")
    if labels.ndim != 1 or len(labels) != len(matrix):
        raise ValueError("One label per observation is required.")
    mask = labels != -1
    clusters = np.unique(labels[mask])
    score = davies = calinski = None
    if 1 < len(clusters) < mask.sum():
        score = float(silhouette_score(matrix[mask], labels[mask],
                                      sample_size=min(2000, int(mask.sum())), random_state=42))
        davies = float(davies_bouldin_score(matrix[mask], labels[mask]))
        calinski = float(calinski_harabasz_score(matrix[mask], labels[mask]))
    return {"clusters": int(len(clusters)), "coverage": float(mask.mean()),
            "silhouette_assigned_only": score,
            "davies_bouldin_assigned_only": davies,
            "calinski_harabasz_assigned_only": calinski}



def bootstrap_stability(features, seed=42, clusters=3, repetitions=10, include_path=True):
    """Refit scaler and K-means on bootstrap samples; predict a common player set.

    This measures in-sample resampling sensitivity, not future predictive accuracy.
    """
    if not isinstance(repetitions, int) or repetitions < 2:
        raise ValueError("At least two bootstrap repetitions are required.")
    if not isinstance(clusters, int) or clusters < 2 or len(features) <= clusters:
        raise ValueError("Cluster count must be at least two and smaller than the player count.")
    matrix = transform_features(features, include_path=include_path)
    scaler = StandardScaler().fit(matrix)
    reference = KMeans(n_clusters=clusters, n_init=20, random_state=seed).fit_predict(
        scaler.transform(matrix))
    rng = np.random.default_rng(seed)
    scores = []
    for repeat in range(repetitions):
        sampled = matrix.iloc[rng.integers(0, len(matrix), len(matrix))]
        boot_scaler = StandardScaler().fit(sampled)
        model = KMeans(n_clusters=clusters, n_init=20, random_state=seed + repeat + 1)
        model.fit(boot_scaler.transform(sampled))
        labels = model.predict(boot_scaler.transform(matrix))
        scores.append(float(adjusted_rand_score(reference, labels)))
    return {"reference": f"kmeans_k{clusters}", "repetitions": repetitions,
            "ari_mean": float(np.mean(scores)), "ari_min": float(np.min(scores)),
            "ari_max": float(np.max(scores)), "ari_values": scores}



def temporal_stability(early, late, seed=42, clusters=3, include_path=True):
    """Compare independent partitions on common players in disjoint windows."""
    common = early.index.intersection(late.index)
    if len(common) <= clusters:
        return {"common_players": len(common), "ari": None}
    labels = []
    for frame in (early, late):
        matrix = StandardScaler().fit_transform(transform_features(frame.loc[common], include_path=include_path))
        labels.append(KMeans(n_clusters=clusters, n_init=20,
                             random_state=seed).fit_predict(matrix))
    return {"common_players": len(common),
            "ari": float(adjusted_rand_score(*labels)),
            "interpretation": "Descriptive temporal consistency, not a prediction score."}



def partition_agreement(reference, alternative):
    """Compare aligned labels, reporting noise-sensitive and jointly assigned ARI."""
    reference, alternative = np.asarray(reference), np.asarray(alternative)
    if reference.shape != alternative.shape or reference.ndim != 1 or len(reference) == 0:
        raise ValueError("Aligned, non-empty one-dimensional labels are required.")
    assigned = (reference != -1) & (alternative != -1)
    meaningful = (assigned.sum() > 2 and np.unique(reference[assigned]).size > 1
                  and np.unique(alternative[assigned]).size > 1)
    return {"ari_including_noise": float(adjusted_rand_score(reference, alternative)),
            "jointly_assigned_fraction": float(assigned.mean()),
            "ari_jointly_assigned": float(adjusted_rand_score(reference[assigned], alternative[assigned]))
            if meaningful else None}


def subsample_stability(features, estimator, seed=42, repetitions=10, fraction=.8, include_path=True):
    """Refit every estimator, including DBSCAN, on common 80% player subsets.

    No DBSCAN prediction on unseen players is invented. Scaling is refitted in
    each subset. Comparisons are on that subset, so this is descriptive stability.
    """
    from sklearn.base import clone
    if not isinstance(repetitions, int) or repetitions < 2 or not 0 < fraction < 1:
        raise ValueError("Use at least two repetitions and a fraction strictly between zero and one.")
    data = transform_features(features, include_path=include_path)
    size = int(len(data) * fraction)
    needed = getattr(estimator, "n_clusters", getattr(estimator, "n_components", 1))
    if size <= needed:
        raise ValueError("The subsample must outnumber the requested clusters/components.")
    reference = clone(estimator).fit_predict(StandardScaler().fit_transform(data))
    rng = np.random.default_rng(seed)
    trials = []
    for _ in range(repetitions):
        indices = np.sort(rng.choice(len(data), size=size, replace=False))
        subset = StandardScaler().fit_transform(data.iloc[indices])
        labels = clone(estimator).fit_predict(subset)
        trials.append(partition_agreement(reference[indices], labels))
    assigned = [row["ari_jointly_assigned"] for row in trials if row["ari_jointly_assigned"] is not None]
    return {"repetitions": repetitions, "subsample_fraction": fraction,
            "ari_including_noise_mean": float(np.mean([row["ari_including_noise"] for row in trials])),
            "jointly_assigned_fraction_mean": float(np.mean([row["jointly_assigned_fraction"] for row in trials])),
            "ari_jointly_assigned_mean": float(np.mean(assigned)) if assigned else None,
            "defined_assigned_trials": len(assigned), "trials": trials}


def temporal_model_stability(early, late, estimator, include_path=True):
    """Compare independently refitted models across two windows on common players."""
    from sklearn.base import clone
    common = early.index.intersection(late.index)
    needed = getattr(estimator, "n_clusters", getattr(estimator, "n_components", 1))
    if len(common) <= needed:
        return {"common_players": len(common), "status": "insufficient_common_players"}
    labels = []
    for frame in (early, late):
        matrix = StandardScaler().fit_transform(transform_features(frame.loc[common], include_path=include_path))
        labels.append(clone(estimator).fit_predict(matrix))
    return {"common_players": len(common), "status": "evaluated",
            **partition_agreement(*labels)}
