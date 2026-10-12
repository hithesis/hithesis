"""Build the full Shenzhen master's examples and a local font-comparison gallery."""
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from html import escape
from pathlib import Path
import argparse
import json
import os
import re
import shutil
import subprocess
import zipfile

import pdfplumber
import pypdfium2 as pdfium
from pypdf import PdfReader, PdfWriter
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
DEMO = ROOT / 'examples/demo'
DRIVER = ROOT / 'tests/shenzhen-report-preview.tex'
PRESETS = ('auto', 'windows', 'macos', 'founder', 'noto', 'fandol')
VARIANTS = (('proposal', 'zh', '中文开题'), ('proposal', 'en', '英文开题'),
            ('interim', 'zh', '中文中期'), ('interim', 'en', '英文中期'))
ROLES = {'songti': '宋体', 'heiti': '黑体', 'kaishu': '楷体', 'fangsong': '仿宋',
         'kaishu-gb2312': '封面校名楷体', 'serif': '西文衬线', 'sans': '西文无衬线',
         'mono': '等宽', 'math': '数学'}


def build(out, preset, stage, lang, title):
    name = f'{preset}-{stage}-{lang}'
    work = out / 'build' / name
    work.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    for key, directory in [('INDEXSTYLE', ROOT), ('BSTINPUTS', ROOT), ('BIBINPUTS', DEMO)]:
        env[key] = str(directory) + os.pathsep + env.get(key, '')
    options = f'stage={stage},campus=shenzhen,degree-level=master,lang={lang},fontset={preset}'
    command = ['latexmk', '-lualatex', '-interaction=nonstopmode', '-halt-on-error',
               f'-jobname={name}', f'-outdir={work}',
               rf'-usepretex=\PassOptionsToClass{{{options}}}{{hithesis}}', str(DRIVER)]
    result = subprocess.run(command, cwd=DEMO, env=env, capture_output=True, text=True, timeout=240)
    (work / 'build.log').write_text(result.stdout + result.stderr)
    if result.returncode:
        raise RuntimeError(f'{name}: build failed; see {work / "build.log"}')
    log = (work / f'{name}.log').read_text(errors='replace')
    if re.search(r'^!', log, re.M):
        raise RuntimeError(f'{name}: TeX error in {work / (name + ".log")}')
    roles = dict(re.findall(r'^hithesis font role ([\w-]+) = (.+)$', log, re.M))
    if not all(role in roles for role in ROLES):
        raise RuntimeError(f'{name}: incomplete font report')
    joined = re.sub(r'\s*\(hithesis\)\s*', ' ', log)
    fallbacks = [{'role': role, 'requested': ' '.join(requested.split()), 'actual': ' '.join(actual.split())}
                 for role, requested, actual in re.findall(
                     r"Font role '([^']+)': '([^']+)' is\s+unavailable;\s+using '([^']+)'", joined)]
    destination = out / f'{name}.pdf'
    shutil.copyfile(work / f'{name}.pdf', destination)
    with pdfplumber.open(destination) as pdf:
        if len(pdf.pages) < 3:
            raise RuntimeError(f'{name}: incomplete report')
        body_page = next((i for i, page in enumerate(pdf.pages) if i >= 2 and
                         any(c['size'] >= 14.5 and c['top'] < 300 and c['text'].strip()
                             for c in page.chars)), 2)
        embedded = sorted({c['fontname'].split('+')[-1] for p in pdf.pages for c in p.chars})
        record = dict(name=name, preset=preset, stage=stage, lang=lang, title=title,
                      pdf=destination.name, pages=len(pdf.pages), body_page=body_page + 1,
                      roles=roles, fallbacks=fallbacks, embedded_fonts=embedded,
                      overfull=re.findall(r'Overfull \\hbox \(([^)]+)\)', log),
                      missing_glyphs=re.findall(r'^Missing character:.*$', log, re.M))
    print(f'BUILT {name}: {record["pages"]} pages, {len(fallbacks)} fallback roles', flush=True)
    return record


def render(out, records):
    assets = out / 'images'
    assets.mkdir(exist_ok=True)
    for record in records:
        doc = pdfium.PdfDocument(out / record['pdf'])
        for kind, index in [('cover', 0), ('body', record['body_page'] - 1)]:
            image_path = assets / f'{record["name"]}-{kind}.png'
            page = doc[index]
            bitmap = page.render(scale=1.25)
            bitmap.to_pil().convert('RGB').save(image_path, optimize=True)
            bitmap.close()
            page.close()
            record[kind + '_image'] = image_path.relative_to(out).as_posix()
        doc.close()
    # Two contact sheets per variant make all six presets visible simultaneously.
    for stage, lang, _ in VARIANTS:
        group = [r for r in records if r['stage'] == stage and r['lang'] == lang]
        for kind in ('cover', 'body'):
            sheet = Image.new('RGB', (1500, 1500), '#edf0f4')
            draw = ImageDraw.Draw(sheet)
            for i, record in enumerate(group):
                image = Image.open(out / record[kind + '_image']).convert('RGB')
                image.thumbnail((478, 700), Image.Resampling.LANCZOS)
                x, y = (i % 3) * 500 + 11, (i // 3) * 750 + 32
                draw.text((x, y - 22), record['preset'], fill='#15253b')
                sheet.paste(image, (x, y))
            sheet.save(assets / f'compare-{stage}-{lang}-{kind}.jpg', quality=92)


def comparisons(out, records):
    for stage, lang, title in VARIANTS:
        writer = PdfWriter()
        for record in records:
            if (record['stage'], record['lang']) != (stage, lang):
                continue
            reader = PdfReader(out / record['pdf'])
            start = len(writer.pages)
            writer.add_page(reader.pages[0])
            writer.add_page(reader.pages[record['body_page'] - 1])
            parent = writer.add_outline_item(record['preset'], start)
            writer.add_outline_item('封面', start, parent=parent)
            writer.add_outline_item('正文首页', start + 1, parent=parent)
        # Original document links may name pages outside this two-page selection.
        writer.remove_annotations(subtypes='/Link')
        writer.add_metadata({'/Title': title + ' · 六种字体预设对照'})
        with (out / f'compare-{stage}-{lang}.pdf').open('wb') as stream:
            writer.write(stream)


def gallery(out, records):
    panels = []
    for preset in PRESETS:
        group = [r for r in records if r['preset'] == preset]
        first = group[0]
        rows = ''.join(f'<tr><th>{escape(label)}</th><td>{escape(first["roles"][role])}</td></tr>'
                       for role, label in ROLES.items())
        falls = ''.join(f'<li>{escape(ROLES.get(f["role"], f["role"]))}：'
                        f'{escape(f["requested"])} → {escape(f["actual"])}</li>'
                        for f in first['fallbacks'])
        description = f'<ul class="fallback">{falls}</ul>' if falls else '<p>所有预设候选字体均可用。</p>'
        if preset == 'auto' and first['roles'] == next(r for r in records if r['preset'] == 'windows')['roles']:
            description += '<p>本机 auto 的解析结果与 windows 一致。</p>'
        cards = []
        for record in group:
            warnings = []
            if record['overfull']:
                warnings.append(f'超宽提示 {len(record["overfull"])} 处')
            if record['missing_glyphs']:
                warnings.append(f'缺字提示 {len(record["missing_glyphs"])} 处')
            warning = ' · '.join(warnings)
            images = ''.join(
                f'<a class="preview {kind}" href="{escape(record["pdf"])}#page={page}" target="_blank">'
                f'<img loading="lazy" src="{escape(record[kind + "_image"])}" alt="{escape(record["title"])} {label}">'
                f'<span>{label}</span></a>'
                for kind, page, label in [('cover', 1, '封面'), ('body', record['body_page'], '正文首页')])
            cards.append(f'<article class="card" data-variant="{record["stage"]}-{record["lang"]}">'
                         f'<h3>{record["title"]} <small>{record["pages"]} 页</small></h3>'
                         f'<div class="pages">{images}</div>'
                         f'<p><a href="{record["pdf"]}" target="_blank">打开完整 PDF ↗</a>'
                         f'<span class="warning">{warning}</span></p></article>')
        panels.append(f'<section class="font-panel" data-font="{preset}"><h2>{preset}</h2>'
                      f'<details><summary>实际字体与回退情况</summary>{description}<table>{rows}</table></details>'
                      f'<div class="cards">{"".join(cards)}</div></section>')
    comparison_links = ''.join(
        f'<li><strong>{title}</strong>：<a href="compare-{stage}-{lang}.pdf" target="_blank">对照 PDF</a> · '
        f'<a href="images/compare-{stage}-{lang}-cover.jpg" target="_blank">封面对照图</a> · '
        f'<a href="images/compare-{stage}-{lang}-body.jpg" target="_blank">正文对照图</a></li>'
        for stage, lang, title in VARIANTS)
    html = '''<!doctype html><html lang="zh-CN"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>深圳硕士报告 · 字体预览</title>
<style>
*{box-sizing:border-box}body{margin:0;background:#f1f4f8;color:#18263b;font:16px/1.65 system-ui,sans-serif}
main{max-width:1300px;margin:auto;padding:30px 24px}h1{font-size:30px;margin-bottom:8px}h2{margin:0 0 10px}
a{color:#175ca3}header,.font-panel,.comparison{background:white;padding:24px;border-radius:12px;margin-bottom:24px}
.controls{display:flex;flex-wrap:wrap;gap:18px;position:sticky;top:0;padding:14px 20px;background:#e4ebf4;z-index:2;border-radius:8px}
select{font:inherit;padding:5px;border:1px solid #aab8c9;border-radius:5px}.cards{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:22px}
.card{min-width:0;border:1px solid #dbe2eb;border-radius:9px;padding:16px}.card h3{margin:0 0 12px;font-size:18px}
small{font-weight:400;color:#667387}.pages{display:flex;gap:10px}.preview{flex:1;min-width:0;text-decoration:none;text-align:center;font-size:13px}
.preview img{display:block;width:100%;border:1px solid #dce2ea;box-shadow:0 2px 6px #0001}.preview span{display:block;margin-top:5px}
.warning{font-size:12px;color:#9b6420;margin-left:12px}details{margin-bottom:20px;color:#465469}summary{cursor:pointer}
table{border-collapse:collapse;font-size:14px}td,th{padding:5px 14px;text-align:left;border-bottom:1px solid #e4e9ef}
body[data-view="cover"] .preview.body,body[data-view="body"] .preview.cover{display:none}[hidden]{display:none!important}
.intro{color:#55657a;font-size:14px}.fallback{color:#8c5b18}@media(max-width:800px){.cards{grid-template-columns:1fr}main{padding:14px}h1{font-size:24px}}
</style><body data-view="both"><main>
<header><h1>深圳硕士报告 · 字体预览</h1>
<p>六档字体 × 中英文开题、中期，共 24 份完整示例。</p>
<p class="intro">LuaLaTeX 编译，启用默认基线校正；各字体集使用相同元信息与对应正文。数学字体统一为 TeX Gyre Termes Math。
字体缺失时展示实际回退结果，可展开每组的字体清单查看。英文正文主要体现西文字体差异，部分预设的效果会相同。</p>
<p><a href="shenzhen-font-previews.zip">下载全部预览（ZIP）</a> · <a href="manifest.json">查看编译清单</a></p></header>
<nav class="controls"><label>字体 <select id="font">FONT_OPTIONS</select></label>
<label>报告 <select id="variant"><option value="all">全部四套</option>VARIANT_OPTIONS</select></label>
<label>显示 <select id="view"><option value="both">封面与正文</option><option value="cover">仅封面</option><option value="body">仅正文</option></select></label></nav>
<section class="comparison"><h2>六种字体并排比较</h2><ul>COMPARISON_LINKS</ul>
<p class="intro">每份对照 PDF 共 12 页，按字体集收录封面与正文首页，并提供书签；完整报告在下方各卡片中。</p></section>
PANELS
<footer class="intro">生成时间：GENERATED。PDF 为当前 hithesis 示例输出；原件依据与取舍见 README。</footer>
</main><script>
function filter(){const f=document.querySelector('#font').value,v=document.querySelector('#variant').value;
document.querySelectorAll('.font-panel').forEach(p=>p.hidden=f!=='all'&&p.dataset.font!==f);
document.querySelectorAll('.card').forEach(c=>c.hidden=v!=='all'&&c.dataset.variant!==v);
document.body.dataset.view=document.querySelector('#view').value;}
document.querySelectorAll('select').forEach(s=>s.addEventListener('change',filter));filter();
</script></body></html>'''
    html = html.replace('FONT_OPTIONS', '<option value="all">全部六档</option>' + ''.join(
        f'<option value="{p}" {"selected" if p=="windows" else ""}>{p}</option>' for p in PRESETS))
    html = html.replace('VARIANT_OPTIONS', ''.join(f'<option value="{s}-{l}">{t}</option>' for s,l,t in VARIANTS))
    html = html.replace('COMPARISON_LINKS', comparison_links).replace('PANELS', ''.join(panels))
    html = html.replace('GENERATED', datetime.now().astimezone().isoformat(timespec='seconds'))
    (out / 'index.html').write_text(html)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=ROOT/'tests/output/shenzhen-fonts')
    parser.add_argument('--jobs', type=int, default=2)
    parser.add_argument('--skip-build', action='store_true', help='regenerate previews from the existing manifest')
    args = parser.parse_args()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    if args.skip_build:
        records = json.loads((out/'manifest.json').read_text())['reports']
    else:
        records = []
        with ThreadPoolExecutor(max_workers=args.jobs) as pool:
            tasks = [pool.submit(build, out, p, s, l, t) for p in PRESETS for s,l,t in VARIANTS]
            for task in as_completed(tasks):
                records.append(task.result())
        order = {(p,s,l):i for i,(p,s,l) in enumerate((p,s,l) for p in PRESETS for s,l,_ in VARIANTS)}
        records.sort(key=lambda r:order[r['preset'],r['stage'],r['lang']])
    assert len(records) == 24
    # PDFium rendering stays on the main thread; only TeX builds run concurrently.
    render(out, records)
    comparisons(out, records)
    gallery(out, records)
    (out/'manifest.json').write_text(json.dumps({'engine':'LuaLaTeX', 'reports':records}, ensure_ascii=False, indent=2))
    with zipfile.ZipFile(out/'shenzhen-font-previews.zip', 'w', zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(out.iterdir()):
            if path.is_file() and path.suffix in ('.pdf','.html','.json','.md'):
                archive.write(path,path.name)
        for path in sorted((out/'images').iterdir()):
            archive.write(path,path.relative_to(out))
    for stage,lang,_ in VARIANTS:
        assert len(PdfReader(out/f'compare-{stage}-{lang}.pdf').pages) == 12
    print(f'PREVIEW ALL PASS: 24 reports, 4 comparison PDFs, 48 page previews; {out / "index.html"}',flush=True)


if __name__ == '__main__':
    main()
