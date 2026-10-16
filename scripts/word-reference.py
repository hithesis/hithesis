#!/usr/bin/env python3
"""Prepare content-aligned Word references from the approved layout-normalized inputs.

The external DOCX inputs are never overwritten. This tool deliberately supports
the doctor/bachelor sample content, not arbitrary TeX-to-Word conversion.
"""
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[1]
W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
NS = {'w': W}
ET.register_namespace('w', W)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def element(tag, **attrs):
    return ET.Element('{' + W + '}' + tag, {'{' + W + '}' + k: str(v) for k, v in attrs.items()})


def text(node):
    return ''.join(n.text or '' for n in node.findall('.//w:t', NS))


def compact(value):
    return re.sub(r'[\s\u200b]+', '', value)


def serialize(node, original):
    opening = re.search(rb'<[\w]+:[\w]+\b[^>]*>', original).group().decode()
    namespaces = dict(re.findall(r'xmlns:([\w]+)="([^"]+)"', opening))
    for prefix, uri in namespaces.items():
        if not re.fullmatch(r'ns\d+', prefix):
            ET.register_namespace(prefix, uri)
    result = ET.tostring(node, encoding='unicode')
    extra = ' '.join(f'xmlns:{p}="{u}"' for p, u in namespaces.items() if f'xmlns:{p}=' not in result)
    if extra:
        result = result.replace('>', ' ' + extra + '>', 1)
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n' + result).encode()


def group(source, offset):
    if source[offset] != '{':
        raise ValueError('Expected a braced TeX value')
    depth = 1
    for i in range(offset + 1, len(source)):
        if source[i] in '{}' and (i == 0 or source[i - 1] != '\\'):
            depth += 1 if source[i] == '{' else -1
            if depth == 0:
                return source[offset + 1:i], i + 1
    raise ValueError('Unclosed TeX value')


def value(source, key):
    match = re.search(r'(?<![\w-])' + re.escape(key) + r'\s*=\s*(\{)', source)
    if not match:
        raise ValueError('Missing sample key: ' + key)
    return group(source, match.start(1))[0]


def plain(source):
    source = re.sub(r'(?<!\\)%[^\n]*', '', source).strip()
    for old, new in [(r'\%', '%'), (r'\&', '&'), (r'\_', '_'), ('~', ' ')]:
        source = source.replace(old, new)
    if '\\' in source or re.search(r'[{}<>]', source):
        raise ValueError('Unsupported markup in sample reference text: ' + source[:100])
    return re.sub(r'\s+', ' ', source).strip()


def paragraphs(source):
    return [plain(p) for p in re.split(r'\n\s*\n', source.strip()) if p.strip()]


def content_profile(repo, degree):
    sample = repo / 'tests/sample'
    main = (sample / degree / 'main.tex').read_text()
    abstract = (sample / 'doctor/abstract.tex').read_text()
    conclusion = (sample / 'doctor/conclusion.tex').read_text()
    terms = (repo / 'src/config/hit-terms.dtx').read_text()
    title = plain(value(main, 'title'))
    bodies = re.findall(r'\\begin\{abstract\}(\[lang=en\])?\s*(.*?)\\end\{abstract\}', abstract, re.S)
    abstracts = {'en' if lang else 'zh': paragraphs(body) for lang, body in bodies}
    con = re.search(r'\\begin\{conclusions\}\s*(.*?)\\end\{conclusions\}', conclusion, re.S)
    if not con or len(abstracts) != 2:
        raise ValueError('Unexpected sample abstract/conclusion structure')
    # These sample keys intentionally contain plain comma-separated keyword lists.
    km = re.search(r'keywords\s*=\s*(\{)', main)
    zh_keys, end = group(main, km.start(1))
    em = re.match(r'\s*\[\s*(\{)', main[end:])
    if not em:
        raise ValueError('Expected grouped English sample keywords')
    en_keys, _ = group(main, end + em.start(1))
    suffix = '-bachelor' if degree == 'bachelor' else ''
    statement = value(terms, 'statement-text' + suffix).replace('<title-flat-zh>', title)
    auth = value(terms, 'authorization-text' + suffix)
    declaration = {
        'statement': plain(statement),
        'authorization': [plain(p) for p in auth.split(r'\par')],
        'statement_heading': plain(value(terms, 'statement-bachelor' if suffix else 'statement')),
        'authorization_heading': plain(value(terms, 'authorization' + suffix)),
    }
    if suffix:
        declaration['title_lines'] = [plain(value(terms, 'title-line-one-bachelor')), plain(value(terms, 'title-line-two-bachelor'))]
    paths = ['tests/sample/' + degree + '/main.tex', 'tests/sample/doctor/abstract.tex',
             'tests/sample/doctor/conclusion.tex', 'src/config/hit-terms.dtx',
             'src/config/hit-layout.dtx', 'src/pages/hit-final-abstract.dtx',
             'src/pages/hit-final-declarations.dtx']
    if degree == 'bachelor':
        for name in ('abstract', 'conclusion'):
            path = sample / 'bachelor' / (name + '.tex')
            if re.sub(r'(?<!\\)%[^\n]*', '', path.read_text()).strip() != r'\input{../doctor/' + name + '}':
                raise ValueError('Bachelor sample no longer shares doctor ' + name)
            paths.append('tests/sample/bachelor/' + name + '.tex')
    return {'degree': degree, 'title': title, 'abstracts': abstracts,
            'keywords': {'zh': '；'.join(plain(k) for k in zh_keys.split(',')), 'en': ', '.join(plain(k) for k in en_keys.split(','))},
            'conclusion': paragraphs(con.group(1)), 'declaration': declaration,
            'latex_sources': {p: digest(repo / p) for p in paths}}


def font(size=12, asian='宋体', bold=False):
    node = element('rPr')
    # Ambiguous characters such as U+2026 follow the sample's CJK font, including
    # the standalone ellipsis paragraph at the end of the English abstract.
    node.append(element('rFonts', ascii='Times New Roman', hAnsi='Times New Roman', eastAsia=asian, hint='eastAsia'))
    if bold:
        node.append(element('b'))
    node.append(element('kern', val=32767))
    node.extend([element('sz', val=round(size * 2)), element('szCs', val=round(size * 2))])
    return node


def run(value, properties=None):
    node = element('r')
    node.append(deepcopy(properties) if properties is not None else font())
    t = element('t')
    t.set('{http://www.w3.org/XML/1998/namespace}space', 'preserve')
    t.text = value
    node.append(t)
    return node


def body_paragraph(value='', english=False, blank=False, keyword=False):
    p = element('p'); pr = element('pPr')
    # Normal and abstract-en both inherit adjustRightInd=false in hit-layout.dtx.
    pr.extend([element('adjustRightInd', val=0), element('snapToGrid', val=0),
               element('spacing', before=0, after=0, line=300, lineRule='auto'),
               element('ind', firstLineChars=0 if blank or keyword else 200, firstLine=0 if blank or keyword else 498),
               element('jc', val='both'), font()])
    p.append(pr)
    if keyword:
        label = 'Keywords' if english else '关键词：'
        p.append(run(label, font(asian='宋体' if english else '黑体', bold=english)))
        p.append(run(('：' if english else '') + value))
    elif value:
        p.append(run(value))
    return p


def replace_text(p, value):
    if p.find('.//w:fldChar', NS) is not None or p.find('.//w:drawing', NS) is not None:
        raise ValueError('Refuse to replace fields/drawings as plain text')
    exemplar = next((r.find('w:rPr', NS) for r in p.findall('w:r', NS) if text(r).strip()), None)
    starts = [deepcopy(n) for n in p.findall('.//w:bookmarkStart', NS)]
    ends = [deepcopy(n) for n in p.findall('.//w:bookmarkEnd', NS)]
    for n in list(p):
        if n.tag != '{' + W + '}pPr':
            p.remove(n)
    replacement = run(value, exemplar)
    if exemplar is None:
        replacement.remove(replacement.find('w:rPr', NS))
    p.extend(starts); p.append(replacement); p.extend(ends)


def replace_region(parent, old, new):
    """Replace plain paragraph content while retaining section and bookmark identities."""
    if any(n.tag != '{' + W + '}p' or n.find('w:pPr/w:sectPr', NS) is not None for n in old):
        raise ValueError('Content replacement must not delete a table or section boundary')
    if not new:
        raise ValueError('Replacement must retain a bookmark target')
    starts = [deepcopy(n) for p in old for n in p.findall('.//w:bookmarkStart', NS)]
    ends = [deepcopy(n) for p in old for n in p.findall('.//w:bookmarkEnd', NS)]
    for n in starts:
        new[0].insert(1 if new[0].find('w:pPr', NS) is not None else 0, n)
    new[-1].extend(ends)
    at = list(parent).index(old[0])
    for n in old:
        parent.remove(n)
    for i, n in enumerate(new, at):
        parent.insert(i, n)


def is_heading(p):
    style = p.find('w:pPr/w:pStyle', NS)
    return style is not None and style.get('{' + W + '}val') == '1'


def abstract_content(root, profile, language):
    parent = root.find('w:body', NS); children = list(parent)
    wanted = 'Abstract' if language == 'en' else '摘要'
    start = next(i for i, p in enumerate(children) if compact(text(p)) == wanted and is_heading(p))
    finish = next(i for i, p in enumerate(children[start + 1:], start + 1) if is_heading(p) and text(p).strip())
    segment = children[start + 1:finish]
    # The final empty paragraph holds this section's page/header/footer settings.
    boundary = next(i for i, p in enumerate(segment) if p.find('w:pPr/w:sectPr', NS) is not None)
    old = segment[:boundary]
    if not old:
        raise ValueError('Missing abstract body')
    new = [body_paragraph(t, english=language == 'en') for t in profile['abstracts'][language]]
    new += [body_paragraph(blank=True, english=language == 'en'),
            body_paragraph(profile['keywords'][language], english=language == 'en', keyword=True)]
    replace_region(parent, old, new)
    return {'language': language, 'body_paragraphs': len(profile['abstracts'][language]), 'keyword_blank_paragraphs': 1}


def declaration_content(root, profile):
    parent = root.find('w:body', NS); children = list(parent)
    start = next(i for i, p in enumerate(children) if is_heading(p) and '哈尔滨工业大学' in text(p)
                 and ('本科毕业论文' in text(p) if profile['degree'] == 'bachelor' else '原创性声明' in compact(text(p))))
    end = next((i for i, p in enumerate(children[start + 1:], start + 1) if is_heading(p) and compact(text(p)) == '致谢'), len(children) - 1)
    block = children[start:end]; cfg = profile['declaration']
    conclusion = next(i for i, p in enumerate(children) if is_heading(p) and compact(text(p)) == '结论')
    body_grid = next(p.find('w:pPr/w:sectPr/w:docGrid', NS) for p in children[conclusion:]
                     if p.find('w:pPr/w:sectPr/w:docGrid', NS) is not None)
    grids_changed = 0
    for p in block:
        section = p.find('w:pPr/w:sectPr', NS)
        if section is not None:
            old_grid = section.find('w:docGrid', NS)
            if old_grid is None:
                raise ValueError('Missing declaration document grid')
            section.remove(old_grid); section.append(deepcopy(body_grid))
            grids_changed += 1
    if not grids_changed:
        raise ValueError('Missing declaration section boundary')
    statement = next(p for p in block if text(p).startswith('本人郑重声明'))
    use_head = next(p for p in block if not is_heading(p) and compact(text(p)).endswith('使用权限') and '哈尔滨' not in text(p))
    statement_head = next(p for p in block if compact(text(p)).endswith('原创性声明') and not is_heading(p))
    # Keep existing signature, blank-paragraph and heading geometry; update body runs.
    for old, value in [(statement, cfg['statement'])]:
        fresh = body_paragraph(value)
        replace_region(parent, [old], [fresh])
    replace_text(statement_head, cfg['statement_heading'])
    replace_text(use_head, cfg['authorization_heading'])
    auth = [p for p in block if text(p).startswith(('本科毕业论文是', '学位论文是', '（1）学校', '保密论文在', '本人知悉'))]
    if len(auth) != 4:
        raise ValueError('Expected four authorization paragraphs')
    for old, value in zip(auth, cfg['authorization']):
        replace_region(parent, [old], [body_paragraph(value)])
    if profile['degree'] == 'bachelor':
        replace_text(children[start], cfg['title_lines'][0])
        replace_text(children[start + 1], cfg['title_lines'][1])
        # Update only visible title text in the Chinese TOC, retaining its live fields.
        for p in children[:start]:
            if '哈尔滨工业大学本科毕业论文原创性声明和使用权限' in compact(text(p)):
                for t in p.findall('.//w:t', NS):
                    if t.text and '本科毕业论文' in t.text:
                        t.text = t.text.replace('本科毕业论文', '本科毕业论文（设计）')
    return {'statement_title_filled': True, 'authorization_paragraphs': 4,
            'bachelor_design_and_ai_text': profile['degree'] == 'bachelor',
            'document_grids_restored_from_body': grids_changed}


def relocate_toc_bookmark(root, heading, label):
    names = []
    for p in root.findall('w:body/w:p', NS):
        if compact(text(p)).startswith(label) and not is_heading(p):
            instructions = ''.join(n.text or '' for n in p.findall('.//w:instrText', NS))
            names += re.findall(r'PAGEREF\s+(\w+)', instructions)
            names += [n.get('{' + W + '}anchor') for n in p.findall('.//w:hyperlink', NS) if n.get('{' + W + '}anchor')]
    for name in dict.fromkeys(names):
        mark = next((n for n in root.findall('.//w:bookmarkStart', NS) if n.get('{' + W + '}name') == name), None)
        if mark is None:
            # The bachelor seed's conclusion was deleted, including this target.
            # Repair its existing TOC link using a fresh, document-unique ID.
            identifiers = [int(n.get('{' + W + '}id')) for n in root.findall('.//w:bookmarkStart', NS)]
            identifier = str(max(identifiers, default=-1) + 1)
            mark = element('bookmarkStart', id=identifier, name=name)
            end = element('bookmarkEnd', id=identifier)
        else:
            identifier = mark.get('{' + W + '}id')
            end = next(n for n in root.findall('.//w:bookmarkEnd', NS) if n.get('{' + W + '}id') == identifier)
        for p in root.iter():
            for node in list(p):
                if node is mark or node is end:
                    p.remove(node)
        heading.insert(1, mark); heading.append(end)
    return list(dict.fromkeys(names))


def conclusion_content(root, profile, heading_template):
    parent = root.find('w:body', NS); children = list(parent)
    ref = next(i for i, p in enumerate(children) if is_heading(p) and compact(text(p)) == '参考文献')
    existing = next((i for i, p in enumerate(children[:ref]) if is_heading(p) and compact(text(p)) == '结论'), None)
    new = [body_paragraph(t) for t in profile['conclusion']]
    if existing is not None:
        end = next(i for i, p in enumerate(children[existing + 1:ref], existing + 1) if p.find('w:pPr/w:sectPr', NS) is not None)
        replace_region(parent, children[existing + 1:end], new)
        return {'inserted': False, 'paragraphs': len(new)}
    # The bachelor seed retains the deleted conclusion's empty section before references.
    boundaries = [p for p in children[max(0, ref - 5):ref] if p.find('w:pPr/w:sectPr', NS) is not None]
    if len(boundaries) < 2:
        raise ValueError('Missing bachelor conclusion section boundaries')
    previous_end, conclusion_end = boundaries[0], boundaries[-1]
    heading = deepcopy(heading_template)
    for p in heading.iter():
        for n in list(p):
            if n.tag in ('{' + W + '}bookmarkStart', '{' + W + '}bookmarkEnd'):
                p.remove(n)
    replace_text(heading, '结  论')
    at = list(parent).index(previous_end) + 1
    for p in boundaries[1:-1]:
        for mark in p.findall('.//w:bookmarkStart', NS):
            heading.insert(1, deepcopy(mark))
        for mark in p.findall('.//w:bookmarkEnd', NS):
            heading.append(deepcopy(mark))
        parent.remove(p)
    section = conclusion_end.find('w:pPr/w:sectPr', NS)
    # The deleted bachelor conclusion left a 21.26bp character grid behind.
    # Restore the surrounding body's grid (12.4543bp), not its measured PDF x/y.
    old_grid = section.find('w:docGrid', NS)
    body_grid = previous_end.find('w:pPr/w:sectPr/w:docGrid', NS)
    if old_grid is None or body_grid is None:
        raise ValueError('Missing conclusion/body document grid')
    section.remove(old_grid)
    section.append(deepcopy(body_grid))
    kind = section.find('w:type', NS)
    if kind is None:
        kind = element('type')
        # sectPr: header/footer references precede the section type.
        at_type = sum(n.tag in ('{' + W + '}headerReference', '{' + W + '}footerReference') for n in section)
        section.insert(at_type, kind)
    kind.set('{' + W + '}val', 'nextPage')
    for i, p in enumerate([heading, *new], at):
        parent.insert(i, p)
    names = relocate_toc_bookmark(root, heading, '结论')
    return {'inserted': True, 'paragraphs': len(new), 'toc_bookmarks_relocated': names,
            'document_grid_restored_from_body': True}


def prepare(args):
    repo = args.repo.resolve(); out = args.output.resolve()
    source_spec = json.loads(args.sources_manifest.read_text())
    inputs = {}
    for degree, cfg in source_spec['documents'].items():
        p = args.input_dir / cfg['filename']
        if digest(p) != cfg['sha256']:
            raise ValueError('Unverified layout-normalized input: ' + str(p))
        with zipfile.ZipFile(p) as z:
            payload = {name: z.read(name) for name in z.namelist()}
        inputs[degree] = (p, payload, ET.fromstring(payload['word/document.xml']))
    doctor_root = inputs['doctor'][2]
    heading_template = next(p for p in doctor_root.findall('w:body/w:p', NS) if is_heading(p) and compact(text(p)) == '结论')
    if out.exists():
        raise FileExistsError('Reference output already exists: ' + str(out))
    prepared = []
    for degree, (source, payload, root) in inputs.items():
        original_marks = {n.get('{' + W + '}name') for n in root.findall('.//w:bookmarkStart', NS)}
        profile = content_profile(repo, degree)
        changes = {'abstracts': [abstract_content(root, profile, lang) for lang in ('zh', 'en')],
                   'conclusion': conclusion_content(root, profile, heading_template),
                   'declaration': declaration_content(root, profile)}
        assert original_marks <= {n.get('{' + W + '}name') for n in root.findall('.//w:bookmarkStart', NS)}
        payload['word/document.xml'] = serialize(root, payload['word/document.xml'])
        prepared.append((degree, source, payload, profile, changes))
    out.mkdir(parents=True, exist_ok=False)
    documents = []
    for degree, source, payload, profile, changes in prepared:
        name = degree + '-content'
        dest = out / (name + '.docx')
        with zipfile.ZipFile(dest, 'w', zipfile.ZIP_DEFLATED) as z:
            for member, data in payload.items():
                info = zipfile.ZipInfo(member, date_time=(1980, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                z.writestr(info, data)
        profile_file = out / (name + '-profile.json')
        profile_file.write_text(json.dumps(profile, ensure_ascii=False, indent=2) + '\n')
        documents.append({'degree': degree, 'name': name, 'file': dest.name, 'sha256': digest(dest),
                          'source': str(source.resolve()), 'source_sha256': digest(source),
                           'content_profile': profile_file.name, 'content_profile_sha256': digest(profile_file),
                           'changes': changes})
        print(degree, changes)
    manifest = {'schema': 1, 'kind': 'hithesis-content-aligned-word-inputs',
                'generator_sha256': digest(Path(__file__)),
                'seed_manifest_sha256': digest(args.sources_manifest), 'documents': documents,
                'coverage': ['zh/en abstract paragraphs and keyword blank', 'conclusion body', 'declaration text'],
                'retained_differences': ['instructional cover annotations', 'bibliography and publication entry wording', 'LaTeX math internals']}
    (out / 'inputs.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input-dir', type=Path, required=True, help='Approved layout-normalized Word inputs')
    p.add_argument('--output', type=Path, required=True, help='New immutable output directory')
    p.add_argument('--repo', type=Path, default=ROOT)
    p.add_argument('--sources-manifest', type=Path, default=ROOT / 'tests/reference/word-reference-sources.json')
    args = p.parse_args()
    prepare(args)


if __name__ == '__main__':
    main()
