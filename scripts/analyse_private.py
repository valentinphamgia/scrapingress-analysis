"""Run local analysis of pseudonymised events; output is private, not a public API."""
import argparse
from pathlib import Path
import pandas as pd
from scrapingress.private_data import load_private_events
from scrapingress.experiment import ExperimentConfig, analyse_events
from scrapingress.reporting import PRIVATE_NOTICE


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--repetitions", type=int, default=10)
    parser.add_argument("--sensitivity", action="store_true")
    args = parser.parse_args()
    events, quality = load_private_events(args.database)
    start = events.timestamp.min().floor("D")
    end = events.timestamp.max().floor("D") + pd.Timedelta(days=1)
    config = ExperimentConfig(repetitions=args.repetitions, sensitivity=args.sensitivity)
    print(PRIVATE_NOTICE)
    report = analyse_events(events, start, end, config, args.output,
                            synthetic=False, quality=quality)
    print(f"Local private analysis complete: {report['eligible_players']} eligible activity profiles.")
    print(f"Incomplete rows excluded from analysis (preserved in database): {quality['excluded_incomplete_rows']}")


if __name__ == "__main__":
    main()
