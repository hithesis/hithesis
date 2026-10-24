"""Render two maintainer-defined comparisons; never compile model-written code."""
import hashlib
import io
import os
from pathlib import Path
import shutil
import subprocess
import tarfile

ROOT = Path(__file__).resolve().parents[1]

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


def environment():
    clean = {k: v for k, v in os.environ.items() if k not in ('DEV_REPORT_API_KEY', 'GH_TOKEN', 'GITHUB_TOKEN')}
    return clean | {'TEXINPUTS': '.:', 'TEXMFLOCAL': str(ROOT / 'build/dependencies/texmf'),
                         'SOURCE_DATE_EPOCH': '1700000000', 'FORCE_SOURCE_DATE': '1'}


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


def compile_case(runtime, source, folder):
    folder.mkdir()
    for pattern in ('*.cls', '*.cfg', '*.sty', '*.bst', '*.ist', '*.eps'):
        for path in runtime.glob(pattern):
            shutil.copy2(path, folder / path.name)
    if (runtime / 'modules').is_dir():
        shutil.copytree(runtime / 'modules', folder / 'modules')
    (folder / 'main.tex').write_text(source)
    with (folder / 'compile.log').open('w') as output:
        for _ in range(2):
            subprocess.run(['xelatex', '-no-shell-escape', '-interaction=nonstopmode', '-halt-on-error', '-recorder', 'main.tex'],
                           cwd=folder, env=environment(), stdout=output, stderr=subprocess.STDOUT, check=True, timeout=120)
    if 'Missing character:' in (folder / 'main.log').read_text():
        raise ValueError('Missing glyph in controlled comparison')
    return folder / 'main.pdf'


def pictures(before, after, destination, crop_text):
    import pypdfium2 as pdfium
    from PIL import Image, ImageDraw, ImageChops
    images, counts, bounds = [], [], []
    for path in (before, after):
        with pdfium.PdfDocument(path) as pdf:
            counts.append(len(pdf))
            page = pdf[0]
            bitmap = page.render(scale=1.4).to_pil().convert('RGB')
            text = page.get_textpage()
            boxes = [text.get_charbox(i) for i in range(text.count_chars())
                     if text.get_text_range(i, 1).strip() and text.get_charbox(i)[1] > (110 if crop_text else 60)
                     and (crop_text or text.get_charbox(i)[3] < page.get_height() / 2)]
            bounds.append((max(0, min(b[0] for b in boxes) - 6), page.get_height() - max(b[3] for b in boxes) - 8,
                           min(page.get_width(), max(b[2] for b in boxes) + 6), page.get_height() - min(b[1] for b in boxes) + 8))
            images.append(bitmap)
            text.close()
            page.close()
    if crop_text:
        common = (min(b[0] for b in bounds), min(b[1] for b in bounds), max(b[2] for b in bounds), max(b[3] for b in bounds))
        images = [image.crop(tuple(round(value * 1.4) for value in common)) for image in images]
    else:
        left, right = min(b[0] for b in bounds), max(b[2] for b in bounds)
        images = [image.crop(tuple(round(value * 1.4) for value in (left, box[1], right, box[3])))
                  for image, box in zip(images, bounds)]
    width, height = max(i.width for i in images), max(i.height for i in images)
    changed = images[0].size != images[1].size or ImageChops.difference(images[0], images[1]).getbbox() is not None
    size = (width * 2 + 24, height + 34) if crop_text else (width, sum(i.height + 34 for i in images))
    combined = Image.new('RGB', size, 'white')
    draw = ImageDraw.Draw(combined)
    for index, image in enumerate(images):
        x = index * (width + 24) if crop_text else 0
        y = 0 if crop_text or index == 0 else images[0].height + 34
        draw.text((x + 4, y + 5), ('BEFORE' if index == 0 else 'AFTER') + f' ({counts[index]} page)', fill='black')
        combined.paste(image, (x, y + 30))
    combined.save(destination)
    return counts, changed


def build(info, directory):
    directory = Path(directory)
    directory.mkdir(exist_ok=False)
    old = directory / 'baseline'
    baseline(info.get('previous_source_commit') or info['version_plan']['official_release']['tag'], old)
    results = []
    for name, title, source, crop in [('keywords', '关键词续行对齐：旧版 / 本次', KEYWORDS, True),
                                       ('english-cover', '英文内封信息栏局部：相同长字段的旧版 / 本次', ENGLISH, False)]:
        before = compile_case(old, source, directory / (name + '-before'))
        after = compile_case(ROOT, source, directory / (name + '-after'))
        image = directory / (name + '.png')
        counts, changed = pictures(before, after, image, crop)
        results.append({'id': name, 'title': title, 'image': str(image.resolve()),
                        'layout': 'side-by-side' if crop else 'stacked',
                        'changed': changed,
                        'before_pages': counts[0], 'after_pages': counts[1],
                        'before_sha256': hashlib.sha256(before.read_bytes()).hexdigest(),
                        'after_sha256': hashlib.sha256(after.read_bytes()).hexdigest()})
    return results
