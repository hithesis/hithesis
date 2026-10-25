"""Choose previews from today's changes and preserve all comparisons within two AI images."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('dev_previews', ROOT / 'scripts/dev-previews.py')
previews = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(previews)


class DailyPreviewTests(unittest.TestCase):
    def test_only_todays_notes_are_selected(self):
        notes = [{'change': '旧更新', 'title': '旧例子', 'preview': 'keywords'},
                 {'change': '今日更新', 'title': '新例子', 'code': [r'\begin{futureenv}', 'Text.', r'\end{futureenv}']}]
        cases, uncovered = previews.plan({'changes': [{'text': '今日更新'}]}, notes)
        self.assertEqual([case['id'] for case in cases], ['example-2'])
        self.assertIn(r'\begin{futureenv}', cases[0]['source'])
        self.assertIn(r'\ifcsname futureenv\endcsname', cases[0]['source'])
        self.assertEqual(uncovered, [])

    def test_no_example_is_recorded_instead_of_showing_old_unrelated_pictures(self):
        info = {'changes': [{'text': '仅调整内部构建流程。'}],
                'version_plan': {'official_release': {'tag': 'v3.2a'}}}
        with tempfile.TemporaryDirectory() as folder, patch.object(previews, 'baseline') as baseline:
            result = previews.build(info, Path(folder) / 'previews')
        baseline.assert_not_called()
        self.assertEqual(result['comparisons'], [])
        self.assertEqual(result['coverage'][0]['status'], 'no-reviewed-example')
        self.assertEqual(len(result['evidence']), 1)

    def test_this_release_covers_all_five_new_features(self):
        import json
        notes = json.loads(previews.NOTES.read_text())
        changes = [{'text': note['change']} for note in notes[-5:]]
        cases, uncovered = previews.plan({'changes': changes})
        self.assertEqual([case['id'] for case in cases],
                         ['pdf-properties', 'beijing-date', 'url', 'example-11', 'example-12'])
        self.assertEqual(uncovered, [])

    def test_unknown_fixture_is_an_error(self):
        with self.assertRaisesRegex(ValueError, 'Unknown reviewed preview fixture'):
            previews.plan({'changes': [{'text': 'Update'}]},
                          [{'change': 'Update', 'title': 'Update', 'preview': 'typo'}])

    def test_preamble_and_caption_fragments_get_their_document_context(self):
        source = previews.snippet([r'\hitsetup{keywords-hanging=true}'])
        self.assertLess(source.index(r'\hitsetup'), source.index(r'\begin{document}'))
        source = previews.snippet([r'\caption{中文}[English]'])
        self.assertIn(r'\begin{figure}', source)
        self.assertIn(r'\caption{中文}[English]', source)

    def test_contact_sheets_include_every_case(self):
        from PIL import Image
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            comparisons = []
            for index in range(5):
                image = folder / f'case-{index}.png'
                Image.new('RGB', (160, 80), (index * 20, 100, 150)).save(image)
                comparisons.append({'id': f'case-{index}', 'image': str(image)})
            previews.contact_sheets(comparisons, folder)
            self.assertEqual(len({c['ai_image'] for c in comparisons}), 2)
            self.assertTrue(all(Path(c['ai_image']).is_file() for c in comparisons))


if __name__ == '__main__':
    unittest.main()
