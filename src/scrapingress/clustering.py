"""Configurable candidate comparison, with GMM convergence and information criteria."""
from dataclasses import dataclass
import warnings
import numpy as np
from sklearn.cluster import DBSCAN, KMeans
from sklearn.exceptions import ConvergenceWarning
from sklearn.mixture import GaussianMixture
from sklearn.preprocessing import StandardScaler, RobustScaler
from .features import transform_features
from .evaluation import partition_metrics


@dataclass(frozen=True)
class ModelGrid:
    clusters: tuple = (2, 3, 4, 5)
    dbscan_eps: tuple = (.8, 1.2, 1.8, 2.4)
    min_samples: int = 5

    def __post_init__(self):
        if not self.clusters or len(set(self.clusters)) != len(self.clusters):
            raise ValueError("Provide a non-empty, unique cluster-count grid.")
        if any(isinstance(k, bool) or not isinstance(k, int) or k < 2 for k in self.clusters):
            raise ValueError("Cluster counts must be integers >= 2.")
        if not self.dbscan_eps or len(set(self.dbscan_eps)) != len(self.dbscan_eps):
            raise ValueError("Provide a non-empty, unique DBSCAN radius grid.")
        if any(not np.isfinite(eps) or eps <= 0 for eps in self.dbscan_eps):
            raise ValueError("DBSCAN radii must be finite and positive.")
        if isinstance(self.min_samples, bool) or not isinstance(self.min_samples, int) or self.min_samples < 2:
            raise ValueError("min_samples must be an integer >= 2.")


def candidate_models(seed, grid=None):
    grid = grid or ModelGrid()
    for k in grid.clusters:
        yield f"kmeans_k{k}", KMeans(n_clusters=k, n_init=20, random_state=seed)
        yield f"gmm_k{k}", GaussianMixture(n_components=k, n_init=3,
                                          reg_covar=1e-5, random_state=seed)
    for eps in grid.dbscan_eps:
        yield f"dbscan_eps{eps}", DBSCAN(eps=eps, min_samples=grid.min_samples)


def compare_models(features, seed=42, grid=None, scaling="standard", include_path=True):
    grid = grid or ModelGrid()
    if scaling not in {"standard", "robust"}:
        raise ValueError("scaling must be standard or robust.")
    scaler = StandardScaler() if scaling == "standard" else RobustScaler()
    matrix = scaler.fit_transform(transform_features(features, include_path=include_path))
    if len(matrix) <= max(grid.clusters):
        raise ValueError("Eligible players must outnumber the largest cluster count.")
    results, assignments = [], {}
    for name, model in candidate_models(seed, grid):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always", ConvergenceWarning)
            labels = model.fit_predict(matrix)
        row = {"model": name, **partition_metrics(matrix, labels),
               "convergence_warning": any(issubclass(w.category, ConvergenceWarning) for w in caught)}
        if isinstance(model, GaussianMixture):
            row.update(bic=float(model.bic(matrix)), aic=float(model.aic(matrix)),
                       converged=bool(model.converged_))
        results.append(row)
        assignments[name] = labels
    return matrix, results, assignments
