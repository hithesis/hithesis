"""Compile and check the eight Shenzhen graduate report variants (LuaLaTeX)."""
import argparse
from pathlib import Path
import re
import subprocess
from collections import defaultdict
import pdfplumber

def rows(page):
    groups = defaultdict(list)
    for c in page.chars:
        groups[round(page.height-c['matrix'][5],2)].append(c)
    return [(y,re.sub(r'\s+','', ''.join(c['text'] for c in sorted(cs,key=lambda c:c['x0']))),cs)
            for y,cs in sorted(groups.items())]

parser = argparse.ArgumentParser()
parser.add_argument('--out', type=Path, required=True)
args = parser.parse_args()
assert args.out.is_dir(), 'output directory must already exist'
root = Path(__file__).resolve().parents[1]
results = {}
for degree in ('master', 'doctor'):
    for stage in ('proposal', 'interim'):
        for lang in ('zh', 'en'):
            name = f'sz-{degree}-{stage}-{lang}'
            options = f'campus=shenzhen,degree-level={degree},stage={stage},lang={lang},fontset=windows'
            cmd = ['lualatex', '-interaction=nonstopmode', '-halt-on-error',
                   f'-jobname={name}', f'-output-directory={args.out}',
                   rf'\PassOptionsToClass{{{options}}}{{hithesis}}\input{{tests/shenzhen-report.tex}}']
            for run in range(2):
                p = subprocess.run(cmd, cwd=root, capture_output=True, text=True, timeout=90)
                (args.out / f'{name}-build.log').write_text(p.stdout+p.stderr)
                if p.returncode:
                    raise RuntimeError(name+'\n'+'\n'.join((p.stdout+p.stderr).splitlines()[-40:]))
            assert 'ctexbook.cls' not in p.stdout and 'ctex.sty' not in p.stdout, name
            assert '不认识的键' not in p.stdout, name
            assert 'Overfull' not in p.stdout, name+' overfull box'
            assert 'ctex=false; word=true; sz=true' in p.stdout, name
            width = float(re.search(r'SZ-WIDTH: ([\d.]+)', p.stdout)[1])
            assert abs(width - (430.85 if stage == 'proposal' else 453.55)) < .02, (name,width)
            with pdfplumber.open(args.out/f'{name}.pdf') as pdf:
                pages = [page.extract_text() or '' for page in pdf.pages]
                compact = [re.sub(r'\s+', '', t) for t in pages]
                cover = compact[0]
                expected = ('硕士' if degree == 'master' else '博士')+'学位论文'+('开题' if stage == 'proposal' else '中期')+'报告'
                if lang == 'zh':
                    assert expected in cover, (name,cover)
                    assert '研究生院制' not in cover and '（学位论文）' not in cover, name
                    assert ('深圳校区教务部制' in cover) == (stage == 'proposal'), name
                    first, second = '课题的来源及研究的目的和意义', '研究进展'
                else:
                    assert 'HarbinInstituteofTechnology' in cover, name
                    assert ('Master' if degree == 'master' else 'Doctoral') in cover, name
                    assert not re.search(r'[\u4e00-\u9fff]', cover), (name,cover)
                    first, second = 'Sourceandobjectives', 'Researchprogress'
                assert len(pages) >= 3 and any(first in t and second in t for t in compact[2:]), (name,pages)
                cover_rows = rows(pdf.pages[0])
                if lang == 'zh':
                    references = [('哈尔滨工业大学',146.78 if stage=='proposal' else 155.42),
                                  (expected,211.34 if stage=='proposal' else 219.26),
                                  ('题目：',271.61 if stage=='proposal' else 280.25),
                                  ('院（系）',352.01 if stage=='proposal' else 367.85)]
                else:
                    references = [('HarbinInstituteofTechnology',146.78 if stage=='proposal' else 155.42),
                                  ('Title:',271.61 if stage=='proposal' else 280.25),
                                  ('School:',425.23 if stage=='proposal' else 441.05)]
                for label,target in references:
                    actual = next(y for y,text,_ in cover_rows if text.startswith(label))
                    assert abs(actual-target)<.5,(name,'cover',label,actual,target)
                if lang=='en':
                    field_chars = next(cs for _,text,cs in cover_rows if text.startswith('School:'))
                    x = min(c['x0'] for c in field_chars)
                    assert abs(x-(107.66 if stage=='proposal' else 137.54))<.5,(name,'field indent',x)
                toc_header = [c for c in pdf.pages[1].chars if c['top'] < 70]
                if stage == 'interim':
                    assert not toc_header, name+' interim TOC header not empty'
                body = pdf.pages[2]
                header = [c for c in body.chars if c['size'] < 10 and c['top'] < 105]
                assert header, name+' missing body header'
                baseline = body.height - header[0]['matrix'][5]
                target = (94.22 if lang == 'zh' else 93.50) if stage == 'proposal' else (60.12 if lang == 'zh' else 59.40)
                assert abs(baseline-target) < .5, (name,'header',baseline,target)
                paragraph_rows = [(y,cs) for y,text,cs in rows(body) if len(text)>28 and y<300
                                  and all(abs(c['size']-12)<.01 for c in cs)]
                assert len(paragraph_rows)>=2, name+' missing multiline body'
                pitch = paragraph_rows[1][0]-paragraph_rows[0][0]
                assert abs(pitch-(18.72 if lang=='zh' else 16.56))<.12,(name,'body pitch',pitch)
                # The removed doctoral frame would add page-height vertical edges.
                assert not any(r.get('height',0)>300 and r.get('width',0)<2 for r in body.rects), name
                results[degree,stage,lang] = (len(pages),width)
                print(f'PASS {name}: {len(pages)} pages, width={width:.2f}bp, header={baseline:.2f}bp',flush=True)
for stage in ('proposal','interim'):
    for lang in ('zh','en'):
        assert results['master',stage,lang] == results['doctor',stage,lang], (stage,lang,'inheritance differs')
print('SHENZHEN REPORT ALL PASS: 8 variants')
