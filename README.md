# OpenSHC progress

How far [OpenSHC](https://github.com/sourcehold/OpenSHC), the community's matching decompilation of the classic game
Stronghold Crusader, has come: **https://kotijekriv.github.io/openshc-progress/**

OpenSHC rewrites the game in C++ one function at a time, until Microsoft Visual C++ 2005 compiles each one to the same
machine code as the game's 1.41 executable. The page shows:

- the share of the functions OpenSHC has mapped so far that are done on main, how many more already match 100% on a
  branch, and the last 7 days;
- **a map of every function mapped so far**: one cell per function, 3,703 of them, in the order they sit in the
  executable, coloured by where each stands. Clicking or tapping a cell opens a card next to it with the function's name, its best match, the
  branch holding it and a link to its code on GitHub (on main, or on that branch), with buttons to step to the
  previous and next function; on a phone a finger sliding along a row moves the selection. The map can be regrouped
  by part of the game (animated), searched by name, namespace or address (Enter steps through the matches), walked
  with the arrow keys, and linked to: `?fn=0x0053BC20` selects a function, `?view=parts` opens the grouped view;
- functions on main over time, against the goal of every mapped function, with what is waiting on branches on top;
- how a function gets to 100% (Ghidra, C++, MSVC 2005 SP1, reccmp, the DLL), and what the last few percent are;
- the unfinished functions closest to 100%, how close the rest are, and the branches holding finished work.

An unofficial page by a contributor. Not affiliated with Firefly Studios. No per-contributor counts: the page counts
the community's work as a whole.

## Where the numbers come from

All public, nothing else:

- `status_rollup.tsv` from OpenSHC's `latest-sarif` release: every function OpenSHC has mapped so far (declared at its
  address, with a resolver) and its best match on main or on the branches the project tracks (the file
  `tools/pick_work.py` reads). Forks it doesn't track can hold more finished work than the page shows. That list isn't
  the whole game yet: Ghidra finds about 4,570 functions in the 1.41 executable, so about 860 aren't on it, and every
  percentage on the page is of the mapped ones.
- OpenSHC's main branch: `status/addresses-SHC-3BB0A8C1.txt` and its git history, for what is on main now and
  how that grew.
- For the map's links to the code: each function's reccmp annotation (`// FUNCTION: STRONGHOLDCRUSADER 0x…`) on
  main, and, with `--fetch-branches`, on the branches the rollup names. The script fetches those into
  `refs/progress/` in the OpenSHC clone, so point it at a clone of its own.

`scripts/build_data.py` (Python standard library only) turns them into `site/data/progress.json` (totals, parts of the
game, namespaces, history, lists) and `site/data/functions.json` (one row per function in address order, for the map).
Both are published with the page.

## The page

`site/index.html` is one static file: plain HTML, CSS and JavaScript, no build step and no libraries. The map is drawn
on a canvas, the history chart as hand-written SVG. The only outside requests are IBM Plex Sans and IBM Plex Mono from
jsDelivr (`@fontsource`, pinned versions). Light and dark follow the system; the button in the top bar overrides it and
remembers the choice.

The function states are one hue: two lit steps for on main and 100% on a branch, an unlit track for in progress, and an
outline for not started.

## The preview card

`scripts/make_card.py` draws `site/card.png` (1200 x 630), the image X and other sites show for a link to the page:
the share on main and the map of every function, in the page's dark theme. It uses matplotlib and the IBM Plex fonts in
`scripts/fonts` (SIL Open Font License, see `scripts/fonts/LICENSE.txt`).

## How it updates

`.github/workflows/pages.yml` runs every day at 05:17 UTC, on every push to main, and from the Actions tab
("Run workflow"). It clones OpenSHC, runs `scripts/build_data.py` and `scripts/make_card.py`, and publishes `site/` to
GitHub Pages. A push to main publishes the site.

GitHub pauses scheduled workflows in a repository with no activity for 60 days; a push or a manual run restarts them.

## Run it locally

```bash
git clone --single-branch --branch main https://github.com/sourcehold/OpenSHC.git ../openshc-for-progress
python scripts/build_data.py --openshc ../openshc-for-progress --out site/data --fetch-branches
pip install matplotlib==3.9.2 && python scripts/make_card.py
python -m http.server 8000 --directory site
```

Then open http://localhost:8000.
