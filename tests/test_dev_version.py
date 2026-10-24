"""Official Release selection, bounded bumping, metadata policy and safe source writeback."""
import importlib.util
import io
import json
from pathlib import Path
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts' / (name.replace('_', '-') + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


versions = load('dev_version')
dates = load('dev_dates')


def official(tag='v3.2a'):
    return versions.official_release([{'tag_name': tag, 'draft': False, 'prerelease': False,
                                       'published_at': '2026-10-12T06:54:18Z'}])


def commit(message):
    return {'sha': 'a' * 40, 'subject': message.splitlines()[0], 'body': message,
            'breaking': versions.breaking(message), 'migration': versions.footer(message, 'Migration')}


def source(version='v3.2b'):
    return (r'\ProvidesFile{hithesis.dtx}[2026/10/12 ' + version[1:] + ' Template]\n' +
        '\n'.join(r'\ProvidesExplClass{class' + str(i) + '}{2026/10/12}{' + version + '}{Template}'
                  for i in range(6)) + '\n' +
        r'% \changes{v3.2a}{2026/10/12}{Published.}' + '\n' +
        r'% \changes{' + version + r'}{0000/00/00}{Pending.}')


class DevVersionTests(unittest.TestCase):
    def test_only_published_official_releases_are_candidates(self):
        releases = [dict(tag_name='v3.2a', published_at='2026-10-12'),
                    dict(tag_name='v3.3a', published_at='2026-10-13', prerelease=True),
                    dict(tag_name='v9.9a', published_at='2026-10-14', draft=True),
                    dict(tag_name='dev-20261025-sha-1-1', published_at='2026-10-25'),
                    dict(tag_name='v3.1e', published_at='2026-10-26')]
        self.assertEqual(versions.official_release(releases)['version'], 'v3.2a')
        with self.assertRaisesRegex(ValueError, 'No published official Release'):
            versions.official_release(releases[1:4])

    def test_official_release_lookup_follows_github_pagination(self):
        first = io.BytesIO(json.dumps([dict(tag_name='v3.1e', published_at='2026-01-01')]).encode())
        first.headers = {'Link': '<https://api.github.com/repositories/123/releases?per_page=100&page=2>; rel="next"'}
        second = io.BytesIO(json.dumps([dict(tag_name='v3.2a', published_at='2026-10-12')]).encode())
        second.headers = {}
        with patch.object(versions, 'urlopen', side_effect=[first, second]) as request:
            self.assertEqual(versions.fetch_official()['tag'], 'v3.2a')
            self.assertEqual(request.call_count, 2)

    def test_user_version_table_and_no_daily_letter_increment(self):
        breaking = [commit('feat!: remove old option\n\nBREAKING CHANGE: old option removed\nMigration: use the new option')]
        cases = [
            ('v3.2a', 'v3.2a', [], [], 'v3.2b'),
            ('v3.2a', 'v3.2b', [], [], 'v3.2b'),
            ('v3.2a', 'v3.2c', [], [], 'v3.2c'),
            ('v3.2a', 'v3.2b', [], breaking, 'v3.3a'),
            ('v3.2a', 'v3.3a', [], breaking, 'v3.3a'),
            ('v3.2a', 'v3.3a', [], breaking * 3, 'v3.3a'),
            ('v3.2a', 'v3.3c', [], breaking, 'v3.3c'),
            ('v3.2a', 'v3.2b', ['v3.3c'], [], 'v3.3c'),
            ('v3.2b', 'v3.2b', [], [], 'v3.2c'),
            ('v3.2b', 'v3.2c', [], breaking, 'v3.3a'),
            ('v3.3a', 'v3.3a', ['v3.3a'], [], 'v3.3b'),
            ('v3.3a', 'v3.3a', [], breaking, 'v3.4a'),
        ]
        for base, current, history, marked, expected in cases:
            with self.subTest(base=base, current=current, expected=expected):
                plan = versions.resolve(official(base), current,
                    {'releases': [{'version': version} for version in history]}, marked)
                self.assertEqual(plan['version'], expected)
        with self.assertRaisesRegex(ValueError, 'never downgrade'):
            versions.resolve(official(), 'v3.4a', {}, [])

    def test_breaking_markers_cover_squash_merge_and_footers(self):
        for message in ['feat!: remove option', 'fix(cover)!: remove legacy argument (#312)',
                        'refactor: new code\n\nBREAKING CHANGE: incompatible',
                        'fix: new code\n\nBREAKING-CHANGE: incompatible',
                        'Merge pull request #312 from branch\n\nfeat(cover)!: remove old interface']:
            self.assertTrue(versions.breaking(message), message)
        for message in ['fix: keep old behavior!', 'docs: describe BREAKING CHANGE: syntax',
                        'refactor: rewrite without an API change',
                        'docs: show a title\n\nfeat!: example title',
                        'docs: examples\n\n```text\nBREAKING CHANGE: example\n```',
                        'docs: examples\n\n<!--\nBREAKING CHANGE: placeholder\n-->']:
            self.assertFalse(versions.breaking(message), message)

    def test_cosmetic_changes_preserve_normal_development_version(self):
        messages = ['feat(keywords): 调整关键词默认续行对齐', 'fix(layout): 调整字号和段间距',
                    'feat(cover): 长字段自动换行，旧写法继续支持',
                    'feat(caption): 新增双语写法，保留旧命令']
        commits = [commit(message) for message in messages]
        self.assertTrue(all(not item['breaking'] for item in commits))
        for title in messages:
            versions.check_pr(title, 'Compatibility: compatible\nValidation: 旧用法回归通过')
        self.assertEqual(versions.resolve(official(), 'v3.2b', {}, commits)['version'], 'v3.2b')

    def test_verified_merge_pr_body_supplies_markers_and_migration(self):
        merged = commit('Merge pull request #312 from branch\n\nrefactor: simplify options')
        pr = {'number': 312, 'html_url': 'https://github.com/hithesis/hithesis/pull/312',
              'merged': True, 'merge_commit_sha': merged['sha'], 'title': 'refactor: simplify options',
              'body': 'Compatibility: breaking\nBREAKING CHANGE: removed the old key\nMigration: use the new key'}
        result = versions.enrich_commit(merged, pr)
        self.assertTrue(result['breaking'])
        self.assertEqual(result['migration'], 'use the new key')
        self.assertEqual(versions.enrich_commit(merged, pr | {'merge_commit_sha': 'b' * 40}), merged)

    def test_pr_policy_requires_explicit_classification_and_migration(self):
        versions.check_pr('fix(cover): wrap fields', 'Compatibility: compatible\nValidation: 25 checks passed')
        versions.check_pr('feat!: remove key', 'Compatibility: breaking\nBREAKING CHANGE: old key removed\nMigration: replace old by new\nValidation: tests passed')
        bad = [
            ('Fix cover', 'Compatibility: compatible\nValidation: tests passed'),
            ('fix: cover', 'Validation: tests passed'),
            ('feat!: remove key', 'Compatibility: compatible\nValidation: tests passed'),
            ('feat!: remove key', 'Compatibility: breaking\nBREAKING CHANGE: old key removed\nValidation: passed'),
            ('feat!: remove key', 'Compatibility: breaking\nMigration: use new key\nValidation: passed'),
            ('fix: cover', 'Compatibility: compatible\nValidation:\n'),
            ('docs: examples', 'Compatibility: compatible\n```text\nValidation: only an example\n```'),
        ]
        for title, body in bad:
            with self.subTest(title=title, body=body), self.assertRaises(ValueError):
                versions.check_pr(title, body)

    def test_version_stamp_preserves_published_changes_and_runtime_dates(self):
        original = source()
        entries = dates.spans(original)
        known = {entries[0]['id']}
        updated, journal = versions.rewrite_pending(original, {'version': 'v3.3a'}, entries, known)
        self.assertEqual(versions.source_version(updated), 'v3.3a')
        self.assertEqual(len(versions.BANNER.findall(updated)), 6)
        self.assertTrue(all(v == '3.3a' for _, v in versions.BANNER.findall(updated)))
        self.assertIn(r'\changes{v3.2a}{2026/10/12}{Published.}', updated)
        self.assertIn(r'\changes{v3.3a}{0000/00/00}{Pending.}', updated)
        self.assertEqual(len(journal), 2)
        self.assertEqual(updated.count('2026/10/12'), original.count('2026/10/12'))

    def test_concurrent_writeback_keeps_newer_code_version_and_new_pending_changes(self):
        original = source()
        plan = {'version': 'v3.3a'}
        _, journal = versions.rewrite_pending(original, plan, dates.spans(original), set())
        concurrent = source('v3.3c').replace(r'\changes{v3.3c}{0000/00/00}{Pending.}',
            r'\changes{v3.2b}{0000/00/00}{Pending.}') + '\n' + r'% \changes{v3.3c}{0000/00/00}{Newer implementation.}'
        updated = versions.backfill_versions(concurrent, plan, journal, dates.spans(concurrent))
        self.assertEqual(versions.source_version(updated), 'v3.3c')
        self.assertIn(r'\changes{v3.3a}{0000/00/00}{Pending.}', updated)
        self.assertIn(r'\changes{v3.3c}{0000/00/00}{Newer implementation.}', updated)

    def test_real_dtx_version_rewrite_preserves_every_published_record(self):
        text = (ROOT / 'hithesis.dtx').read_text()
        entries = dates.spans(text)
        known = {entry['id'] for entry in entries if entry['date'] != dates.ZERO}
        major, minor, _ = versions.parse(versions.source_version(text))
        target = f'v{major}.{minor + 1}a'
        rewritten, _ = versions.rewrite_pending(text, {'version': target}, entries, known)
        self.assertEqual(versions.source_version(rewritten), target)
        self.assertEqual([version for _, version in versions.BANNER.findall(rewritten)], [target[1:]] * 6)
        old = [(e['version'], e['date'], e['text']) for e in entries if e['id'] in known]
        new = [(e['version'], e['date'], e['text']) for e in dates.spans(rewritten) if e['date'] != dates.ZERO]
        self.assertEqual(old, new)


if __name__ == '__main__':
    unittest.main()
