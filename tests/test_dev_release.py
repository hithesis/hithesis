"""Dated preview identity, changes attribution and real zip payload regression checks."""
from datetime import datetime, timezone
import importlib.util
import io
import json
import os
from pathlib import Path
import tempfile
import subprocess
import unittest
from unittest.mock import patch
from types import SimpleNamespace
import zipfile

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('dev_release', ROOT / 'scripts/dev-release.py')
release = importlib.util.module_from_spec(spec)
spec.loader.exec_module(release)


def build(day='2026-10-24T01:00:00+00:00', commit='a' * 40, run=123):
    return release.metadata('v3.2b', commit, datetime.fromisoformat(day), run, 1, run) | {'source_sha256': 'f' * 64}


def metadata_only_gate():
    """Isolate packaging/order tests; real PDF parsing has separate gate/render tests."""
    gate = release.report_gate()
    def validate(path, info):
        data = path.read_bytes()
        return {'identity': gate.identity(info), 'sha256': release.digest(data), 'size': len(data),
                'pages': 1, 'ai_label': gate.AI_LABEL}
    gate.validate = validate
    return gate


class DevReleaseTests(unittest.TestCase):
    def test_failed_git_command_shows_reason_without_logging_credentials(self):
        failed = subprocess.CompletedProcess(['git'], 128, '', 'remote: write access denied for fake-secret-token')
        with patch.dict(os.environ, {'GH_TOKEN': 'fake-secret-token'}), \
                patch.object(release.subprocess, 'run', return_value=failed), patch('sys.stderr', new_callable=io.StringIO) as error:
            with self.assertRaises(subprocess.CalledProcessError):
                release.command('git', 'push', 'origin', 'HEAD:refs/tags/test')
            self.assertIn('write access denied', error.getvalue())
            self.assertNotIn('fake-secret-token', error.getvalue())

    def test_version_month_day_and_timezone(self):
        info = build('2026-10-23T17:00:00+00:00')
        self.assertEqual(info['label'], 'v3.2b-dev.1024')
        self.assertEqual(info['published_on'], '2026-10-24')
        self.assertTrue(info['built_at'].endswith('+08:00'))
        self.assertNotEqual(info['build_id'], build(run=124)['build_id'])
        self.assertNotEqual(info['build_id'], build('2027-10-23T17:00:00+00:00')['build_id'])
        self.assertNotIn('tag', info)
        self.assertIsNone(info['download_base'])

    def test_new_changes_get_release_date_and_history_is_preserved(self):
        baseline = r'% \changes{v3.2a}{2026/10/12}{历史条目。}'
        source = baseline + '\n' + r'% \changes{v3.2b}{0000/00/00}{修复 \cs{emultiline} 的{长字段}。}'
        empty = {'schema': 1, 'repository': 'hithesis/hithesis', 'releases': []}
        first, history = release.build_history(build(), source, baseline, empty)
        self.assertEqual(len(first['changes']), 1)
        self.assertEqual(first['changes'][0]['published_on'], '2026-10-24')
        self.assertEqual(first['changes'][0]['source_date'], '0000/00/00')
        first['files'] = {'large-asset.zip': {'sha256': 'a' * 64}}
        self.assertNotIn('files', history['releases'][0])
        # Editing a development date alone must not announce the same change again.
        updated = source.replace('0000/00/00', '2026/10/25') + '\n' + r'% \changes{v3.2b}{0000/00/00}{新增功能。}'
        second, later = release.build_history(build('2026-10-25T01:00:00+00:00', 'b' * 40, 124), updated, baseline, history)
        self.assertEqual([c['text'] for c in second['changes']], ['新增功能。'])
        self.assertEqual(later['releases'][0], history['releases'][0])
        log = release.changelog(later)
        self.assertIn('v3.2b-dev.1024 · 2026-10-24', log)
        self.assertIn('v3.2b-dev.1025 · 2026-10-25', log)
        self.assertNotIn('历史条目', log)

    def test_multiline_nested_changes(self):
        source = '% \\changes{v3.2b}{0000/00/00}{第一行 \\cs{foo}\n% 第二行含 \\{ 与 \\}。}'
        self.assertEqual(len(release.change_records(source)), 1)
        self.assertIn(r'\{', release.change_records(source)[0][2])

    def test_stamps_all_archives_without_changing_runtime_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            info = build()
            for i in range(42):
                with zipfile.ZipFile(folder / f'variant-{i}.zip', 'w') as z:
                    z.writestr(f'variant-{i}-v3.2b/', '')
                    z.writestr(f'variant-{i}-v3.2b/hithesisbook.cls', b'unchanged runtime')
            with zipfile.ZipFile(folder / 'hithesis-examples.zip', 'w') as z:
                z.writestr('hithesis-examples/', '')
                for i in range(42):
                    z.writestr(f'hithesis-examples/variant-{i}-v3.2b/thesis.tex', 'example')
            (folder / 'hithesis-ctan.zip').write_bytes(b'original CTAN archive')
            (folder / 'MD5SUMS').write_text('stale checksums')
            release.stamp_archives(folder, info)
            with zipfile.ZipFile(folder / 'variant-0.zip') as z:
                self.assertEqual(z.read('variant-0-v3.2b-dev.1024/hithesisbook.cls'), b'unchanged runtime')
                self.assertEqual(json.loads(z.read('variant-0-v3.2b-dev.1024/BUILD-INFO.json'))['commit'], info['commit'])
            with zipfile.ZipFile(folder / 'hithesis-examples.zip') as z:
                self.assertEqual(sum(n.endswith('/BUILD-INFO.json') for n in z.namelist()), 42)
                self.assertIn('hithesis-examples/variant-41-v3.2b-dev.1024/thesis.tex', z.namelist())
            self.assertEqual((folder / 'hithesis-ctan.zip').read_bytes(), b'original CTAN archive')
            self.assertFalse((folder / 'MD5SUMS').exists())
            self.assertEqual(len((folder / 'SHA256SUMS').read_text().splitlines()), 44)

    def test_rejects_incomplete_packages(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                release.stamp_archives(Path(tmp), build())

    def test_prepare_links_pdf_hash_and_history_to_the_dated_version(self):
        from test_dev_version import source
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'build').mkdir()
            (root / 'tests').mkdir()
            (root / 'tests/change-history.py').write_bytes((ROOT / 'tests/change-history.py').read_bytes())
            dist = root / 'dist'
            dist.mkdir()
            original = source('v3.2b')
            dated = source('v3.3a').replace('0000/00/00', '2026/10/25')
            (root / 'hithesis.dtx').write_text(dated)
            plan = {'version': 'v3.3a', 'official_release': {'tag': 'v3.2a'}}
            journal = {'source_commit': 'a' * 40, 'date_commit': 'b' * 40,
                'source_sha256': release.digest(original.encode()), 'dated_sha256': release.digest(dated.encode()),
                'date': '2026/10/25', 'version_plan': plan, 'entries': []}
            release.write_json(root / 'build/dev-date-stamp.json', journal)
            for i in range(42):
                with zipfile.ZipFile(dist / f'variant-{i}.zip', 'w') as archive:
                    archive.writestr(f'variant-{i}-v3.3a/hithesisbook.cls', 'runtime')
            with zipfile.ZipFile(dist / 'hithesis-examples.zip', 'w') as archive:
                archive.writestr('hithesis-examples/variant-0-v3.3a/thesis.tex', 'example')
            def command(*args, **kwargs):
                if args[:2] == ('python3', 'scripts/release.py'):
                    return SimpleNamespace(stdout='v3.3a\n')
                if args[:2] == ('git', 'rev-parse'):
                    return SimpleNamespace(stdout='b' * 40 + '\n')
                if args[:2] == ('git', 'show'):
                    text = original if args[2].startswith('a' * 40) else r'% \changes{v3.2a}{2026/10/12}{Published.}'
                    return SimpleNamespace(stdout=text)
                return SimpleNamespace(stdout='', returncode=0)
            def report(info, commits, directory):
                self.assertEqual(info['version'], 'v3.3a')
                (directory / 'DEV_UPDATE.pdf').write_bytes(b'%PDF-local-report')
                (directory / 'DEV_UPDATE.md').write_text('Detailed changes')
                return {'model': 'deepseek-flash', 'input_sha256': 'c' * 64, 'message': '关键词对齐方式有变化。'}
            environment = {'GITHUB_REPOSITORY': 'hithesis/hithesis', 'GITHUB_REF': 'refs/heads/dev',
                           'GITHUB_EVENT_NAME': 'workflow_dispatch', 'GITHUB_SHA': 'a' * 40,
                           'GITHUB_RUN_ID': '1', 'GITHUB_RUN_ATTEMPT': '1', 'GITHUB_RUN_NUMBER': '1'}
            with patch.object(release, 'ROOT', root), patch.object(release, 'command', side_effect=command), \
                    patch.object(release.versions, 'commits_since', return_value=[]), \
                    patch.object(release, 'build_update_report', side_effect=report), \
                    patch.object(release, 'report_gate', return_value=metadata_only_gate()), \
                    patch.object(release, 'datetime') as clock, patch.dict(os.environ, environment):
                clock.now.return_value = datetime.fromisoformat('2026-10-25T01:00:00+00:00')
                release.prepare(dist, root / 'missing-history.json')
            info = json.loads((dist / 'dev.json').read_text())
            history = json.loads((dist / 'dev-history.json').read_text())
            self.assertEqual(info['label'], 'v3.3a-dev.1025')
            self.assertEqual(info['report']['sha256'], release.digest(b'%PDF-local-report'))
            self.assertEqual(history['releases'][-1]['report'], info['report'])
            self.assertIn('DEV_UPDATE.pdf', info['files'])
            self.assertIn('DEV_UPDATE.pdf', (dist / 'SHA256SUMS').read_text())
            self.assertIn(info['report']['url'], (dist / 'DEV_RELEASE_NOTES.md').read_text())
            with zipfile.ZipFile(dist / 'variant-0.zip') as archive:
                identity = json.loads(archive.read('variant-0-v3.3a-dev.1025/BUILD-INFO.json'))
                self.assertEqual(identity['version_plan'], plan)
                self.assertEqual(identity['report'], info['report'])

    def test_publish_is_upstream_dev_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            release.write_json(folder / 'dev.json', build())
            with patch.dict(os.environ, {'GITHUB_REPOSITORY': 'someone/fork', 'GITHUB_REF': 'refs/heads/dev',
                                        'GITHUB_EVENT_NAME': 'push', 'GITHUB_SHA': 'a' * 40}), patch.object(release, 'command') as run:
                with self.assertRaises(ValueError):
                    release.publish(folder, folder)
                run.assert_not_called()

    def test_changed_official_release_aborts_before_publication(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            release.write_json(root / 'dev.json', build() | {'version_plan': {'official_release': {'tag': 'v3.2a'}}})
            with patch.dict(os.environ, {'GITHUB_REPOSITORY': 'hithesis/hithesis', 'GITHUB_REF': 'refs/heads/dev',
                                         'GITHUB_EVENT_NAME': 'workflow_dispatch', 'GITHUB_SHA': 'a' * 40}), \
                    patch.object(release.versions, 'fetch_official', return_value={'tag': 'v3.2b'}), \
                    patch.object(release, 'report_gate') as gate, \
                    patch.object(release, 'command') as command:
                with self.assertRaisesRegex(ValueError, 'Official Release changed'):
                    release.publish(root, root)
                command.assert_not_called()

    def test_assets_publish_before_pointer_and_editor_is_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            dist, site = folder / 'dist', folder / 'site'
            dist.mkdir(); site.mkdir(); (site / 'editor').mkdir()
            (site / 'editor/index.html').write_text('existing editor')
            (dist / 'example.zip').write_bytes(b'validated asset')
            pdf = b'%PDF-local-report'
            (dist / 'DEV_UPDATE.pdf').write_bytes(pdf)
            info = build() | {'source_commit': 'a' * 40, 'previous_commit': None, 'files': {'example.zip': {
                 'sha256': release.digest(b'validated asset'), 'size': 15}}}
            info['files']['DEV_UPDATE.pdf'] = {'sha256': release.digest(pdf), 'size': len(pdf)}
            info['report'] = {'filename': 'DEV_UPDATE.pdf', 'url': info['release_url'] + 'DEV_UPDATE.pdf',
                'sha256': release.digest(pdf), 'identity': release.report_gate().identity(info),
                'model': 'deepseek-flash', 'input_sha256': 'c' * 64}
            release.write_json(dist / 'dev.json', info)
            for name in ('DEV_CHANGELOG.md', 'SHA256SUMS', 'DEV_RELEASE_NOTES.md'):
                (dist / name).write_text('{}')
            release.write_json(dist / 'dev-history.json', {'schema': 1, 'releases': [dict(info)]})
            calls = []
            def run(*args, **kwargs):
                calls.append(args)
                if args[0] == 'gh':
                    self.assertEqual(args, ('gh', 'api', '--method', 'POST', 'repos/hithesis/hithesis/pages/builds'))
                self.assertFalse(any('refs/tags/' in str(arg) for arg in args))
                if args[:3] == ('git', 'rev-parse', 'HEAD'):
                    return SimpleNamespace(returncode=0, stdout='d' * 40 + '\n', stderr='')
                if args[:2] == ('git', 'push'):
                    self.assertEqual(kwargs.get('cwd'), site)
                    self.assertEqual(args[2:], ('origin', 'HEAD:gh-pages'))
                    pointer = json.loads((site / 'dev.json').read_text())
                    self.assertEqual(pointer['build_id'], info['build_id'])
                    self.assertEqual(pointer['download_snapshot_commit'], 'd' * 40)
                    self.assertEqual((site / 'dev-downloads/example.zip').read_bytes(), b'validated asset')
                    self.assertEqual((site / 'dev-builds' / info['build_id'] / 'DEV_UPDATE.pdf').read_bytes(), pdf)
                return SimpleNamespace(returncode=0, stdout='', stderr='')
            with patch.dict(os.environ, {'GITHUB_REPOSITORY': 'hithesis/hithesis', 'GITHUB_REF': 'refs/heads/dev',
                                        'GITHUB_EVENT_NAME': 'workflow_dispatch', 'GITHUB_SHA': 'a' * 40}), \
                    patch.object(release, 'report_gate', return_value=metadata_only_gate()), \
                    patch.object(release, 'wait_for_public_pdf') as public_pdf, \
                    patch.object(release, 'command', side_effect=run):
                release.publish(dist, site)
            public_pdf.assert_called_once()
            pointer = json.loads((site / 'dev.json').read_text())
            self.assertEqual(pointer['download_base'], 'https://raw.githubusercontent.com/hithesis/hithesis/' + 'd' * 40 + '/dev-downloads/')
            self.assertEqual((site / 'editor/index.html').read_text(), 'existing editor')
            self.assertFalse(any('--force' in c for c in calls))

    def test_zip_snapshot_is_a_real_commit_and_never_a_tag(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); dist, site = root / 'dist', root / 'site'
            dist.mkdir(); site.mkdir(); (site / 'editor').mkdir()
            (site / 'editor/index.html').write_text('keep editor')
            subprocess.run(['git', 'init', '-q', '-b', 'gh-pages'], cwd=site, check=True)
            subprocess.run(['git', 'add', 'editor/index.html'], cwd=site, check=True)
            subprocess.run(['git', '-c', 'user.name=test', '-c', 'user.email=test@example.invalid',
                            'commit', '-qm', 'test: initial site'], cwd=site, check=True)
            pdf = b'%PDF-mocked-parser'
            (dist / 'DEV_UPDATE.pdf').write_bytes(pdf)
            (dist / 'example.zip').write_bytes(b'original ZIP')
            info = build() | {'previous_commit': None, 'files': {
                'example.zip': {'sha256': release.digest(b'original ZIP'), 'size': 12},
                'DEV_UPDATE.pdf': {'sha256': release.digest(pdf), 'size': len(pdf)}}}
            info['report'] = {'filename': 'DEV_UPDATE.pdf', 'url': info['release_url'] + 'DEV_UPDATE.pdf',
                'sha256': release.digest(pdf), 'identity': release.report_gate().identity(info),
                'model': 'deepseek-flash', 'input_sha256': 'c' * 64}
            release.write_json(dist / 'dev.json', info)
            release.write_json(dist / 'dev-history.json', {'schema': 1, 'releases': [dict(info)]})
            (dist / 'DEV_CHANGELOG.md').write_text('notes')
            original = release.command
            def command(*args, **kwargs):
                self.assertFalse(any('refs/tags/' in str(arg) for arg in args))
                if args[0] == 'gh':
                    self.assertEqual(args, ('gh', 'api', '--method', 'POST', 'repos/hithesis/hithesis/pages/builds'))
                    return subprocess.CompletedProcess(args, 0, '', '')
                if args[:2] == ('git', 'push'):
                    return subprocess.CompletedProcess(args, 0, '', '')
                return original(*args, **kwargs)
            environment = {'GITHUB_REPOSITORY': 'hithesis/hithesis', 'GITHUB_REF': 'refs/heads/dev',
                'GITHUB_EVENT_NAME': 'workflow_dispatch', 'GITHUB_SHA': info['source_commit']}
            with patch.dict(os.environ, environment), patch.object(release, 'command', side_effect=command), \
                    patch.object(release, 'report_gate', return_value=metadata_only_gate()), \
                    patch.object(release, 'wait_for_public_pdf'):
                release.publish(dist, site)
            published = json.loads((site / 'dev.json').read_text())
            snapshot = published['download_snapshot_commit']
            subprocess.run(['git', 'merge-base', '--is-ancestor', snapshot, 'HEAD'], cwd=site, check=True)
            (site / 'dev-downloads/example.zip').write_bytes(b'newer ZIP')
            old = subprocess.check_output(['git', 'show', snapshot + ':dev-downloads/example.zip'], cwd=site)
            self.assertEqual(old, b'original ZIP')
            self.assertEqual(subprocess.check_output(['git', 'tag', '--list'], cwd=site), b'')
            self.assertEqual((site / 'editor/index.html').read_text(), 'keep editor')

    def test_same_build_retry_imports_snapshot_before_date_writeback(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); dist, site = root / 'dist', root / 'site'
            dist.mkdir(); site.mkdir()
            pdf = b'%PDF-mocked-parser'
            source = 'dated source\n'
            (dist / 'DEV_UPDATE.pdf').write_bytes(pdf)
            (dist / 'dev-date-stamp.bundle').write_bytes(b'mocked bundle')
            info = build() | {'source_sha256': release.digest(source.encode()), 'date_stamp': {'entries': [{}]},
                'files': {'DEV_UPDATE.pdf': {'sha256': release.digest(pdf), 'size': len(pdf)}}}
            info['report'] = {'filename': 'DEV_UPDATE.pdf', 'url': info['release_url'] + 'DEV_UPDATE.pdf',
                'sha256': release.digest(pdf), 'identity': release.report_gate().identity(info),
                'model': 'deepseek-flash', 'input_sha256': 'c' * 64}
            release.write_json(dist / 'dev.json', info)
            release.write_json(site / 'dev.json', info)
            release.write_json(dist / 'dev-history.json', {'schema': 1, 'releases': [dict(info)]})
            calls = []
            def command(*args, **kwargs):
                calls.append(args)
                return subprocess.CompletedProcess(args, 0, source if args[:2] == ('git', 'show') else '', '')
            def writeback(*args):
                self.assertTrue(any(c[:2] == ('git', 'fetch') for c in calls))
                self.assertIn(('gh', 'api', '--method', 'POST', 'repos/hithesis/hithesis/pages/builds'), calls)
            environment = {'GITHUB_REPOSITORY': 'hithesis/hithesis', 'GITHUB_REF': 'refs/heads/dev',
                'GITHUB_EVENT_NAME': 'workflow_dispatch', 'GITHUB_SHA': info['source_commit']}
            with patch.dict(os.environ, environment), patch.object(release, 'command', side_effect=command), \
                    patch.object(release, 'report_gate', return_value=metadata_only_gate()), \
                    patch.object(release, 'wait_for_public_pdf'), patch.object(release, 'backfill_dev', side_effect=writeback):
                release.publish(dist, site)
            self.assertFalse(any(c[:2] == ('git', 'push') for c in calls))


if __name__ == '__main__':
    unittest.main()
