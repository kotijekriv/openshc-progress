"""Draw site/card.png (1200 x 630), the preview image X and other sites show for a link to the page.

It matches the page: the share on main in IBM Plex, and the map of every function of the game in address order,
coloured by where it stands. Dark, so it stands out in both of X's themes.

usage: python scripts/make_card.py [--data site/data] [--out site/card.png]
"""
import argparse
import datetime
import json
import os

import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.collections import PatchCollection  # noqa: E402
from matplotlib.font_manager import FontProperties  # noqa: E402
from matplotlib.patches import FancyBboxPatch, Rectangle  # noqa: E402

FONTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fonts')
SANS = FontProperties(fname=os.path.join(FONTS, 'IBMPlexSans-Regular.ttf'))
SANS_MED = FontProperties(fname=os.path.join(FONTS, 'IBMPlexSans-Medium.ttf'))
MONO = FontProperties(fname=os.path.join(FONTS, 'IBMPlexMono-Regular.ttf'))
MONO_MED = FontProperties(fname=os.path.join(FONTS, 'IBMPlexMono-Medium.ttf'))

# the page's dark theme
BG, INK, INK2, INK3, RULE = '#0f0f0e', '#f1efe9', '#b6b2a8', '#8a867d', '#252422'
STATE = ['#f5a83c', '#9a6a22', '#3b3a36', '#5a5751']  # on main, 100% on a branch, in progress, not started (outline)
W, H = 1200, 630


def text_width(fig, txt):
    return txt.get_window_extent(fig.canvas.get_renderer()).width  # 1 data unit is 1 pixel here


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--data', default='site/data')
    ap.add_argument('--out', default='site/card.png')
    a = ap.parse_args()
    d = json.load(open(os.path.join(a.data, 'progress.json'), encoding='utf-8'))
    rows = json.load(open(os.path.join(a.data, 'functions.json'), encoding='utf-8'))['rows']
    t = d['totals']
    gain = t['on_main'] - t['on_main_week_ago']

    fig = plt.figure(figsize=(W / 100, H / 100), dpi=100, facecolor=BG)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, W)
    ax.set_ylim(H, 0)
    ax.axis('off')

    # left: what it is and how far it has come
    x0 = 64
    ax.text(x0, 78, 'OPENSHC  ·  MATCHING DECOMPILATION', fontproperties=MONO, fontsize=12.5, color=INK2, va='baseline')
    ax.text(x0, 132, 'Stronghold Crusader, rewritten in', fontproperties=SANS_MED, fontsize=22, color=INK,
            va='baseline')
    ax.text(x0, 164, 'C++ one function at a time.', fontproperties=SANS_MED, fontsize=22, color=INK, va='baseline')

    pct = '%.1f' % (100.0 * t['on_main'] / t['total'])
    big = ax.text(x0 - 6, 368, pct, fontproperties=SANS_MED, fontsize=120, color=INK, va='baseline')
    ax.text(x0 - 6 + text_width(fig, big) + 6, 368, '%', fontproperties=SANS, fontsize=120, color=INK3,
            va='baseline')

    # the meter under the number: on main, then 100% on a branch, on a track
    mw, my = 452, 400
    track = FancyBboxPatch((x0, my), mw, 8, boxstyle='round,pad=0,rounding_size=4', facecolor=RULE, edgecolor='none')
    ax.add_patch(track)
    wm = mw * t['on_main'] / t['total']
    wb = mw * t['branch_100'] / t['total']
    for bar in (Rectangle((x0, my), wm, 8, facecolor=STATE[0], edgecolor='none'),
                Rectangle((x0 + wm + 2, my), max(wb - 2, 1), 8, facecolor=STATE[1], edgecolor='none')):
        ax.add_patch(bar)
        bar.set_clip_path(track)

    def line(y, parts):
        x = x0
        for s, prop, color in parts:
            txt = ax.text(x, y, s, fontproperties=prop, fontsize=14.5, color=color, va='baseline')
            x += text_width(fig, txt)

    line(448, [(format(t['on_main'], ','), MONO_MED, INK), (' of ', MONO, INK2), (format(t['total'], ','), MONO_MED, INK),
               (' functions on main', MONO, INK2)])
    line(474, [(('+' if gain >= 0 else '') + format(gain, ','), MONO_MED, INK), (' in the last 7 days', MONO, INK2)])
    line(500, [(format(t['branch_100'], ','), MONO_MED, INK), (' more at 100% on branches', MONO, INK2)])

    ax.text(x0, 574, 'kotijekriv.github.io/openshc-progress', fontproperties=MONO, fontsize=12.5, color=INK3,
            va='baseline')

    # right: the whole game, one cell per function, in address order
    cols, pitch, size = 64, 8, 6.5
    mx0 = W - 64 - cols * pitch + (pitch - size)
    nrows = -(-len(rows) // cols)
    my0 = (H - nrows * pitch) / 2
    filled = {0: [], 1: [], 2: []}
    hollow = []
    for i, r in enumerate(rows):
        x, y = mx0 + (i % cols) * pitch, my0 + (i // cols) * pitch
        if r[5] == 3:
            hollow.append(Rectangle((x + 0.5, y + 0.5), size - 1, size - 1))
        else:
            filled[r[5]].append(FancyBboxPatch((x, y), size, size, boxstyle='round,pad=0,rounding_size=1.2'))
    for st, patches in filled.items():
        ax.add_collection(PatchCollection(patches, facecolor=STATE[st], edgecolor='none'))
    ax.add_collection(PatchCollection(hollow, facecolor='none', edgecolor=STATE[3], linewidth=1))
    day = datetime.date.fromisoformat(d['generated_at'][:10])
    ax.text(W - 64, 574, 'updated {:%b} {}, {}'.format(day, day.day, day.year), fontproperties=MONO, fontsize=12.5,
            color=INK3, ha='right', va='baseline')

    fig.savefig(a.out, dpi=100, facecolor=BG)
    print('wrote', a.out)


if __name__ == '__main__':
    main()
