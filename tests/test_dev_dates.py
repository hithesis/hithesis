"""Date-only stamping preserves repeated historical entries and pending changes."""
import importlib.util
import hashlib
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('dev_dates', ROOT / 'scripts/dev-dates.py')
dates = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(dates)

BASELINE = '\n'.join([
    r'% \changes{v3.1e}{2026/01/07}{设置参考文献列表中的作者是否全大写和最大显示数量}',
    r'% \changes{v3.1e}{2026/01/03}{设置参考文献列表中的作者是否全大写和最大显示数量}',
    r'% \changes{v3.1e}{2026/01/03}{设置参考文献列表中的作者是否全大写和最大显示数量}',
])
PENDING = r'% \changes{v3.2b}{0000/00/00}{修正 \cs{emultiline} 的{长字段}。}'


def history():
    return {'schema': 1, 'repository': 'hithesis/hithesis', 'releases': []}


class DevDateHistoryTests(unittest.TestCase):
    def test_preflight_only_never_starts_a_build(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'output'
            with patch.dict('os.environ', {'PREFLIGHT_ONLY': 'true', 'GITHUB_OUTPUT': str(path)}), \
                    patch.object(dates.release, 'command') as command:
                dates.plan()
                command.assert_not_called()
            self.assertEqual(path.read_text(), 'build_required=false\n')

    def test_repeated_historical_dates_are_preserved(self):
        source = BASELINE + '\n' + PENDING
        dates.check(source, BASELINE, history())
        stamped, journal = dates.stamp(source, BASELINE, history(), '2026/10/25')
        self.assertEqual(stamped, BASELINE + '\n' + PENDING.replace('0000/00/00', '2026/10/25'))
        self.assertEqual(len(journal), 1)
        self.assertEqual(journal[0]['before'], '0000/00/00')
        self.assertEqual(journal[0]['after'], '2026/10/25')

    def test_changing_one_duplicate_to_another_historical_date_is_rejected(self):
        edited = BASELINE.replace('2026/01/07', '2026/01/03')
        with self.assertRaisesRegex(ValueError, 'Published historical date was edited'):
            dates.check(edited, BASELINE, history())

    def test_new_manual_date_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'New changes must use 0000/00/00'):
            dates.check(BASELINE + '\n' + PENDING.replace('0000/00/00', '2026/10/25'),
                BASELINE, history())

    def test_published_pending_date_uses_its_original_publication_date(self):
        version, _, text = dates.release.change_records(PENDING)[0]
        published = history()
        published['releases'] = [{'published_on': '2026-10-24', 'changes': [
            {'id': dates.release.change_id(version, text)}]}]
        stamped, journal = dates.stamp(BASELINE + '\n' + PENDING, BASELINE, published,
            '2026/10/25', published_only=True)
        self.assertEqual(stamped, BASELINE + '\n' + PENDING.replace('0000/00/00', '2026/10/24'))
        self.assertEqual(journal[0]['after'], '2026/10/24')

    def test_daily_stage_changes_versions_and_dates_in_one_traceable_commit(self):
        from test_dev_version import source
        original = source()
        baseline = r'% \changes{v3.2a}{2026/10/12}{Published.}'
        history_value = history()
        version_plan = {'version': 'v3.3a', 'source_commit': 'a' * 40,
            'source_sha256': hashlib.sha256(original.encode()).hexdigest()}
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / 'hithesis.dtx'
            path.write_text(original)
            committed = []
            calls = []
            def command(*args, **kwargs):
                calls.append(args)
                if 'commit' in args:
                    committed.append(True)
                return SimpleNamespace(stdout=('b' if committed else 'a') * 40 + '\n', returncode=0)
            with patch.object(dates, 'ROOT', root), patch.object(dates, 'context', return_value=(baseline, history_value)), \
                    patch.object(dates.versions, 'load_plan', return_value=version_plan), \
                    patch.object(dates.release, 'command', side_effect=command):
                dates.stage(None, root / 'journal.json')
            journal = json.loads((root / 'journal.json').read_text())
            self.assertEqual(journal['source_commit'], 'a' * 40)
            self.assertEqual(journal['date_commit'], 'b' * 40)
            self.assertEqual(journal['source_sha256'], hashlib.sha256(original.encode()).hexdigest())
            self.assertEqual(journal['dated_sha256'], hashlib.sha256(path.read_bytes()).hexdigest())
            self.assertEqual(dates.versions.source_version(path.read_text()), 'v3.3a')
            self.assertNotIn(r'\changes{v3.3a}{0000/00/00}', path.read_text())
            self.assertEqual(len(journal['version_updates']), 2)
            self.assertEqual(sum('commit' in call for call in calls), 1)


if __name__ == '__main__':
    unittest.main()
