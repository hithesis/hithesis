"""Public update notes show practical changes and usage, not development bookkeeping."""
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('dev_report', ROOT / 'scripts/dev-report.py')
report = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(report)


def info(changes):
    return {'label': 'v3.3a-dev.1025', 'published_on': '2026-10-25', 'changes': changes,
            'commit': 'a' * 40, 'source_commit': 'b' * 40,
            'release_url': 'https://hithesis.site/dev-builds/example/',
            'run_url': 'https://github.com/hithesis/hithesis/actions/runs/123',
            'version_plan': {'minor_ceiling': '3.3', 'official_release': {'tag': 'v3.2a'}}}


class PublicReportTests(unittest.TestCase):
    def test_keywords_note_tells_existing_users_how_to_keep_their_layout(self):
        text = '增加 keywords-hanging 开关，关键词续行默认不再悬挂。'
        markdown = report.contents(info([{'text': text, 'tex': text}]), [])
        self.assertIn('旧论文先检查关键词对齐', markdown)
        self.assertIn(r'\hitsetup{keywords-hanging=true}', markdown)
        self.assertIn('```latex', markdown)

    def test_public_report_does_not_dump_commit_subjects_ci_or_version_algorithm(self):
        data = info([{'text': '修复封面日期的显示。'}])
        commit = {'sha': 'c' * 40, 'subject': 'ci: rewrite release pipeline',
                  'body': 'ci: rewrite release pipeline\n\nValidation: internal tests passed'}
        markdown = report.contents(data, [commit])
        for internal in [data['commit'], data['source_commit'], data['run_url'], 'ci: rewrite',
                         'Validation:', '第二位', '正式基准', 'Compatibility declaration']:
            self.assertNotIn(internal, markdown)
        self.assertIn('修复封面日期的显示', markdown)

    def test_explicit_public_footer_is_used_without_private_validation_details(self):
        commit = {'body': 'ci: update publisher\n\nRelease-Notes: 开发版更新会附带可下载的说明 PDF。\nValidation: unit tests passed'}
        markdown = report.contents(info([]), [commit])
        self.assertIn('开发版更新会附带可下载的说明 PDF', markdown)
        self.assertNotIn('unit tests', markdown)

    def test_preview_does_not_link_to_a_nonexistent_release(self):
        data = info([{'text': '更新封面。'}]) | {'preview': True}
        markdown = report.contents(data, [])
        self.assertIn('预览稿，尚未发布', markdown)
        self.assertNotIn(data['release_url'], markdown)

    def test_all_authored_notes_match_actual_change_records(self):
        from test_dev_dates import dates
        source_texts = {entry['text'] for entry in dates.spans((ROOT / 'hithesis.dtx').read_text())}
        notes = json.loads(report.NOTES.read_text())
        self.assertEqual(len(notes), len({note['change'] for note in notes}))
        for note in notes:
            self.assertIn(note['change'], source_texts)
            self.assertTrue(note['title'] and note['text'])


if __name__ == '__main__':
    unittest.main()
