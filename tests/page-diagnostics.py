"""Exercise ordering, duplicate ambiguity and missing content in PDF diagnostics."""
import importlib.util
import json
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('diagnostics', Path(__file__).resolve().parents[1] / 'scripts/diagnose-pages.py')
diagnostics = importlib.util.module_from_spec(spec)
spec.loader.exec_module(diagnostics)


def rows(*texts):
    return [{'page': i // 2 + 1, 'line': i % 2 + 1, 'y': 120 + i % 2 * 20,
             'x': 85, 'text': text} for i, text in enumerate(texts)]


class AlignmentTests(unittest.TestCase):
    def test_actual_continued_table_does_not_reuse_first_table_rows(self):
        path = Path(__file__).resolve().parent / 'reference/word-continuation-sequence.json'
        case = json.loads(path.read_text())
        report = diagnostics.align(case['reference'], case['actual'])
        repeated = [r for r in report['matches'] if r['reference']['text'].startswith('0.350.136')]
        # Word p13 is the first table; p15 is the long table's continuation.
        # The old nearest-page matcher reused the first table for the latter.
        self.assertEqual([(r['reference']['page'], r['actual']['page']) for r in repeated], [(13, 15), (15, 16)])
        self.assertTrue(all(r['ambiguous'] for r in repeated))
        indices = [r['actual_index'] for r in report['matches']]
        self.assertEqual(indices, sorted(set(indices)))

    def test_continuation_uses_later_occurrence_and_does_not_reuse_lines(self):
        reference = rows('Unique first table', 'Repeated header', 'Unique continuation', 'Repeated header', 'Unique ending')
        actual = rows('Unique first table', 'Repeated header', 'Extra first-table row', 'Unique continuation', 'Repeated header', 'Unique ending')
        result = diagnostics.align(reference, actual)
        pairs = [(r['reference_index'], r['actual_index']) for r in result['matches']]
        self.assertEqual(pairs, [(0, 0), (1, 1), (2, 3), (3, 4), (4, 5)])
        self.assertEqual(len({p[1] for p in pairs}), len(pairs))
        self.assertTrue(result['matches'][1]['ambiguous'])
        self.assertTrue(result['matches'][3]['ambiguous'])

    def test_extra_and_missing_content_do_not_force_wrong_pair(self):
        result = diagnostics.align(rows('First unique paragraph', 'Reference-only annotation', 'Last unique paragraph'),
                                   rows('First unique paragraph', 'Last unique paragraph'))
        self.assertEqual(result['unmatched_reference'][0]['text'], 'Reference-only annotation')
        self.assertEqual(result['summary']['unique_exact_matches'], 2)

    def test_coordinates_do_not_choose_duplicate_occurrences(self):
        reference = rows('First anchor', 'Repeated row', 'Second anchor', 'Repeated row')
        actual = rows('First anchor', 'Repeated row', 'Second anchor', 'Repeated row')
        actual[1]['y'], actual[3]['y'] = actual[3]['y'], actual[1]['y']
        pairs = diagnostics.align(reference, actual)['matches']
        self.assertEqual([(p['reference_index'], p['actual_index']) for p in pairs], [(i, i) for i in range(4)])

    def test_short_formula_fragments_are_not_anchors(self):
        result = diagnostics.align(rows('p', 's', 'Unique paragraph'), rows('s', 'p', 'Unique paragraph'))
        self.assertEqual(result['summary']['matched'], 1)

    def test_changed_line_ending_is_not_an_exact_match(self):
        result = diagnostics.align(rows('Same prefix but different ending'), rows('Same prefix but shorter'))
        self.assertEqual(result['matches'][0]['match'], 'prefix-only')
        self.assertEqual(result['summary']['unique_exact_matches'], 0)

    def test_one_reference_page_can_flow_across_actual_pages(self):
        reference = rows('First unique line', 'Second unique line', 'Third unique line')
        actual = rows('First unique line', 'Second unique line', 'Third unique line')
        for row in reference:
            row['page'] = 1
        result = diagnostics.align(reference, actual)
        self.assertEqual(result['page_map']['1'], {1: 2, 2: 1})

    def test_identical_text_beyond_tolerance_remains_a_real_difference(self):
        reference, actual = rows('A unique paragraph'), rows('A unique paragraph')
        actual[0]['y'] += 20
        result = diagnostics.align(reference, actual)
        self.assertEqual(result['matches'][0]['dy'], 20)
        self.assertFalse(result['matches'][0]['within_tolerance'])


if __name__ == '__main__':
    unittest.main()
