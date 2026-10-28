"""Compile the reviewed examples for this release and record what actually changed."""
from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tarfile
import textwrap

ROOT = Path(__file__).resolve().parents[1]
NOTES = ROOT / 'release-notes/notes.json'
MAX_CASES = 12

KEYWORDS = r'''\documentclass[fontset=fandol,type=doctor]{hithesisbook}
\begin{document}\ExplSyntaxOn\group_begin:\hsize=170bp
\cs_if_exist:NTF\__hit_keywords_typeset:nn{\__hit_keywords_typeset:nn}{\use:c{hit@put@keywords}}
{Keywords:~}{Alpha~Beta~Gamma~Delta~Epsilon~Zeta~Eta~Theta~Iota~Kappa~Lambda~Mu~Nu~Xi~Omicron~Pi~Rho~Sigma~Tau~Upsilon~Phi~Chi~Psi~Omega}
\group_end:\ExplSyntaxOff\end{document}'''

ENGLISH = r'''\documentclass[fontset=fandol,type=doctor]{hithesisbook}
\hitsetup{etitle={Short title},eauthor={Candidate Name},esupervisor={Professor Name},
eassosupervisor={Associate Example},ecosupervisor={Industry Example},edate={June, 2026},
esubject={Advanced Mechanical Engineering and Intelligent Manufacturing Technologies with International Collaborative Research},
eaffil={School of Advanced Mechanical Engineering and Intelligent Manufacturing Research with International Collaborative Studies}}
\begin{document}\ExplSyntaxOn
\cs_if_exist:NTF\__hit_engcover:{\__hit_engcover:}{\use:c{hit@engcover}}
\ExplSyntaxOff\end{document}'''


def environment(epoch='1700000000'):
    clean = {k: v for k, v in os.environ.items() if k not in ('DEV_REPORT_API_KEY', 'GH_TOKEN', 'GITHUB_TOKEN')}
    return clean | {'TEXINPUTS': '.:', 'TEXMFLOCAL': str(ROOT / 'build/dependencies/texmf'),
                         'SOURCE_DATE_EPOCH': str(epoch), 'FORCE_SOURCE_DATE': '1', 'TZ': 'UTC'}


def baseline(ref, folder):
    archive = subprocess.check_output(['git', '-c', f'safe.directory={ROOT}', 'archive', ref,
                                      'hithesis.dtx', 'hithesis.ins'], cwd=ROOT)
    folder.mkdir()
    with tarfile.open(fileobj=io.BytesIO(archive)) as package:
        package.extractall(folder, filter='data')
    for name in ('modules', 'examples/hitbook/chinese/modules', 'examples/hitbook/english/modules',
                 'examples/hitart/reports/modules', 'examples/hitart/reportplus/modules'):
        (folder / name).mkdir(parents=True, exist_ok=True)
    with (folder / 'extract.log').open('w') as output:
        subprocess.run(['xetex', '-no-shell-escape', '-interaction=nonstopmode', '-halt-on-error', 'hithesis.ins'],
                       cwd=folder, env=environment(), stdout=output, stderr=subprocess.STDOUT, check=True, timeout=120)


def compile_case(runtime, source, folder, epoch='1700000000', allow_failure=False):
    folder.mkdir()
    for pattern in ('*.cls', '*.cfg', '*.sty', '*.bst', '*.ist', '*.eps'):
        for path in runtime.glob(pattern):
            shutil.copy2(path, folder / path.name)
    if (runtime / 'modules').is_dir():
        shutil.copytree(runtime / 'modules', folder / 'modules')
    (folder / 'main.tex').write_text(source)
    with (folder / 'compile.log').open('w') as output:
        for _ in range(2):
            result = subprocess.run(['xelatex', '-no-shell-escape', '-interaction=nonstopmode', '-halt-on-error', '-recorder', 'main.tex'],
                           cwd=folder, env=environment(epoch), stdout=output, stderr=subprocess.STDOUT, timeout=120)
            if result.returncode:
                if allow_failure:
                    return None
                raise RuntimeError('Current preview failed to compile: ' + str(folder / 'compile.log'))
    if 'Missing character:' in (folder / 'main.log').read_text():
        raise ValueError('Missing glyph in controlled comparison')
    return folder / 'main.pdf'


def document(body, preamble='', requires=()):
    # Missing new commands get an explicit diagnostic in the old rendering.
    # The same guarded source is compiled with both runtimes.
    for name in reversed(requires):
        if not re.fullmatch(r'[A-Za-z][A-Za-z0-9@:*_-]*', name):
            raise ValueError('Invalid command name in reviewed preview')
        shown = name.replace('_', r'\_')
        body = ('\\ifcsname ' + name + '\\endcsname\n' + body + '\n\\else\n' +
                '\\typeout{HIT-PREVIEW-UNSUPPORTED:' + name + '}\n' +
                r'\noindent This template does not define \texttt{' + shown + r'}.\par' + '\n\\fi\n')
    return ('\\documentclass[fontset=fandol,type=doctor]{hithesisbook}\n' + preamble +
            '\n\\begin{document}\n' + body + '\n\\end{document}\n')


def snippet(code):
    source = '\n'.join(code)
    environments = list(dict.fromkeys(re.findall(r'\\begin\{([A-Za-z][A-Za-z0-9*_-]*)\}', source)))
    first = re.match(r'\s*\\([A-Za-z]+)', source)
    command = first[1] if first else ''
    if not environments and command in ('hitsetup', 'hypersetup', 'usepackage', 'PassOptionsToPackage'):
        return document('Preview document.', preamble=source)
    if not environments and command == 'caption':
        source = '\\begin{figure}[htbp]\\centering\\rule{30mm}{8mm}\n' + source + '\n\\end{figure}'
    requires = environments or ([command] if command else [])
    return document(source, requires=requires)


def fixtures():
    return {
        'bachelor-capstone': (r'''\documentclass[fontset=fandol,type=bachelor,campus=harbin,bachelortype=capstone]{hithesisbook}
\hitsetup{ctitle={本科综合设计排版示例}}
\begin{document}\mainmatter
\chapter{本科综合设计}
页眉和声明中的名称随本科类型切换。
\backmatter\authorization\end{document}''', 'layout', '1700000000'),
        'keywords': (KEYWORDS, 'layout', '1700000000'),
        'english-cover': (ENGLISH, 'layout', '1700000000'),
        'pdf-properties': (document('PDF document properties.', preamble=
            r'\hitsetup{ctitle={文档属性示例},cauthor={张三},ckeywords={alpha,beta}}'),
            'pdf-properties', '1700000000'),
        'beijing-date': (document(r'\noindent\today\par'), 'layout',
            str(int(datetime(2026, 10, 25, 18, tzinfo=timezone.utc).timestamp()))),
        'url': (document(r'''\typeout{HIT-PREVIEW-VALUE:url-body=\the\Urlmuskip}
\noindent\begin{minipage}{55mm}
\url{https://example.org/research/long_path_segments/one/two/three?key=value&next=item#anchor}
\end{minipage}
\begin{thebibliography}{1}
\typeout{HIT-PREVIEW-VALUE:url-bibliography=\the\Urlmuskip}
\bibitem{web} \url{https://example.org/research/one/two/three?key=value&next=item}.
\end{thebibliography}'''), 'layout', '1700000000'),
    }


def plan(info, notes=None):
    normalize = lambda text: ' '.join(text.split())
    changes = {normalize(c.get('tex') or c['text']) for c in info['changes']}
    notes = json.loads(NOTES.read_text()) if notes is None else notes
    cases, uncovered, covered = [], [], set()
    known = fixtures()
    for index, note in enumerate(notes, 1):
        change = normalize(note['change'])
        if change not in changes:
            continue
        covered.add(change)
        selected = note.get('preview')
        identifier = selected or f'example-{index}'
        if selected:
            if selected not in known:
                raise ValueError('Unknown reviewed preview fixture: ' + str(selected))
            source, kind, epoch = known[selected]
        elif note.get('code'):
            source, kind, epoch = snippet(note['code']), 'layout', '1700000000'
        else:
            uncovered.append({'change': note['change'], 'status': 'no-reviewed-example'})
            continue
        cases.append({'id': identifier, 'title': note['title'], 'source': source,
                      'kind': kind, 'epoch': epoch, 'change': note['change']})
    uncovered += [{'change': text, 'status': 'no-reviewed-example'} for text in sorted(changes - covered)]
    if len(cases) > MAX_CASES:
        raise ValueError('Too many reviewed preview cases for one release')
    if len({case['id'] for case in cases}) != len(cases):
        raise ValueError('Duplicate preview fixture in this release')
    return cases, uncovered


def properties(path):
    from pypdf import PdfReader
    metadata = PdfReader(path).metadata or {}
    return {name: str(metadata.get('/' + name, '')) for name in ('Title', 'Author', 'Keywords')}


def compiler_error(log):
    lines = log.splitlines()
    start = next((i for i, line in enumerate(lines) if line.startswith('!')), max(0, len(lines) - 12))
    return '\n'.join(lines[start:start + 12])[:1600]


def pictures(before, after, destination, error=''):
    import pypdfium2 as pdfium
    from PIL import Image, ImageDraw, ImageChops
    images, counts = [], []
    for path in (before, after):
        if path is None:
            counts.append(0)
            images.append([])
            continue
        with pdfium.PdfDocument(path) as pdf:
            if len(pdf) > 12:
                raise ValueError('Reviewed preview exceeds twelve pages')
            counts.append(len(pdf))
            pages = []
            for page in pdf:
                pages.append(page.render(scale=1.4).to_pil().convert('RGB'))
                page.close()
            images.append(pages)
    changed = []
    for index in range(max(counts)):
        if index >= min(counts) or images[0][index].size != images[1][index].size or \
                ImageChops.difference(images[0][index], images[1][index]).getbbox() is not None:
            changed.append(index)
    if not changed:
        return counts, []
    rows = []
    # Show the first and last changed pages; record every changed page below.
    for index in dict.fromkeys((changed[0], changed[-1])):
        pair, bounds = [], []
        for side in range(2):
            image = images[side][index] if index < counts[side] else None
            pair.append(image)
            if image is not None:
                box = ImageChops.difference(image, Image.new('RGB', image.size, 'white')).getbbox()
                if box:
                    bounds.append(box)
        if not bounds:
            bounds = [(0, 0, 600, 80)]
        crop = (max(0, min(b[0] for b in bounds) - 8), max(0, min(b[1] for b in bounds) - 8),
                max(b[2] for b in bounds) + 8, max(b[3] for b in bounds) + 8)
        width, height = crop[2] - crop[0], crop[3] - crop[1]
        if error:
            width, height = max(width, 560), max(height, 240)
        row = Image.new('RGB', (2 * width + 24, height + 30), 'white')
        draw = ImageDraw.Draw(row)
        for side, image in enumerate(pair):
            x = side * (width + 24)
            label = ('BEFORE' if side == 0 else 'AFTER') + f' (page {index + 1}/{counts[side]})'
            if side == 0 and error:
                label = 'BEFORE - compilation failed (compiler log)'
            draw.text((x + 4, 5), label if image or (side == 0 and error) else label + ' - no page', fill='black')
            if image:
                row.paste(image.crop(crop), (x, 30))
            elif side == 0 and error:
                wrapped = '\n'.join(textwrap.fill(line, 85) for line in error.splitlines())
                draw.multiline_text((x + 4, 35), wrapped, fill='black', spacing=3)
        rows.append(row)
    combined = Image.new('RGB', (max(r.width for r in rows), sum(r.height for r in rows)), 'white')
    top = 0
    for row in rows:
        combined.paste(row, (0, top))
        top += row.height
    combined.save(destination)
    return counts, [index + 1 for index in changed]


def contact_sheets(comparisons, directory):
    from PIL import Image, ImageDraw
    # AI still receives at most two images. Each sheet contains several real
    # comparisons; the PDF uses the individual images at a readable size.
    for group in range(min(2, len(comparisons))):
        members = comparisons[group::2]
        rows = []
        for comparison in members:
            with Image.open(comparison['image']) as source:
                image = source.convert('RGB')
            image.thumbnail((1400, 2400))
            row = Image.new('RGB', (max(500, image.width), image.height + 30), 'white')
            ImageDraw.Draw(row).text((4, 5), 'comparison_id: ' + comparison['id'], fill='black')
            row.paste(image, (0, 30))
            rows.append(row)
        sheet = Image.new('RGB', (max(r.width for r in rows), sum(r.height for r in rows)), 'white')
        top = 0
        for row in rows:
            sheet.paste(row, (0, top))
            top += row.height
        sheet.thumbnail((1400, 6000))
        path = directory / f'ai-sheet-{group + 1}.png'
        sheet.save(path)
        for comparison in members:
            comparison['ai_image'] = str(path.resolve())


def build(info, directory):
    directory = Path(directory)
    directory.mkdir(exist_ok=False)
    cases, coverage = plan(info)
    reference = info.get('previous_source_commit') or info['version_plan']['official_release']['tag']
    old = directory / 'baseline'
    if cases:
        baseline(reference, old)
    comparisons, evidence = [], []
    for case in cases:
        name, source = case['id'], case['source']
        before_folder = directory / (name + '-before')
        before = compile_case(old, source, before_folder, case['epoch'], allow_failure=True)
        after = compile_case(ROOT, source, directory / (name + '-after'), case['epoch'])
        before_log = (before_folder / 'main.log').read_text()
        after_log = after.with_suffix('.log').read_text()
        unsupported = re.findall(r'HIT-PREVIEW-UNSUPPORTED:([^\n]+)', before_log)
        if 'HIT-PREVIEW-UNSUPPORTED:' in after_log:
            raise ValueError('Current template does not support its reviewed example: ' + name)
        image = directory / (name + '.png')
        error = compiler_error(before_log) if before is None else ''
        counts, changed_pages = pictures(before, after, image, error)
        record = {'id': name, 'change': case['change'], 'kind': case['kind'],
                  'status': 'changed' if changed_pages else 'no-visual-change',
                  'before_status': 'compile-error' if before is None else 'unsupported' if unsupported else 'compiled',
                  'unsupported_commands': unsupported, 'changed_pages': changed_pages,
                  'before_pages': counts[0], 'after_pages': counts[1],
                  'source_sha256': hashlib.sha256(source.encode()).hexdigest(),
                  'before_sha256': hashlib.sha256(before.read_bytes() if before else before_log.encode()).hexdigest(),
                  'after_sha256': hashlib.sha256(after.read_bytes()).hexdigest()}
        if error:
            record['before_error'], record['before_kind'] = error, 'compiler-log'
        if case['kind'] == 'pdf-properties':
            record['before_properties'], record['after_properties'] = properties(before) if before else {}, properties(after)
        values = lambda log: dict(re.findall(r'HIT-PREVIEW-VALUE:([a-z0-9-]+)=([^\n]+)', log))
        if values(before_log) or values(after_log):
            record['before_values'], record['after_values'] = values(before_log), values(after_log)
        coverage.append(record)
        evidence.append({'id': 'preview-' + name, 'text': json.dumps(record, ensure_ascii=False)})
        if changed_pages:
            comparisons.append({'id': name, 'title': case['title'], 'image': str(image.resolve()),
                                'layout': 'side-by-side', 'changed': True, 'before_status': record['before_status'],
                                'unsupported_commands': unsupported,
                                **{key: record[key] for key in ('before_pages', 'after_pages', 'before_sha256', 'after_sha256')}})
    for index, item in enumerate(coverage):
        if item['status'] == 'no-reviewed-example':
            evidence.append({'id': f'preview-uncovered-{index + 1}', 'text': json.dumps(item, ensure_ascii=False)})
    contact_sheets(comparisons, directory)
    result = {'baseline': reference, 'comparisons': comparisons, 'evidence': evidence, 'coverage': coverage}
    (directory / 'PREVIEW_EVIDENCE.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    return result
