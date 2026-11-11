# OpenSHC progress

How far [OpenSHC](https://github.com/sourcehold/OpenSHC), the community reimplementation of the classic game
Stronghold Crusader, has come: **https://kotijekriv.github.io/openshc-progress/**

The page shows how many of the game's functions are done on main, how many already match 100% on a branch and wait to
land, which parts of the game have the most left, how close the unfinished ones are, and which functions are one small
fix away from a full match.

An unofficial page by a contributor. Not affiliated with Firefly Studios.

## Where the numbers come from

All public, nothing else:

- `status_rollup.tsv` from OpenSHC's `latest-sarif` release: every function of the game and its best match on main
  or on the branches the project tracks (the file `tools/pick_work.py` reads). Forks it doesn't track can hold more
  finished work than the page shows.
- OpenSHC's main branch: `status/addresses-SHC-3BB0A8C1.txt` and its git history, for what is on main now and
  how that grew.

## How it updates

`.github/workflows/pages.yml` runs every day at 05:17 UTC, on every push, and from the Actions tab
("Run workflow"). It clones OpenSHC, runs `scripts/build_data.py` (writes `site/data/progress.json`) and
`scripts/make_card.py` (draws `site/card.png`, the preview image for links on X and elsewhere), and publishes
`site/` to GitHub Pages.

GitHub pauses scheduled workflows in a repository with no activity for 60 days; a push or a manual run restarts them.

## Run it locally

```bash
git clone https://github.com/sourcehold/OpenSHC.git ../OpenSHC
python scripts/build_data.py --openshc ../OpenSHC --out site/data
pip install matplotlib && python scripts/make_card.py
python -m http.server 8000 --directory site
```

Then open http://localhost:8000.
