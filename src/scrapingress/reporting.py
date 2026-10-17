"""Export experiment results; no original observations are loaded or copied."""
import json
from pathlib import Path
import pandas as pd

DATA_NOTICE = (
    "SYNTHETIC DATA ONLY: all players, sites and observations are fictional. "
    "No original records or real-data-fitted parameters are used. "
    "Results demonstrate methods, not actual Ingress player behaviour."
)


PRIVATE_NOTICE = (
    "PRIVATE PSEUDONYMISED DATA: identifiers have changed but timestamps and "
    "coordinates are retained. This is not anonymous data. Keep these outputs private. "
    "Activity is measured from game events; event sites are not verified player positions."
)


def save_results(features, labels, report, output):
    """Write metrics and synthetic feature summaries to an output directory."""
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    synthetic = report["data_kind"] == "synthetic"
    prefix = "synthetic" if synthetic else "private"
    if not synthetic:
        import os
        os.chmod(output, 0o700)
    (output / "DATA_NOTICE.txt").write_text(report["data_notice"] + "\n")
    (output / "metrics.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    features.to_csv(output / f"{prefix}_features.csv")
    assignments = pd.DataFrame(labels, index=features.index)
    assignments.to_csv(output / f"{prefix}_assignments.csv")
    features.groupby(assignments[report["reference_model"]]).median().to_csv(
        output / f"{prefix}_cluster_medians.csv")
