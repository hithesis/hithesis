"""Validate placeholder dates and stage traceable daily version/date metadata."""
import argparse
from collections import Counter
from datetime import datetime
import importlib.util
import json
import os
from pathlib import Path
import re
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('dev_release', ROOT / 'scripts/dev-release.py')
release = importlib.util.module_from_spec(spec)
spec.loader.exec_module(release)
spec = importlib.util.spec_from_file_location('dev_version', ROOT / 'scripts/dev-version.py')
versions = importlib.util.module_from_spec(spec)
spec.loader.exec_module(versions)
ZERO = '0000/00/00'


def spans(source):
    """Keep raw source offsets, including multiline dtx comment prefixes."""
    def skip(at):
        while at < len(source):
            if source[at].isspace():
                at += 1
            elif source[at] == '%':
                at += 1
            else:
                break
        return at
    def group(at):
        at = skip(at)
        if at >= len(source) or source[at] != '{':
            raise ValueError('Malformed changes argument')
        begin, depth = at + 1, 1
        at += 1
        while depth:
            if at >= len(source):
                raise ValueError('Unclosed changes argument')
            if source[at] == '\\':
                at += 2
                continue
            depth += (source[at] == '{') - (source[at] == '}')
            at += 1
        raw = source[begin:at - 1]
        cleaned = ' '.join(re.sub(r'(?m)^\s*% ?', '', raw).split())
        return cleaned, (begin, at - 1), at
    result = []
    for match in re.finditer(r'\\changes\s*(?=\{)', source):
        version, version_span, at = group(match.end())
        date, date_span, at = group(at)
        text, _, _ = group(at)
        result.append({'version': version, 'date': date, 'text': text,
                       'id': release.change_id(version, text), 'span': date_span,
                       'version_span': version_span})
    return result


def known_dates(baseline, history):
    original = {}
    for version, date, text in release.change_records(baseline):
        original.setdefault(release.change_id(version, text), Counter())[date] += 1
    published = {c['id']: r['published_on'].replace('-', '/')
                 for r in history.get('releases', []) for c in r['changes']}
    return original, published


def check(source, baseline, history):
    original, published = known_dates(baseline, history)
    for entry in spans(source):
        identity, date = entry['id'], entry['date']
        if identity in original:
            # The original dtx repeats some version/text pairs for different
            # classes, sometimes with different dates. Preserve each occurrence.
            if not original[identity][date]:
                raise ValueError('Published historical date was edited: ' + entry['text'])
            original[identity][date] -= 1
        elif identity in published:
            if date not in (ZERO, published[identity]):
                raise ValueError('Published dev date was edited: ' + entry['text'])
        elif date != ZERO:
            raise ValueError('New changes must use 0000/00/00: ' + entry['text'])


def stamp(source, baseline, history, date, published_only=False):
    check(source, baseline, history)
    original, published = known_dates(baseline, history)
    edits, journal = [], []
    for entry in spans(source):
        if entry['date'] != ZERO or entry['id'] in original:
            continue
        if published_only and entry['id'] not in published:
            continue
        target = published.get(entry['id'], date)
        edits.append((*entry['span'], target))
        journal.append({'id': entry['id'], 'version': entry['version'], 'text': entry['text'],
                        'before': ZERO, 'after': target})
    for begin, end, target in reversed(edits):
        source = source[:begin] + target + source[end:]
    return source, journal


def context(history_path):
    plan = versions.load_plan()
    official = plan['official_release'] if plan else versions.fetch_official()
    baseline_ref = official['tag']
    baseline = release.command('git', 'show', baseline_ref + ':hithesis.dtx').stdout
    if history_path and history_path.exists():
        history = json.loads(history_path.read_text())
    else:
        history = {'schema': 1, 'repository': release.REPOSITORY, 'releases': []}
    return baseline, history


def stage(history_path, journal_path):
    baseline, history = context(history_path)
    source = (ROOT / 'hithesis.dtx').read_text()
    source_commit = release.command('git', 'rev-parse', 'HEAD').stdout.strip()
    release.command('git', 'diff', '--exit-code', 'HEAD', '--', 'hithesis.dtx')
    plan = versions.load_plan() or versions.make_plan(history)
    if plan['source_commit'] != source_commit or plan['source_sha256'] != release.digest(source.encode()):
        raise ValueError('Version plan does not match the checked-out source')
    check(source, baseline, history)
    original, published = known_dates(baseline, history)
    versioned, version_updates = versions.rewrite_pending(source, plan, spans(source), original.keys() | published.keys())
    date = datetime.now(ZoneInfo('Asia/Shanghai')).strftime('%Y/%m/%d')
    dated, entries = stamp(versioned, baseline, history, date)
    if dated != source:
        (ROOT / 'hithesis.dtx').write_text(dated)
        release.command('git', 'add', '--', 'hithesis.dtx')
        release.command('git', '-c', 'user.name=github-actions[bot]', '-c',
                        'user.email=41898282+github-actions[bot]@users.noreply.github.com',
                        'commit', '-m', f'chore(dev): prepare {plan["version"]} for {date}',
                        '-m', f'Source-Commit: {source_commit}\nPublication-Date: {date}')
    date_commit = release.command('git', 'rev-parse', 'HEAD').stdout.strip()
    record = {'source_commit': source_commit, 'date_commit': date_commit, 'date': date,
               'source_sha256': release.digest(source.encode()), 'dated_sha256': release.digest(dated.encode()),
              'entries': entries, 'version_plan': plan, 'version_updates': version_updates}
    release.write_json(journal_path, record)
    if date_commit != source_commit:
        release.command('git', 'bundle', 'create', str(journal_path.with_suffix('.bundle')),
                        source_commit + '..HEAD')
    print('Staged', plan['version'], len(entries), 'date replacements for', date, 'commit', date_commit)


def plan():
    required = True
    if os.environ.get('PREFLIGHT_ONLY') == 'true':
        required = False
    elif os.environ.get('PUBLISH_ONLY') == 'true':
        head = release.command('git', 'rev-parse', 'HEAD').stdout.strip()
        previous = release.command('git', 'show', 'origin/gh-pages:dev.json', check=False)
        if previous.returncode == 0:
            published = json.loads(previous.stdout)
            official = versions.fetch_official()
            required = (published['commit'] != head or
                        published.get('version_plan', {}).get('official_release', {}).get('tag') != official['tag'])
    with Path(os.environ['GITHUB_OUTPUT']).open('a') as output:
        output.write('build_required=' + str(required).lower() + '\n')
    print('Publication preflight only; no build requested' if os.environ.get('PREFLIGHT_ONLY') == 'true'
          else 'Build required' if required else 'No dev updates since the last published date commit')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('check', 'stage', 'plan'))
    parser.add_argument('--history', type=Path)
    parser.add_argument('--journal', type=Path, default=ROOT / 'build/dev-date-stamp.json')
    args = parser.parse_args()
    if args.action == 'plan':
        plan()
    elif args.action == 'stage':
        stage(args.history, args.journal)
    else:
        baseline, history = context(args.history)
        check((ROOT / 'hithesis.dtx').read_text(), baseline, history)
        print('Development changes use placeholder dates; published dates preserved')
