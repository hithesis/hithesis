"""Reference generation/provenance tests without private Word files or a VM."""
from argparse import Namespace
from contextlib import redirect_stdout
from copy import deepcopy
import importlib.util
import io
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


word = load('word_reference', ROOT / 'scripts/word-reference.py')
checker = load('check_word_reference', ROOT / 'scripts/check-word-reference.py')


def paragraph(value='', heading=False):
    p = word.body_paragraph(value)
    if heading:
        p.find('w:pPr', word.NS).insert(0, word.element('pStyle', val=1))
    return p


def boundary(pitch=1861, continuous=False):
    p = paragraph()
    s = word.element('sectPr')
    if continuous:
        s.append(word.element('type', val='continuous'))
    s.append(word.element('docGrid', type='linesAndChars', linePitch=391, charSpace=pitch))
    p.find('w:pPr', word.NS).append(s)
    return p


def seed(degree):
    root = word.element('document'); body = word.element('body'); root.append(body)
    toc = paragraph('结论7'); link = word.element('hyperlink', anchor='_TocDeleted'); toc.append(link)
    body.append(toc)
    for label in ('摘  要', 'Abstract'):
        body.extend([paragraph(label, True), paragraph('Obsolete abstract'), boundary()])
    body.append(paragraph('第1章', True))
    table = word.element('tbl'); table.append(paragraph('Preserved table cell'))
    body.extend([table, boundary()])
    if degree == 'doctor':
        body.extend([paragraph('结  论', True), paragraph('Obsolete conclusion'), boundary()])
    else:
        body.extend([boundary(continuous=True), boundary(37928)])
    body.extend([paragraph('参考文献', True), paragraph('Preserved bibliography'), boundary()])
    body.append(paragraph('哈尔滨工业大学' + ('本科毕业论文' if degree == 'bachelor' else '原创性声明'), True))
    if degree == 'bachelor':
        body.append(paragraph('原创性声明和使用权限'))
    body.extend([paragraph('学位论文原创性声明'), paragraph('本人郑重声明：Old'),
                 paragraph('学位论文使用权限')])
    body.extend(paragraph(t) for t in ('学位论文是Old', '（1）学校Old', '保密论文在Old', '本人知悉Old'))
    body.extend([paragraph('作者签名：'), paragraph('导师签名：'), boundary(2752), paragraph('致谢', True)])
    mark = word.element('bookmarkStart', id=3, name='preserve_me')
    body[2].extend([mark, word.element('bookmarkEnd', id=3)])
    return root


class ReferenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name)
        documents = {}
        for degree in ('doctor', 'bachelor'):
            file = self.path / (degree + '.docx')
            with zipfile.ZipFile(file, 'w') as z:
                z.writestr('word/document.xml', ET.tostring(seed(degree)))
                z.writestr('word/media/opaque.bin', b'unchanged embedded content')
            documents[degree] = {'filename': file.name, 'sha256': word.digest(file)}
        self.manifest = self.path / 'sources.json'
        self.manifest.write_text(json.dumps({'documents': documents}))

    def prepare(self, name='prepared'):
        args = Namespace(repo=ROOT, input_dir=self.path, sources_manifest=self.manifest, output=self.path / name)
        with redirect_stdout(io.StringIO()):
            word.prepare(args)
        return args.output

    def test_same_inputs_produce_byte_identical_docx(self):
        a, b = self.prepare('one'), self.prepare('two')
        for degree in ('doctor', 'bachelor'):
            self.assertEqual((a / (degree + '-content.docx')).read_bytes(), (b / (degree + '-content.docx')).read_bytes())

    def test_tampered_seed_is_rejected_before_creating_output(self):
        with (self.path / 'bachelor.docx').open('ab') as f:
            f.write(b'tampered')
        with self.assertRaisesRegex(ValueError, 'Unverified'):
            self.prepare()
        self.assertFalse((self.path / 'prepared').exists())

    def test_existing_output_is_never_overwritten(self):
        out = self.prepare(); before = (out / 'inputs.json').read_bytes()
        with self.assertRaises(FileExistsError):
            self.prepare()
        self.assertEqual((out / 'inputs.json').read_bytes(), before)

    def test_generated_content_bookmarks_sections_and_opaque_parts(self):
        out = self.prepare()
        for degree in ('doctor', 'bachelor'):
            with zipfile.ZipFile(out / (degree + '-content.docx')) as z:
                root = ET.fromstring(z.read('word/document.xml'))
                self.assertEqual(z.read('word/media/opaque.bin'), b'unchanged embedded content')
            original = seed(degree)
            self.assertEqual(ET.tostring(root.find('.//w:tbl', word.NS)), ET.tostring(original.find('.//w:tbl', word.NS)))
            self.assertIn('Preserved bibliography', word.text(root))
            starts = root.findall('.//w:bookmarkStart', word.NS)
            self.assertIn('preserve_me', [n.get('{' + word.W + '}name') for n in starts])
            self.assertEqual(CounterIds(starts), CounterIds(root.findall('.//w:bookmarkEnd', word.NS)))
            self.assertEqual(len(CounterIds(starts)), len(starts))
            profile = json.loads((out / (degree + '-content-profile.json')).read_text())
            self.assertIn(profile['declaration']['statement'], word.text(root))
            for value in profile['conclusion']:
                self.assertIn(value, word.text(root))
            grids = root.findall('.//w:docGrid', word.NS)
            self.assertTrue(all(g.get('{' + word.W + '}charSpace') == '1861' for g in grids))
            if degree == 'bachelor':
                heading = next(p for p in root.findall('w:body/w:p', word.NS) if word.is_heading(p) and word.compact(word.text(p)) == '结论')
                self.assertEqual(heading.find('w:bookmarkStart', word.NS).get('{' + word.W + '}name'), '_TocDeleted')

    def test_new_body_uses_normal_right_indent_and_cjk_ellipsis(self):
        p = word.body_paragraph('……')
        self.assertEqual(p.find('w:pPr/w:adjustRightInd', word.NS).get('{' + word.W + '}val'), '0')
        self.assertEqual(p.find('w:r/w:rPr/w:rFonts', word.NS).get('{' + word.W + '}hint'), 'eastAsia')

    def test_profile_tracks_current_bachelor_design_and_ai_terms(self):
        p = word.content_profile(ROOT, 'bachelor')
        self.assertIn('AI', p['declaration']['statement'])
        self.assertIn('（设计）', p['declaration']['authorization_heading'])
        self.assertIn('tests/sample/bachelor/conclusion.tex', p['latex_sources'])
        self.assertEqual(len(p['abstracts']['zh']), 4)

    def test_unsupported_tex_fails_loudly(self):
        with self.assertRaises(ValueError):
            word.plain(r'Unsupported \textbf{bold}')

    def test_region_replacement_refuses_section_deletion(self):
        parent = word.element('body'); p = boundary(); parent.append(p)
        with self.assertRaises(ValueError):
            word.replace_region(parent, [p], [paragraph('replacement')])

    def test_late_content_error_does_not_leave_partial_output(self):
        original = word.content_profile
        def fail(repo, degree):
            if degree == 'bachelor':
                raise ValueError('simulated source change')
            return original(repo, degree)
        with patch.object(word, 'content_profile', side_effect=fail), self.assertRaises(ValueError):
            self.prepare()
        self.assertFalse((self.path / 'prepared').exists())

    def bundle(self):
        prepared = self.prepare()
        exported = self.path / 'exported'; exported.mkdir()
        repo = self.path / 'repo'; repo.mkdir()
        inputs = checker.read_json(prepared / 'inputs.json')
        paths = {'scripts/word-reference.py', 'scripts/export-word-reference.py', 'tests/reference/word-fonts.json'}
        for d in inputs['documents']:
            paths.update(checker.read_json(prepared / d['content_profile'])['latex_sources'])
        for path in paths:
            dest = repo / path; dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / path, dest)
        shutil.copy2(self.manifest, repo / 'tests/reference/word-reference-sources.json')
        fonts = {'files': checker.read_json(repo / 'tests/reference/word-fonts.json')['files'],
                 'source_record_sha256': checker.digest(repo / 'tests/reference/word-fonts.json')}
        (exported / 'fonts.json').write_text(json.dumps(fonts))
        entries = []
        for d in inputs['documents']:
            pdf = exported / (d['name'] + '.pdf'); pdf.write_bytes(b'synthetic PDF bytes for integrity test only')
            entries.append({'name': d['name'], 'input_sha256': d['sha256'], 'pdf_sha256': checker.digest(pdf), 'pages': 1})
        report = {'kind': 'actual-windows-word-com-export', 'inputs': entries,
                  'input_manifest_sha256': checker.digest(prepared / 'inputs.json'),
                  'font_record_sha256': checker.digest(exported / 'fonts.json'),
                  'exporter_sha256': checker.digest(repo / 'scripts/export-word-reference.py')}
        (exported / 'verified-export.json').write_text(json.dumps(report))
        return prepared, exported, repo

    def test_provenance_rejects_modified_docx_and_profile(self):
        prepared, exported, repo = self.bundle()
        self.assertEqual(len(checker.verified_bundle(prepared, exported, repo)[0]['documents']), 2)
        profile = prepared / 'bachelor-content-profile.json'
        original = profile.read_bytes()
        profile.write_bytes(original.replace(b'porous graphite', b'changed keyword'))
        with self.assertRaisesRegex(ValueError, 'Provenance hash mismatch'):
            checker.verified_bundle(prepared, exported, repo)
        profile.write_bytes(original)
        with (prepared / 'doctor-content.docx').open('ab') as f:
            f.write(b'corrupted')
        with self.assertRaisesRegex(ValueError, 'Provenance hash mismatch'):
            checker.verified_bundle(prepared, exported, repo)

    def test_provenance_rejects_changed_pdf_and_missing_export(self):
        prepared, exported, repo = self.bundle()
        pdf = exported / 'doctor-content.pdf'; original = pdf.read_bytes(); pdf.write_bytes(b'wrong PDF')
        with self.assertRaisesRegex(ValueError, 'Provenance hash mismatch'):
            checker.verified_bundle(prepared, exported, repo)
        pdf.write_bytes(original)
        path = exported / 'verified-export.json'; report = checker.read_json(path); report['inputs'].pop()
        path.write_text(json.dumps(report))
        with self.assertRaisesRegex(ValueError, 'duplicate or missing'):
            checker.verified_bundle(prepared, exported, repo)


def CounterIds(nodes):
    from collections import Counter
    return Counter(n.get('{' + word.W + '}id') for n in nodes)


class GateTests(unittest.TestCase):
    def rows(self, *texts):
        return [{'page': 1, 'line': i + 1, 'y': 120 + 20 * i, 'x': 85, 'text': t} for i, t in enumerate(texts)]

    def test_only_unique_full_lines_count(self):
        rows = self.rows('First unique table', 'Repeated header', 'Unique continuation', 'Repeated header', 'p')
        result = checker.evaluate(rows, deepcopy(rows), 3)
        self.assertEqual(result['gate']['actual'], 2)
        self.assertFalse(result['gate']['passed'])

    def test_real_geometry_regression_fails_even_with_all_text_matched(self):
        rows = self.rows('Unique paragraph here'); actual = deepcopy(rows); actual[0]['y'] += 2
        self.assertFalse(checker.evaluate(rows, actual, 1)['gate']['passed'])

    def test_hash_member_paths_cannot_escape_bundle(self):
        with self.assertRaises(ValueError):
            checker.member(Path('/tmp/example'), '../outside.pdf')

    def test_fixture_serialization_retains_blank_pages(self):
        value = checker.fixture_text([[], [(120.1, 85.104, 'Unique text')]], 'actual.pdf')
        self.assertIn('PAGE\t1\nPAGE\t2\nLINE\t120.10\t85.104\tUnique text', value)


if __name__ == '__main__':
    unittest.main()
