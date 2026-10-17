"""Plot published group medians only; no player-level file is read."""
import argparse
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def plot(summary, destination):
    report = json.loads(Path(summary).read_text())
    profiles = sorted(report['cluster_profiles']['kmeans_k2'],
                      key=lambda row: row['medians']['events_per_active_day'])
    plt.rcParams['svg.hashsalt'] = 'scrapingress-aggregate-profiles-v1'
    fig, axes = plt.subplots(2, 2, figsize=(10, 7))
    panels = [('active_day_fraction', 'Observed active dates (%)', 100),
              ('events_per_active_day', 'Events per active day', 1),
              ('sites_per_active_day', 'Distinct event sites per active day', 1),
              ('median_session_minutes', 'Median observed session span (minutes)', 1)]
    labels = ['Lower observed activity', 'Higher observed activity']
    for ax, (feature, title, scale) in zip(axes.flat, panels):
        values = [row['medians'][feature] * scale for row in profiles]
        bars = ax.bar(labels, values, color=['#466b8b', '#b47735'], width=.6)
        ax.set_title(title, fontsize=11)
        ax.spines[['top', 'right']].set_visible(False)
        ax.set_ylim(0, max(values) * 1.25)
        ax.bar_label(bars, labels=[f'{value:.1f}' for value in values], padding=3)
        ax.tick_params(axis='x', labelsize=9)
    counts = ' and '.join(str(row['players']) for row in profiles)
    fig.suptitle(f'Real-event reanalysis · K-means baseline, k=2\nMedians of player-level features; {counts} players', fontsize=14)
    fig.text(.5, .01, 'Aggregate statistics only · observed game activity is not verified physical mobility', ha='center', fontsize=9)
    fig.tight_layout(rect=(0, .04, 1, .91))
    fig.savefig(destination, metadata={'Date': None}, bbox_inches='tight')
    plt.close(fig)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--summary', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    plot(args.summary, args.output)
