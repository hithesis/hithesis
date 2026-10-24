"""Resolve bounded dev versions from published official Releases and explicit breaking markers."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
from urllib.error import HTTPError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
REPOSITORY = 'hithesis/hithesis'
VERSION = re.compile(r'v?(\d+)\.(\d+)([a-z]?)\Z')
TITLE = re.compile(r'(feat|fix|perf|refactor|docs|test|build|ci|chore|revert|style)'
                   r'(?:\([^()\n]+\))?(!)?:\s+\S.*\Z')
BANNER = re.compile(r'(\\ProvidesExpl(?:Class|File|Package)\{[^}]+\}\{[^}]+\})\{v([^}]+)\}')
DRIVER = re.compile(r'(\\ProvidesFile\{hithesis\.dtx\}\[[^ ]+ )([^ ]+)( )')


def parse(value):
    match = VERSION.fullmatch(value)
    if not match:
        raise ValueError('Unsupported release version: ' + value)
    major, minor, letter = match.groups()
    return int(major), int(minor), ord(letter) - ord('a') + 1 if letter else 0


def display(value):
    major, minor, letter = value
    return f'v{major}.{minor}' + (chr(ord('a') + letter - 1) if letter else '')


def official_release(releases):
    candidates = [r for r in releases if not r.get('draft') and not r.get('prerelease')
                  and r.get('published_at') and VERSION.fullmatch(r.get('tag_name', ''))]
    if not candidates:
        raise ValueError('No published official Release with a supported version tag; bare Git tags are not a baseline')
    selected = max(candidates, key=lambda r: (parse(r['tag_name']), r['published_at']))
    return {'tag': selected['tag_name'], 'version': display(parse(selected['tag_name'])),
            'published_at': selected['published_at'], 'repository': REPOSITORY,
            'url': f'https://github.com/{REPOSITORY}/releases/tag/{selected["tag_name"]}'}


def fetch_official():
    # List all pages: /releases/latest or Git tag ordering can hide older, higher
    # official versions, and bare tags do not prove a published stable release.
    url = f'https://api.github.com/repos/{REPOSITORY}/releases?per_page=100'
    releases = []
    while url:
        if not re.fullmatch(r'https://api\.github\.com/(?:repos/hithesis/hithesis|repositories/\d+)/releases\?[^\s]+', url):
            raise ValueError('Unexpected release pagination URL')
        headers = {'User-Agent': 'hithesis-dev-version', 'Accept': 'application/vnd.github+json'}
        token = os.environ.get('GH_TOKEN') or os.environ.get('GITHUB_TOKEN')
        if token:
            headers['Authorization'] = 'Bearer ' + token
        with urlopen(Request(url, headers=headers), timeout=30) as response:
            page = json.load(response)
            links = response.headers.get('Link', '')
        if not isinstance(page, list):
            raise ValueError('Unexpected GitHub releases response')
        releases.extend(page)
        next_page = re.search(r'<([^>]+)>;\s*rel="next"', links)
        url = next_page[1] if next_page else None
    return official_release(releases)


def git(*args):
    return subprocess.check_output(['git', '-c', f'safe.directory={ROOT}', *args], cwd=ROOT).decode('utf-8')


def source_version(source):
    match = DRIVER.search(source)
    if not match:
        raise ValueError('Missing source package version')
    return display(parse(match[2]))


def footer(message, name):
    match = re.search(r'(?im)^' + re.escape(name) + r':[^\S\n]*(\S[^\n]*)', message)
    if not match:
        return ''
    lines = [match[1].strip()]
    for line in message[match.end():].splitlines()[1:]:
        if re.match(r'^[A-Za-z][A-Za-z -]+:\s*', line):
            break
        lines.append(line)
    return '\n'.join(lines).strip()


def metadata_text(message):
    """Ignore template comments and quoted code examples when reading markers."""
    plain = re.sub(r'<!--.*?-->', '', message, flags=re.S)
    visible, fence = [], None
    for line in plain.splitlines():
        marker = re.match(r'^\s*(`{3,}|~{3,})', line)
        if marker:
            if fence is None:
                fence = marker[1][0]
            elif marker[1][0] == fence:
                fence = None
            continue
        if fence is None:
            visible.append(line)
    return '\n'.join(visible)


def breaking(message):
    lines = message.splitlines()
    title = TITLE.fullmatch(lines[0]) if lines else None
    marked_title = bool(title and title[2])
    # Only the first body paragraph of a standard GitHub merge is a PR title;
    # arbitrary conventional-title examples in documentation are not markers.
    if lines and re.match(r'^Merge pull request #\d+\b', lines[0]):
        merged_title = next((line for line in lines[1:] if line.strip()), '')
        match = TITLE.fullmatch(merged_title)
        marked_title = marked_title or bool(match and match[2])
    plain = metadata_text(message)
    return bool(marked_title or footer(plain, 'BREAKING CHANGE') or footer(plain, 'BREAKING-CHANGE'))


def enrich_commit(record, pr):
    if not pr.get('merged') or pr.get('merge_commit_sha') != record['sha']:
        return record
    message = record['body'] + '\n\n' + pr['title'] + '\n\n' + (pr.get('body') or '')
    return record | {'body': message, 'breaking': record['breaking'] or breaking(pr['title'] + '\n' + (pr.get('body') or '')),
        'migration': footer(message, 'Migration'), 'impact': footer(message, 'Impact'),
        'validation': footer(message, 'Validation'),
        'pull_request': {'number': pr['number'], 'url': pr['html_url']}}


def fetch_pr(number):
    headers = {'User-Agent': 'hithesis-dev-version', 'Accept': 'application/vnd.github+json'}
    token = os.environ.get('GH_TOKEN') or os.environ.get('GITHUB_TOKEN')
    if token:
        headers['Authorization'] = 'Bearer ' + token
    try:
        with urlopen(Request(f'https://api.github.com/repos/{REPOSITORY}/pulls/{int(number)}', headers=headers), timeout=30) as response:
            return json.load(response)
    except HTTPError as error:
        if error.code == 404:
            error.close()
            return {}
        raise


def commits_since(base, head='HEAD', enrich=False):
    subprocess.run(['git', '-c', f'safe.directory={ROOT}', 'merge-base', '--is-ancestor', base, head],
                   cwd=ROOT, check=True, capture_output=True)
    parts = git('log', '--reverse', '--format=%H%x00%B%x00', f'{base}..{head}').split('\0')
    records = []
    for at in range(0, len(parts) - 1, 2):
        sha, message = parts[at].strip(), parts[at + 1].strip()
        if not re.fullmatch(r'[0-9a-f]{40}', sha):
            raise ValueError('Invalid Git log commit identity')
        record = {'sha': sha, 'subject': message.splitlines()[0], 'body': message,
                  'breaking': breaking(message), 'migration': footer(message, 'Migration'),
                  'impact': footer(message, 'Impact'), 'validation': footer(message, 'Validation')}
        match = re.search(r'^Merge pull request #(\d+)\b|\(#(\d+)\)$', record['subject'])
        if enrich and match:
            record = enrich_commit(record, fetch_pr(match[1] or match[2]))
        records.append(record)
    return records


def resolve(official, source, history, commits):
    stable = parse(official['version'])
    major, minor, letter = stable
    normal = (major, minor, letter + 1) if letter < 26 else (major, minor + 1, 1)
    candidates = [normal, parse(source)]
    for release in history.get('releases', []):
        value = release.get('version') or release['label'].split('-dev.')[0]
        candidates.append(parse(value))
    selected = max(candidates)
    marked = [c for c in commits if c['breaking']]
    if marked:
        selected = max(selected, (major, minor + 1, 1))
    if selected[0] != major or selected[1] > minor + 1:
        raise ValueError('Existing dev version exceeds the official Release +1 minor ceiling; '
                         'publish the new official Release first (never downgrade automatically)')
    return {'schema': 1, 'official_release': official, 'source_version': source,
            'normal_version': display(normal), 'version': display(selected),
            'minor_ceiling': f'{major}.{minor + 1}', 'breaking': bool(marked),
            'breaking_commits': marked}


def make_plan(history):
    official = fetch_official()
    source = (ROOT / 'hithesis.dtx').read_text()
    result = resolve(official, source_version(source), history, commits_since(official['tag'], enrich=True))
    return result | {'source_commit': git('rev-parse', 'HEAD').strip(),
                     'source_sha256': hashlib.sha256(source.encode()).hexdigest()}


def load_plan(path=None):
    path = path or ROOT / 'build/dev-version-plan.json'
    if path.exists():
        return json.loads(path.read_text())
    return None


def rewrite_banners(source, target):
    current = source_version(source)
    banners = BANNER.findall(source)
    if len(banners) != 6 or any('v' + version != current for _, version in banners):
        raise ValueError('Source driver and all six runtime versions must agree')
    source = DRIVER.sub(lambda m: m[1] + target.lstrip('v') + m[3], source)
    return BANNER.sub(lambda m: m[1] + '{' + target + '}', source)


def rewrite_pending(source, plan, entries, known_ids):
    target = plan['version']
    edits, updates = [], []
    for entry in entries:
        if entry['date'] == '0000/00/00' and entry['id'] not in known_ids and entry['version'] != target:
            edits.append((*entry['version_span'], target))
            updates.append({'kind': 'changes', 'id': entry['id'], 'text': entry['text'],
                            'before': entry['version'], 'after': target})
    for begin, end, value in reversed(edits):
        source = source[:begin] + value + source[end:]
    current = source_version(source)
    if current != target:
        source = rewrite_banners(source, target)
        updates.insert(0, {'kind': 'package', 'before': current, 'after': target})
    return source, updates


def backfill_versions(source, plan, updates, entries):
    replacements = {u['id']: u['after'] for u in updates if u['kind'] == 'changes'}
    for entry in reversed(entries):
        if entry['date'] == '0000/00/00' and entry['id'] in replacements:
            begin, end = entry['version_span']
            source = source[:begin] + replacements[entry['id']] + source[end:]
    if parse(source_version(source)) < parse(plan['version']):
        source = rewrite_banners(source, plan['version'])
    return source


def check_pr(title, body):
    match = TITLE.fullmatch(title)
    if not match:
        raise ValueError('PR title must use type(scope): summary or type(scope)!: summary')
    body = metadata_text(body)
    compatibility = re.findall(r'(?im)^Compatibility:\s*(compatible|breaking)\s*$', body)
    if len(compatibility) != 1:
        raise ValueError('PR body must contain exactly one Compatibility: compatible|breaking')
    marked = breaking(title + '\n' + body)
    if marked != (compatibility[0].lower() == 'breaking'):
        raise ValueError('Compatibility declaration conflicts with ! / BREAKING CHANGE markers')
    if marked and not footer(body, 'Migration'):
        raise ValueError('Breaking PRs must provide Migration: instructions')
    if marked and not (footer(body, 'BREAKING CHANGE') or footer(body, 'BREAKING-CHANGE')):
        raise ValueError('Breaking PRs must explain BREAKING CHANGE: in the body')
    if not footer(body, 'Validation'):
        raise ValueError('PRs must provide Validation: results or explain why checks were not run')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('resolve', 'check-pr'))
    parser.add_argument('--history', type=Path)
    parser.add_argument('--output', type=Path, default=ROOT / 'build/dev-version-plan.json')
    parser.add_argument('--event', type=Path)
    args = parser.parse_args()
    if args.action == 'check-pr':
        if not args.event:
            parser.error('check-pr requires --event')
        pr = json.loads(args.event.read_text())['pull_request']
        check_pr(pr['title'], pr.get('body') or '')
        print('PR compatibility declaration, breaking markers, migration and validation: PASS')
    else:
        history = json.loads(args.history.read_text()) if args.history and args.history.exists() else {'releases': []}
        plan = make_plan(history)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + '\n')
        print(plan['official_release']['tag'], '→', plan['version'], '(breaking=' + str(plan['breaking']) + ')')
