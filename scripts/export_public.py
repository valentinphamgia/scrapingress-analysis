"""Build an explicit-allowlist source archive, never a recursive folder export."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
FILES = [
    ".gitignore", "README.md", "pyproject.toml", "requirements-lock.txt",
    "data/README.md", "data/synthetic/README.md", "reports/README.md", "reports/CONCLUSIONS.md", "reports/aggregate_metrics.json", "reports/cluster_profiles.svg",
    "docs/PROVENANCE.md", "docs/ROADMAP.md", "docs/RESEARCH_NOTES.md",
    "docs/FUNCTIONS.md", "docs/PRIVATE_DATA.md", "DATA_NOTICE.md",
    "src/scrapingress/__init__.py", "src/scrapingress/synthetic.py",
    "src/scrapingress/features.py", "src/scrapingress/clustering.py",
    "src/scrapingress/experiment.py", "src/scrapingress/geometry.py",
    "src/scrapingress/validation.py", "src/scrapingress/sessions.py",
    "src/scrapingress/evaluation.py", "src/scrapingress/plotting.py",
    "src/scrapingress/reporting.py", "src/scrapingress/sensitivity.py", "src/scrapingress/private_data.py", "tests/test_core.py", "tests/test_aggregate_report.py", "tests/test_regressions.py", "tests/test_private_data.py", "tests/test_export.py", "scripts/export_public.py", "scripts/build_aggregate_report.py", "scripts/plot_aggregate_profiles.py", "scripts/pseudonymize_database.py", "scripts/analyse_private.py",
]


def export(destination):
    destination = Path(destination).resolve()
    if destination in [(ROOT / name).resolve() for name in FILES]:
        raise ValueError("The destination cannot overwrite a source file.")
    payload = {}
    for name in FILES:
        source = ROOT / name
        if source.is_symlink() or not source.is_file():
            raise ValueError(f"Missing or symbolic-link source: {name}")
        payload[name] = source.read_bytes()
    manifest = {name: hashlib.sha256(data).hexdigest() for name, data in payload.items()}
    # Exclusive creation avoids overwriting a pre-existing archive.
    with zipfile.ZipFile(destination, mode="x", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, data in payload.items():
            archive.writestr("scrapingress-public/" + name, data)
        archive.writestr("scrapingress-public/SHA256SUMS.json",
                         json.dumps(manifest, indent=2) + "\n")
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    manifest = export(args.destination)
    print(f"Exported {len(manifest)} explicitly selected source files: {args.destination}")
