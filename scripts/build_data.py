"""Build site/data/progress.json and site/data/functions.json from OpenSHC's public data.

Sources, all public:
- status_rollup.tsv from sourcehold/OpenSHC's latest-sarif release: every function of the game with its best match on
  main or on the branches the project's rollup knows (the same file tools/pick_work.py reads);
- a clone of sourcehold/OpenSHC: main's status/addresses-SHC-3BB0A8C1.txt and its git history, and where each
  function's code is (its reccmp annotation, "// FUNCTION: STRONGHOLDCRUSADER 0x..."), for the map's link to it;
- with --fetch-branches, the branches the rollup names (fetched into refs/progress/ in that clone), for the same link
  to the code of functions that are only on a branch.

progress.json holds the totals, parts of the game, namespaces, history and lists; functions.json holds one row per
function in address order, for the page's map of the executable.

usage: python scripts/build_data.py --openshc PATH [--ref REF] [--out site/data] [--rollup FILE] [--fetch-branches]
"""
import argparse
import collections
import csv
import datetime
import io
import json
import os
import re
import subprocess
import urllib.request

ROLLUP_URL = 'https://github.com/sourcehold/OpenSHC/releases/download/latest-sarif/status_rollup.tsv'
STATUS = 'status/addresses-SHC-3BB0A8C1.txt'
AREA_NAMES = {
    'Map': 'Map: units, buildings, terrain', 'UI': 'Menus and interface', 'Global': 'Start-up and globals',
    'AI': 'Computer players (AI)', 'Synchrony': 'Multiplayer sync', 'Meta': 'Engine helpers', 'Game': 'Game rules',
    'Text': 'Text', 'Audio': 'Sound', 'IO': 'Files and saves', 'Rendering': 'Rendering', 'OS': 'Windows layer',
    'Input': 'Mouse and keyboard', 'Util': 'Utilities', 'Random': 'Random numbers',
}
BANDS = ['95 to 99.9%', '90 to 95%', '75 to 90%', '50 to 75%', '25 to 50%', 'under 25%', 'not started']
STATES = ['on_main', 'branch_100', 'in_progress', 'not_started']
ANNOTATION = r'// *(FUNCTION|STUB): *STRONGHOLDCRUSADER 0x[0-9a-fA-F]+'
BRANCH = re.compile(r'^(.+?)-OpenSHC/(.+)$')  # the rollup's "<owner>-OpenSHC/<branch>", as the page reads it


def git(repo, *args):
    r = subprocess.run(['git', '-C', repo, *args], capture_output=True, text=True, encoding='utf-8', errors='replace')
    if r.returncode:
        raise SystemExit('git ' + ' '.join(args[:3]) + ': ' + r.stderr[:300])
    return r.stdout


def http_get(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'openshc-progress'})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read().decode('utf-8')


def addr_of(text):
    return text.strip().lower().split('0x')[-1].lstrip('0') or '0'


def code_in(repo, ref):
    """address -> (file, line) of each function's annotation under src/ at ref"""
    r = subprocess.run(['git', '-C', repo, 'grep', '-n', '-I', '-E', ANNOTATION, ref, '--', 'src'],
                       capture_output=True, text=True, encoding='utf-8', errors='replace')
    if r.returncode > 1:
        raise SystemExit('git grep ' + ref + ': ' + r.stderr[:300])
    found = {}
    for line in r.stdout.splitlines():
        _, path, num, text = line.split(':', 3)
        found.setdefault(addr_of(re.search(r'0x[0-9a-fA-F]+', text).group(0)), (path, int(num)))
    return found


def fetch_branches(repo, sources):
    """fetch the rollup's branches that still exist into refs/progress/; returns source -> ref"""
    by_owner = collections.defaultdict(list)
    for s in sources:
        m = BRANCH.match(s)
        if m:
            by_owner[m.group(1)].append((s, m.group(2)))
    refs = {}
    for owner, items in sorted(by_owner.items()):
        url = 'https://github.com/' + owner + '/OpenSHC.git'
        r = subprocess.run(['git', 'ls-remote', '--heads', url], capture_output=True, text=True)
        heads = {line.split('refs/heads/', 1)[1] for line in r.stdout.splitlines() if 'refs/heads/' in line}
        mine = {s: 'refs/progress/' + owner + '/' + b for s, b in items if b in heads}
        specs = ['+refs/heads/' + b + ':' + mine[s] for s, b in items if s in mine]
        if specs and subprocess.run(['git', '-C', repo, 'fetch', '--quiet', '--no-tags', url, *specs]).returncode == 0:
            refs.update(mine)
        else:
            print('no code links for', owner + "'s branches")
    return refs


def area_of(cpp):
    parts = cpp.replace(chr(92), '/').split('/')
    return parts[2] if len(parts) > 3 and parts[0] == 'src' else None


def namespace_of(cpp):
    parts = cpp.replace(chr(92), '/').split('/')[2:-1]
    return '::'.join(parts)


def band_of(pct):
    if pct <= 0:
        return 'not started'
    for low, name in ((95, '95 to 99.9%'), (90, '90 to 95%'), (75, '75 to 90%'), (50, '50 to 75%'), (25, '25 to 50%')):
        if pct >= low:
            return name
    return 'under 25%'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--openshc', required=True, help='a clone of sourcehold/OpenSHC with main checked out or fetched')
    ap.add_argument('--ref', default='HEAD')
    ap.add_argument('--out', default='site/data')
    ap.add_argument('--rollup', help='a local status_rollup.tsv instead of the release asset')
    ap.add_argument('--fetch-branches', action='store_true',
                    help="fetch the rollup's branches into the clone, to link to the code of functions only on a branch")
    a = ap.parse_args()

    rollup_text = open(a.rollup, encoding='utf-8').read() if a.rollup else http_get(ROLLUP_URL)
    rollup = [r for r in csv.DictReader(io.StringIO(rollup_text), delimiter='\t') if area_of(r['expected_cpp'] or '')]

    # main's status list now
    main100 = set()
    for line in git(a.openshc, 'show', a.ref + ':' + STATUS).splitlines():
        cols = line.split('|')
        if len(cols) >= 2 and cols[1].strip() == '100.0%':
            main100.add(addr_of(cols[0]))

    # main's history: the 100% count after each day, counting only the functions the rollup lists (as the totals do)
    known = {addr_of(r['address']) for r in rollup}
    log = git(a.openshc, 'log', '--first-parent', '--reverse', '-p', '--unified=0', '--format=@@C %cI', a.ref,
              '--', STATUS)
    count, days, day = 0, collections.OrderedDict(), None
    for line in log.splitlines():
        if line.startswith('@@C '):
            day = datetime.datetime.fromisoformat(line[4:].strip()).astimezone(datetime.timezone.utc).date().isoformat()
            continue
        if line[:3] in ('+++', '---') or line[:1] not in '+-':
            continue
        cols = line[1:].split('|')
        if len(cols) < 2 or cols[1].strip() != '100.0%' or addr_of(cols[0]) not in known:
            continue
        if line[0] == '+':
            count += 1
        else:
            count -= 1
        days[day] = count
    history = [{'date': d, 'on_main': c} for d, c in days.items()]

    # every function of the game, from the rollup
    areas, namespaces = collections.OrderedDict(), {}
    bands = collections.Counter()
    almost, waiting_by = [], collections.Counter()
    fn_rows = []
    for r in rollup:
        addr = addr_of(r['address'])
        pct = float(r['best_pct'] or 0)
        state = ('on_main' if addr in main100 else 'branch_100' if pct >= 100 else
                 'in_progress' if pct > 0 else 'not_started')
        key = area_of(r['expected_cpp'])
        fn_rows.append((int(addr, 16), key, namespace_of(r['expected_cpp']),
                        os.path.splitext(os.path.basename(r['expected_cpp']))[0], pct, state,
                        r['best_source'] if state in ('branch_100', 'in_progress') else ''))
        for table, k, extra in ((areas, key, {'key': key, 'area': AREA_NAMES.get(key, key)}),
                                (namespaces, namespace_of(r['expected_cpp']), {'namespace': namespace_of(r['expected_cpp'])})):
            row = table.setdefault(k, dict(extra, on_main=0, branch_100=0, in_progress=0, not_started=0, total=0))
            row[state] += 1
            row['total'] += 1
        if state in ('in_progress', 'not_started'):
            bands[band_of(pct)] += 1
        if state == 'in_progress' and pct >= 95:
            almost.append({'function': os.path.splitext(os.path.basename(r['expected_cpp']))[0],
                           'namespace': namespace_of(r['expected_cpp']), 'address': r['address'],
                           'best_pct': pct, 'where': r['best_source']})
        if state == 'branch_100':
            waiting_by[r['best_source']] += 1

    total = len(rollup)
    on_main = sum(1 for r in rollup if addr_of(r['address']) in main100)
    week_ago = (datetime.date.fromisoformat(history[-1]['date']) - datetime.timedelta(days=7)).isoformat()
    then = next((h['on_main'] for h in reversed(history) if h['date'] <= week_ago), 0)
    data = {
        'generated_at': datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat(),
        'main_commit': git(a.openshc, 'rev-parse', '--short=9', a.ref).strip(),
        'totals': {
            'total': total, 'on_main': on_main,
            'branch_100': sum(r['branch_100'] for r in areas.values()),
            'in_progress': sum(r['in_progress'] for r in areas.values()),
            'not_started': sum(r['not_started'] for r in areas.values()),
            'on_main_week_ago': then, 'week_ago': week_ago,
        },
        'areas': sorted(areas.values(), key=lambda r: -r['total']),
        'namespaces': sorted((r for r in namespaces.values() if r['total'] - r['on_main'] > 0),
                             key=lambda r: -(r['total'] - r['on_main'])),
        'history': history,
        'bands': [{'band': b, 'count': bands[b]} for b in BANDS],
        'almost': sorted(almost, key=lambda r: -r['best_pct']),
        'waiting': [{'where': k, 'functions': v} for k, v in waiting_by.most_common(12)],
    }
    # one row per function, in address order: [address, area, namespace, name, best % x10, state, source]
    # area, namespace, state and source are indexes into the lists next to the rows, to keep the file small
    fn_rows.sort()
    # where each function's code is, in its best source: main's file, or the branch's
    code = {'main': code_in(a.openshc, a.ref)}
    if a.fetch_branches:
        for s, ref in fetch_branches(a.openshc, {row[6] for row in fn_rows if row[6] not in ('', 'main')}).items():
            code[s] = code_in(a.openshc, ref)

    def code_of(addr, ns, name, src):
        at = code.get(src or 'main', {}).get(addr_of(hex(addr)))
        if not at:
            return 0
        # the page builds the usual path from the namespace and the name; spell out only a file somewhere else
        return at[1] if at[0] == 'src/OpenSHC/' + ns.replace('::', '/') + '/' + name + '.cpp' else list(at)

    area_keys = [r['key'] for r in data['areas']]
    ns_list = sorted({row[2] for row in fn_rows})
    src_list = sorted({row[6] for row in fn_rows if row[6]})
    ns_ix = {n: i for i, n in enumerate(ns_list)}
    src_ix = {s: i for i, s in enumerate(src_list)}
    functions = {
        'generated_at': data['generated_at'],
        # code: the line of the function's annotation in src/OpenSHC/<namespace>/<name>.cpp, or [file, line] for a
        # file elsewhere, or 0 when there is none; in main's code, or the source branch's for a function not on main
        'columns': ['address', 'area', 'namespace', 'name', 'best_pct_x10', 'state', 'source', 'code'],
        'states': STATES, 'areas': area_keys, 'namespaces': ns_list, 'sources': src_list,
        'rows': [[addr, area_keys.index(area), ns_ix[ns], name, int(round(pct * 10)), STATES.index(state),
                  src_ix[src] if src else -1, code_of(addr, ns, name, src)]
                 for addr, area, ns, name, pct, state, src in fn_rows],
    }

    os.makedirs(a.out, exist_ok=True)
    json.dump(data, open(os.path.join(a.out, 'progress.json'), 'w', encoding='utf-8', newline='\n'),
              ensure_ascii=False, indent=1)
    with open(os.path.join(a.out, 'functions.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(functions, f, ensure_ascii=False, separators=(',', ':'))
    t = data['totals']
    print('functions %d, on main %d (%.1f%%), 100%% on a branch %d, in progress %d, not started %d; history %d days'
          % (total, on_main, 100.0 * on_main / total, t['branch_100'], t['in_progress'], t['not_started'], len(history)))
    print('code found for %d functions' % sum(1 for row in functions['rows'] if row[7]))


if __name__ == '__main__':
    main()
