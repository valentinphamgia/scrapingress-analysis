"""Synthetic-only PCA visualisation, separate from model fitting."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA


def plot_clusters(matrix, labels, destination, title="Synthetic players · illustrative clustering"):
    """Save a two-component PCA view; PCA is not a clustering preprocessing step."""
    pca = PCA(n_components=2).fit(matrix)
    coordinates = pca.transform(matrix)
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.scatter(*coordinates.T, c=labels, cmap="viridis", s=25)
    ax.set(xlabel="Principal component 1", ylabel="Principal component 2",
           title=title)
    ax.text(.01, -.18, f"PCA is a visualisation only · explained variance: {pca.explained_variance_ratio_.sum():.1%}",
            transform=ax.transAxes, fontsize=9)
    fig.tight_layout()
    fig.savefig(destination, dpi=150, bbox_inches="tight")
    plt.close(fig)
