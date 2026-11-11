"""Draw site/card.png (1200 x 630), the preview image X and other sites show for a link to the page.

usage: python scripts/make_card.py [--data site/data/progress.json] [--out site/card.png]
"""
import argparse
import datetime
import json

import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyBboxPatch  # noqa: E402

SURFACE, TEXT, TEXT2, GRID = '#fcfcfb', '#0b0b0b', '#52514e', '#e1e0d9'
MAIN, BRANCH, PROGRESS, NONE = '#2a78d6', '#eb6834', '#1baf7a', '#d6d4cc'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--data', default='site/data/progress.json')
    ap.add_argument('--out', default='site/card.png')
    a = ap.parse_args()
    d = json.load(open(a.data, encoding='utf-8'))
    t = d['totals']
    pct = 100.0 * t['on_main'] / t['total']
    gain = t['on_main'] - t['on_main_week_ago']

    fig = plt.figure(figsize=(12, 6.3), dpi=100, facecolor=SURFACE)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1200)
    ax.set_ylim(630, 0)
    ax.axis('off')
    ax.text(60, 70, 'OpenSHC progress', fontsize=26, fontweight='bold', color=TEXT, va='center')
    ax.text(60, 112, 'The community rewrite of Stronghold Crusader, one function at a time', fontsize=14, color=TEXT2,
            va='center')
    ax.text(60, 205, '%.1f%%' % pct, fontsize=64, fontweight='bold', color=TEXT, va='center')
    ax.text(60, 268, '%s of %s functions done on main' % (format(t['on_main'], ','), format(t['total'], ',')),
            fontsize=18, color=TEXT, va='center')
    ax.text(60, 302, '%s%s in the last 7 days' % ('+' if gain >= 0 else '', format(gain, ',')), fontsize=16,
            color=MAIN, fontweight='bold', va='center')

    # one bar of where all functions stand
    x0, width, y0, h = 60, 1080, 360, 34
    parts = [(t['on_main'], MAIN, 'Done on main'), (t['branch_100'], BRANCH, '100% on a branch'),
             (t['in_progress'], PROGRESS, 'In progress'), (t['not_started'], NONE, 'Not started')]
    x = x0
    for i, (v, color, _) in enumerate(parts):
        w = width * v / t['total']
        ax.add_patch(FancyBboxPatch((x + 1, y0), max(w - 2, 1), h, boxstyle='round,pad=0,rounding_size=4',
                                    facecolor=color, edgecolor='none'))
        x += w
    lx = x0
    renderer = fig.canvas.get_renderer()
    for v, color, label in parts:
        ax.add_patch(FancyBboxPatch((lx, y0 + h + 22), 14, 14, boxstyle='round,pad=0,rounding_size=3', facecolor=color,
                                    edgecolor='none'))
        txt = ax.text(lx + 22, y0 + h + 29, '%s %s' % (label, format(v, ',')), fontsize=13, color=TEXT2, va='center')
        lx += 22 + txt.get_window_extent(renderer).width + 30  # 1 data unit is 1 pixel here

    # main over time, small
    hist = d['history']
    days = [datetime.date.fromisoformat(r['date']) for r in hist]
    vals = [r['on_main'] for r in hist]
    sub = fig.add_axes([60 / 1200, 30 / 630, 1080 / 1200, 140 / 630], facecolor=SURFACE)
    sub.step(days, vals, where='post', color=MAIN, linewidth=2)
    sub.fill_between(days, vals, step='post', color=MAIN, alpha=0.15, linewidth=0)
    sub.set_ylim(0, max(vals) * 1.08)
    for s in ('top', 'right', 'left'):
        sub.spines[s].set_visible(False)
    sub.spines['bottom'].set_color(GRID)
    sub.tick_params(axis='both', colors=TEXT2, labelsize=10, length=0)
    sub.set_yticks([])
    sub.xaxis.set_major_formatter(matplotlib.dates.DateFormatter('%b'))
    sub.xaxis.set_major_locator(matplotlib.dates.MonthLocator())
    ax.text(1140, 205, 'updated %s' % d['generated_at'][:10], fontsize=13, color=TEXT2, ha='right', va='center')
    ax.text(1140, 232, 'kotijekriv.github.io/openshc-progress', fontsize=13, color=TEXT2, ha='right', va='center')
    fig.savefig(a.out, dpi=100, facecolor=SURFACE)
    print('wrote', a.out)


if __name__ == '__main__':
    main()
