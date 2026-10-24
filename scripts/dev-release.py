"""Package dated dev previews and publish their public download manifest."""
import argparse
from copy import copy
from datetime import datetime
import hashlib
import html
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
import zipfile
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
REPOSITORY = 'hithesis/hithesis'
SITE = 'https://hithesis.site'
spec = importlib.util.spec_from_file_location('dev_version', ROOT / 'scripts/dev-version.py')
versions = importlib.util.module_from_spec(spec)
spec.loader.exec_module(versions)


def command(*args, cwd=ROOT, check=True):
    if args[0] == 'git':
        args = ('git', '-c', f'safe.directory={cwd}', *args[1:])
    result = subprocess.run(args, cwd=cwd, check=False, text=True, capture_output=True)
    message = result.stderr or ''
    for name in ('GH_TOKEN', 'GITHUB_TOKEN', 'DEV_REPORT_API_KEY'):
        secret = os.environ.get(name)
        if secret:
            message = message.replace(secret, '[REDACTED]')
    result.stderr = message
    if check and result.returncode:
        if message:
            print(message[:4000], file=sys.stderr)
        raise subprocess.CalledProcessError(result.returncode, args, output=result.stdout, stderr=message)
    return result


def digest(data):
    return hashlib.sha256(data).hexdigest()


def write_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def build_update_report(info, commits, directory):
    spec = importlib.util.spec_from_file_location('dev_report', ROOT / 'scripts/dev-report.py')
    report = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(report)
    return report.build(info, commits, directory, ai_required=True)


def report_gate():
    spec = importlib.util.spec_from_file_location('dev_report_gate', Path(__file__).with_name('dev-report-gate.py'))
    gate = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gate)
    return gate


def change_records(source):
    # Reuse the maintenance parser: nested TeX arguments and multiline dtx comments.
    spec = importlib.util.spec_from_file_location('change_history', ROOT / 'tests/change-history.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.records(source)


def change_id(version, text):
    return digest((version + '\n' + ' '.join(text.split())).encode())


def plain_tex(text):
    text = re.sub(r'\\(?:cs|env|pkg|file|option|texttt|textbf|emph)\s*\{([^{}]*)\}', r'\1', text)
    text = re.sub(r'\\(?:issue|pr)(?:\[([^]]+)\]|\{([^}]+)\})',
                  lambda m: '#' + (m[1] or m[2]), text)
    text = re.sub(r'\\([%&#_{}])', r'\1', text)
    return ' '.join(text.replace('~', ' ').split())


def metadata(version, commit, now, run_id, attempt, run_number):
    if not re.fullmatch(r'v\d+\.\d+[a-z]?', version):
        raise ValueError('Invalid package version')
    if not re.fullmatch(r'[0-9a-f]{40}', commit):
        raise ValueError('Expected a full source commit SHA')
    if not all(str(n).isdigit() and int(n) > 0 for n in (run_id, attempt, run_number)):
        raise ValueError('Invalid workflow run identity')
    now = now.astimezone(ZoneInfo('Asia/Shanghai'))
    label = f'{version}-dev.{now:%m%d}'
    # A build identifier is metadata/a directory name, never a Git tag.
    build_id = f'dev-{now:%Y%m%d}-{commit[:12]}-{run_id}-{attempt}'
    return {
        'schema': 2, 'repository': REPOSITORY, 'branch': 'dev',
        'version': version, 'label': label, 'date': now.strftime('%m%d'),
        'published_on': now.strftime('%Y-%m-%d'), 'built_at': now.isoformat(timespec='seconds'),
        'commit': commit, 'source_commit': commit, 'build_id': build_id, 'run_number': int(run_number), 'run_attempt': int(attempt),
        'run_url': f'https://github.com/{REPOSITORY}/actions/runs/{run_id}',
        'release_url': f'{SITE}/dev-builds/{build_id}/',
        'download_base': None,
    }


def build_history(info, source, baseline, history):
    if history.get('schema') != 1 or history.get('repository') != REPOSITORY:
        raise ValueError('Invalid dev history')
    releases = history.get('releases', [])
    previous = releases[-1]['commit'] if releases else None
    previous_source = releases[-1].get('source_commit', previous) if releases else None
    seen = {change_id(v, t) for v, _, t in change_records(baseline)}
    seen.update(c['id'] for release in releases for c in release['changes'])
    changes = []
    for version, date, text in change_records(source):
        identity = change_id(version, text)
        if identity in seen:
            continue
        seen.add(identity)
        changes.append({'id': identity, 'version': version, 'source_date': date,
                        'published_on': info['published_on'], 'text': plain_tex(text), 'tex': text})
    info = info | {'previous_commit': previous, 'previous_source_commit': previous_source, 'changes': changes}
    if previous_source:
        info['compare_url'] = f'https://github.com/{REPOSITORY}/compare/{previous_source}...{info["source_commit"]}'
    else:
        info['compare_url'] = f'https://github.com/{REPOSITORY}/commit/{info["source_commit"]}'
    # The daily notification ledger does not need every binary asset's checksum.
    return info, history | {'releases': releases + [dict(info)]}


def changelog(history):
    lines = ['# dev 发布记录', '', '日期按北京时间的 dev 发布日期归档；同日构建以提交号区分。', '']
    for release in reversed(history['releases']):
        lines += [f'## {release["label"]} · {release["published_on"]}', '',
                  f'提交：`{release["commit"]}` · [构建记录]({release["run_url"]})', '']
        lines += ['- ' + c['text'] for c in release['changes']] or ['- 构建、文档或维护更新，详见提交记录。']
        lines += ['', f'[本次提交差异]({release["compare_url"]})', '']
    return '\n'.join(lines)


def stamp_archives(directory, info):
    archives = sorted(p for p in directory.glob('*.zip')
                      if p.name not in ('hithesis-ctan.zip', 'hithesis.tds.zip'))
    if len(archives) != 43 or not (directory / 'hithesis-examples.zip').is_file():
        raise ValueError('Expected 42 verified template archives and one combined archive')
    # Public ZIP addresses are resolved from the Pages asset commit later.
    # Keep a stable build-page link in each ZIP; do not create a hash cycle.
    build_info = json.dumps({key: value for key, value in info.items()
        if key not in ('download_base', 'download_snapshot_commit')}, ensure_ascii=False, indent=2).encode() + b'\n'
    for path in archives:
        temporary = path.with_suffix('.preview.zip')
        with zipfile.ZipFile(path) as original, zipfile.ZipFile(temporary, 'w', zipfile.ZIP_DEFLATED) as output:
            roots = set()
            for original_entry in original.infolist():
                content = original.read(original_entry)
                entry = copy(original_entry)
                parts = entry.filename.split('/')
                index = 1 if parts[0] == 'hithesis-examples' else 0
                if len(parts) <= index or not parts[index]:
                    output.writestr(entry, content)
                    continue
                old = parts[index]
                suffix = '-' + info['version']
                if not old.endswith(suffix):
                    raise ValueError(f'Unexpected archive root: {entry.filename}')
                parts[index] = old[:-len(suffix)] + '-' + info['label']
                roots.add('/'.join(parts[:index + 1]))
                entry.filename = '/'.join(parts)
                output.writestr(entry, content)
            for root in sorted(roots):
                output.writestr(root + '/BUILD-INFO.json', build_info)
        temporary.replace(path)
    # Only zip assets are covered; the manifest has its own asset digests.
    sums = [digest(p.read_bytes()) + '  ' + p.name for p in sorted(directory.glob('*.zip'))]
    (directory / 'SHA256SUMS').write_text('\n'.join(sums) + '\n')
    (directory / 'MD5SUMS').unlink(missing_ok=True)
    for path in directory.glob('*.md5'):
        path.unlink()


def prepare(directory, history_path):
    if os.environ.get('GITHUB_REPOSITORY') != REPOSITORY or os.environ.get('GITHUB_REF') != 'refs/heads/dev':
        raise ValueError('Only the upstream dev branch can prepare public previews')
    if os.environ.get('GITHUB_EVENT_NAME') != 'workflow_dispatch':
        raise ValueError('Only the daily/manual publication workflow prepares dated downloads')
    version = command('python3', 'scripts/release.py', 'version').stdout.strip()
    commit = command('git', 'rev-parse', 'HEAD').stdout.strip()
    journal_path = ROOT / 'build/dev-date-stamp.json'
    journal = json.loads(journal_path.read_text())
    if journal['source_commit'] != os.environ.get('GITHUB_SHA') or journal['date_commit'] != commit:
        raise ValueError('Date commit does not match the tested source')
    source = (ROOT / 'hithesis.dtx').read_bytes()
    if digest(source) != journal['dated_sha256']:
        raise ValueError('Dated source changed after stamping')
    if digest(command('git', 'show', journal['source_commit'] + ':hithesis.dtx').stdout.encode()) != journal['source_sha256']:
        raise ValueError('Date journal does not match the original source')
    command('git', 'diff', '--exit-code', 'HEAD', '--', 'hithesis.dtx')
    info = metadata(version, commit, datetime.now(ZoneInfo('Asia/Shanghai')),
                    os.environ['GITHUB_RUN_ID'], os.environ['GITHUB_RUN_ATTEMPT'], os.environ['GITHUB_RUN_NUMBER'])
    if info['published_on'].replace('-', '/') != journal['date']:
        raise ValueError('Publication crossed a Beijing date boundary; rerun instead of backdating')
    info.update(source_commit=journal['source_commit'], date_stamp=journal)
    plan = journal['version_plan']
    if version != plan['version']:
        raise ValueError('Built source version does not match the daily version plan')
    info['version_plan'] = plan
    info['source_sha256'] = digest((ROOT / 'hithesis.dtx').read_bytes())
    if history_path.exists():
        history = json.loads(history_path.read_text())
    else:
        history = {'schema': 1, 'repository': REPOSITORY, 'releases': []}
    baseline_ref = plan['official_release']['tag']
    baseline = command('git', 'show', baseline_ref + ':hithesis.dtx').stdout
    info, history = build_history(info, (ROOT / 'hithesis.dtx').read_text(), baseline, history)
    commits = versions.commits_since(info['previous_source_commit'] or baseline_ref, info['source_commit'], enrich=True)
    generated = build_update_report(info, commits, directory)
    checked = report_gate().validate(directory / 'DEV_UPDATE.pdf', info)
    if generated.get('model') != 'deepseek-flash' or not generated.get('input_sha256'):
        raise ValueError('Validated DeepSeek draft required; publication blocked')
    info['report'] = {'filename': 'DEV_UPDATE.pdf', 'url': info['release_url'] + 'DEV_UPDATE.pdf',
                       **checked, 'model': generated['model'], 'input_sha256': generated['input_sha256']}
    info['announcement'] = generated['message']
    history['releases'][-1]['report'] = info['report']
    history['releases'][-1]['announcement'] = info['announcement']
    stamp_archives(directory, info)
    info['files'] = {p.name: {'sha256': digest(p.read_bytes()), 'size': p.stat().st_size}
                     for p in sorted(directory.iterdir())
                     if (p.suffix == '.zip' and p.name not in ('hithesis-ctan.zip', 'hithesis.tds.zip'))
                     or p.name in ('DEV_UPDATE.pdf', 'DEV_UPDATE.md', 'DEV_AI_DRAFT.json')}
    (directory / 'SHA256SUMS').write_text(''.join(
        record['sha256'] + '  ' + name + '\n' for name, record in info['files'].items()))
    write_json(directory / 'dev.json', info)
    report_gate().publication(directory, info)
    write_json(directory / 'dev-history.json', history)
    (directory / 'DEV_CHANGELOG.md').write_text(changelog(history), encoding='utf-8')
    notes = [f'# {info["label"]}', '', f'发布日期：{info["published_on"]}（北京时间）', '',
             f'源版本：{info["version"]}，提交：`{commit}`', '',
             *(['- ' + c['text'] for c in info['changes']] or ['- 构建、文档或维护更新。']), '',
             f'[详细更新说明（PDF）]({info["report"]["url"]})', '',
             f'[下载模板](https://hithesis.site/?version=dev) · [构建记录]({info["run_url"]})', '']
    (directory / 'DEV_RELEASE_NOTES.md').write_text('\n'.join(notes), encoding='utf-8')
    shutil.copy2(journal_path, directory / 'dev-date-stamp.json')
    bundle = journal_path.with_suffix('.bundle')
    if bundle.exists():
        shutil.copy2(bundle, directory / 'dev-date-stamp.bundle')
    print(info['label'], commit, 'dated archives and changes prepared')


def backfill_dev(info, history):
    journal = info.get('date_stamp', {})
    if not journal.get('entries') and not journal.get('version_updates'):
        return
    direct = command('git', 'push', 'origin', info['commit'] + ':refs/heads/dev', check=False)
    if direct.returncode == 0:
        return
    # dev advanced during the build. Apply known publication dates to its new
    # source only; never replay the old implementation over another maintainer.
    spec = importlib.util.spec_from_file_location('dev_dates', ROOT / 'scripts/dev-dates.py')
    dates = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(dates)
    baseline, _ = dates.context(None)
    for attempt in range(3):
        command('git', 'fetch', 'origin', 'dev')
        folder = Path(tempfile.mkdtemp(prefix='dev-dates-', dir=ROOT / 'build')) / 'tree'
        command('git', 'worktree', 'add', '--detach', str(folder), 'FETCH_HEAD')
        path = folder / 'hithesis.dtx'
        source = path.read_text()
        if journal.get('version_plan'):
            source = versions.backfill_versions(source, journal['version_plan'],
                journal.get('version_updates', []), dates.spans(source))
        dated, entries = dates.stamp(source, baseline, history, info['published_on'].replace('-', '/'), published_only=True)
        if dated == source:
            command('git', 'worktree', 'remove', str(folder))
            return
        path.write_text(dated)
        command('git', 'add', '--', 'hithesis.dtx', cwd=folder)
        command('git', '-c', 'user.name=github-actions[bot]', '-c',
                'user.email=41898282+github-actions[bot]@users.noreply.github.com',
                'commit', '-m', 'chore(dev): record published change dates',
                '-m', 'Release: ' + info['release_url'], cwd=folder)
        result = command('git', 'push', 'origin', 'HEAD:refs/heads/dev', cwd=folder, check=False)
        command('git', 'worktree', 'remove', str(folder))
        if result.returncode == 0:
            return
    raise RuntimeError('dev is changing concurrently; publication dates need a non-force writeback retry')


def site_commit(site, message, paths):
    command('git', 'add', '--', *paths, cwd=site)
    command('git', '-c', 'user.name=github-actions[bot]', '-c',
            'user.email=41898282+github-actions[bot]@users.noreply.github.com',
            'commit', '-m', message, cwd=site)
    return command('git', 'rev-parse', 'HEAD', cwd=site).stdout.strip()


def build_index(info):
    links = []
    for name in info['files']:
        base = info['download_base'] if name.endswith('.zip') else info['release_url']
        links.append('<li><a href="' + html.escape(base + name, quote=True) + '">' + html.escape(name) + '</a></li>')
    return ('<!doctype html><html lang="zh-CN"><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            '<title>' + html.escape(info['label']) + '</title>'
            '<style>body{max-width:900px;margin:32px auto;padding:0 20px;font:16px/1.7 sans-serif}'
            'pre{white-space:pre-wrap;font:inherit}li{margin:4px 0}</style>'
            '<h1>hithesis ' + html.escape(info['label']) + '</h1><p>' + html.escape(info['published_on']) + '</p>'
            '<p>此预览由 AI 比对生成</p><pre>' + html.escape(info.get('announcement', '')) + '</pre>'
            '<h2>下载</h2><ul>' + ''.join(links) + '</ul></html>')


def wait_for_public_pdf(info, timeout=360):
    gate = report_gate()
    report = gate.manifest(info)
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            request = Request(report['url'] + '?verify=' + str(int(time.time())),
                headers={'User-Agent': 'hithesis-dev-publication', 'Cache-Control': 'no-cache'})
            with urlopen(request, timeout=30) as response:
                data = response.read(gate.MAX_PDF_BYTES + 1)
            if digest(data) == report['sha256']:
                with tempfile.TemporaryDirectory(prefix='hithesis-public-pdf-') as temporary:
                    path = Path(temporary) / 'DEV_UPDATE.pdf'
                    path.write_bytes(data)
                    gate.validate(path, info)
                return
        except HTTPError as error:
            error.close()
        except URLError:
            pass
        time.sleep(10)
    raise RuntimeError('The public build PDF is not available or does not validate; publication is not ready')


def request_pages_build():
    # GITHUB_TOKEN can push this repository, but its pushes do not implicitly
    # deploy legacy Pages. pages:write authorizes this explicit build request.
    command('gh', 'api', '--method', 'POST', f'repos/{REPOSITORY}/pages/builds')


def publish(directory, site):
    info = json.loads((directory / 'dev.json').read_text())
    if (os.environ.get('GITHUB_REPOSITORY') != REPOSITORY or
            os.environ.get('GITHUB_REF') != 'refs/heads/dev' or
            os.environ.get('GITHUB_EVENT_NAME') != 'workflow_dispatch' or
            info['source_commit'] != os.environ.get('GITHUB_SHA')):
        raise ValueError('Preview publication requires the tested upstream dev checkout')
    # A missing, corrupt, stale or mismatched PDF blocks every remote write.
    report_gate().publication(directory, info)
    if info.get('version_plan') and versions.fetch_official()['tag'] != info['version_plan']['official_release']['tag']:
        raise ValueError('Official Release changed during the build; rerun against the new baseline')
    for name, record in info['files'].items():
        if Path(name).name != name or digest((directory / name).read_bytes()) != record['sha256']:
            raise ValueError('Preview artifact digest mismatch')
    if (directory / 'dev-date-stamp.bundle').exists():
        command('git', 'fetch', str(directory / 'dev-date-stamp.bundle'), 'HEAD')
    if info.get('date_stamp'):
        if digest(command('git', 'show', info['commit'] + ':hithesis.dtx').stdout.encode()) != info['source_sha256']:
            raise ValueError('Release commit source does not match the dated archive')
    current = json.loads((site / 'dev.json').read_text()) if (site / 'dev.json').exists() else None
    if current and (current['run_number'], current['run_attempt']) >= (info['run_number'], info['run_attempt']):
        if current.get('build_id') == info['build_id']:
            request_pages_build()
            wait_for_public_pdf(info)
            backfill_dev(info, json.loads((directory / 'dev-history.json').read_text()))
        print('A same or newer successful preview is already published')
        return
    previous = current['commit'] if current else None
    if previous != info['previous_commit']:
        raise ValueError('Dev history changed during build; rerun against the current history')
    # Keep only the current ZIP files in the Pages working tree, while their
    # historical bytes remain available via immutable raw Git commit URLs.
    # Small per-build PDFs/notes keep permanent public Pages addresses.
    relative = Path('dev-builds') / info['build_id']
    public = site / relative
    if public.exists():
        raise ValueError('Build directory already exists; use a new workflow attempt')
    public.mkdir(parents=True)
    paths = []
    for name in info['files']:
        destination = Path('dev-downloads') / name if name.endswith('.zip') else relative / name
        target = site / destination
        if current is None and target.exists():
            raise ValueError('Refusing to overwrite an unrecognized download asset')
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(directory / name, target)
        paths.append(destination.as_posix())
    for name in ('SHA256SUMS', 'DEV_RELEASE_NOTES.md', 'dev-date-stamp.json'):
        if (directory / name).exists():
            shutil.copy2(directory / name, public / name)
            paths.append((relative / name).as_posix())
    snapshot = site_commit(site, 'Store dev build assets: ' + info['build_id'], paths)
    if not re.fullmatch(r'[0-9a-f]{40}', snapshot):
        raise ValueError('Invalid download snapshot commit')
    info['download_snapshot_commit'] = snapshot
    info['download_base'] = f'https://raw.githubusercontent.com/{REPOSITORY}/{snapshot}/dev-downloads/'
    history = json.loads((directory / 'dev-history.json').read_text())
    if history['releases'][-1]['build_id'] != info['build_id']:
        raise ValueError('Build history does not match this publication')
    history['releases'][-1].update(download_base=info['download_base'], download_snapshot_commit=snapshot)
    write_json(directory / 'dev.json', info)
    write_json(directory / 'dev-history.json', history)
    write_json(public / 'dev.json', info)
    (public / 'index.html').write_text(build_index(info), encoding='utf-8')
    for name in ('dev.json', 'dev-history.json', 'DEV_CHANGELOG.md'):
        shutil.copy2(directory / name, site / name)
    site_commit(site, 'Update dev downloads: ' + info['label'],
        ['dev.json', 'dev-history.json', 'DEV_CHANGELOG.md', (relative / 'dev.json').as_posix(),
         (relative / 'index.html').as_posix()])
    for attempt in range(3):
        result = command('git', 'push', 'origin', 'HEAD:gh-pages', cwd=site, check=False)
        if result.returncode == 0:
            request_pages_build()
            wait_for_public_pdf(info)
            print('Published', info['label'], info['release_url'])
            # The next push CI must already see the new publication-date ledger.
            backfill_dev(info, history)
            return
        if any(word in (result.stderr or '').lower() for word in ('permission', 'write access', 'authentication', '403')):
            raise RuntimeError('Download-site write access failed: ' + (result.stderr or '')[:1500])
        command('git', 'fetch', 'origin', 'gh-pages', cwd=site)
        remote = command('git', 'show', 'FETCH_HEAD:dev.json', cwd=site, check=False)
        remote_commit = json.loads(remote.stdout)['commit'] if remote.returncode == 0 else None
        if remote_commit != previous:
            raise RuntimeError('Another dev build was published concurrently; rerun against its history')
        # Do not rebase: ZIP URLs reference the first asset commit's exact SHA.
        command('git', '-c', 'user.name=github-actions[bot]', '-c',
                'user.email=41898282+github-actions[bot]@users.noreply.github.com',
                'merge', '--no-edit', 'FETCH_HEAD', cwd=site)
    raise RuntimeError('Could not update Pages metadata after three non-force push attempts')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'publish'))
    parser.add_argument('--dist', type=Path, required=True)
    parser.add_argument('--history', type=Path)
    parser.add_argument('--site', type=Path)
    args = parser.parse_args()
    if args.action == 'prepare':
        if args.history is None:
            parser.error('prepare requires --history (a missing file means the first dev release)')
        prepare(args.dist.resolve(), args.history)
    else:
        if args.site is None:
            parser.error('publish requires --site')
        publish(args.dist.resolve(), args.site.resolve())
