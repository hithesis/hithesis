"""Verify real page order, heading spacing, section parity and continuous breaks."""
import argparse
from pathlib import Path
import re
import subprocess
from collections import defaultdict
import pdfplumber

parser=argparse.ArgumentParser()
parser.add_argument('--out',type=Path,required=True)
parser.add_argument('--engine',choices=['lualatex','xelatex','pdflatex'],default='lualatex')
args=parser.parse_args()
root=Path(__file__).resolve().parents[1]
out=args.out.resolve()
assert out.is_dir()
name='sectionbreak-'+args.engine
for _ in range(2):
    p=subprocess.run([args.engine,'-halt-on-error','-interaction=nonstopmode',
                      f'-jobname={name}',f'-output-directory={out}','tests/sectionbreak.tex'],
                     cwd=root,capture_output=True,text=True,errors='replace',timeout=120)
    (out/f'{name}-build.log').write_text(p.stdout+p.stderr)
    assert p.returncode==0, p.stdout[-3500:]
with pdfplumber.open(out/f'{name}.pdf') as pdf:
    texts=[re.sub(r'\s+','',p.extract_text() or '') for p in pdf.pages]
    def page_of(s):
        found=[i for i,t in enumerate(texts) if s in t]
        assert len(found)==1,(s,found)
        return found[0]
    alpha=page_of('Alphaheading'); figure=page_of('DEFERREDFIGURE'); beta=page_of('Betaheading')
    assert alpha<figure<beta,(alpha,figure,beta)
    assert page_of('CONTINUOUSMARKER')==beta
    assert page_of('NEXTMARKER')==beta+1
    assert page_of('DEFAULTNEXT')==page_of('EVENTWO')+1
    for label,parity in [('ODDONE',1),('ODDTWO',1),('EVENONE',0),('EVENTWO',0)]:
        assert (page_of(label)+1)%2==parity,label
    assert page_of('ODDTWO')==page_of('ODDONE')+2
    assert page_of('EVENTWO')==page_of('EVENONE')+2
    assert page_of('ROMANPAGE:i.')==page_of('SINGLEAGAIN')
    assert 'reportsectionnumberisstill2.' in texts[page_of('SINGLEAGAIN')]
    geometry=pdf.pages[page_of('GEOMETRYMARKER')]
    rules=[r for r in geometry.rects if abs(r['height']-1)<.02]
    rules += [r for r in geometry.lines if abs(r.get('linewidth',0)-1)<.02 and r['height']<.02]
    assert any(abs(r['width']-(geometry.width-8*72/2.54))<.02 for r in rules), ('section margins ignored',geometry.width,[(r['width'],r['height']) for r in rules])
    def baseline(page,label):
        rows=defaultdict(list)
        for c in page.chars:
            if c['size']>14: rows[round(page.height-c['matrix'][5],3)].append(c)
        return next(y for y,cs in rows.items() if label in ''.join(c['text'] for c in sorted(cs,key=lambda c:c['x0'])).replace(' ',''))
    y1=baseline(pdf.pages[alpha],'Alphaheading'); y2=baseline(pdf.pages[beta],'Betaheading')
    assert abs(y1-y2)<.02,(y1,y2)
    assert abs(y1-141.7)<1,(y1,'page-before spacing lost')
    print(f'SECTIONBREAK PASS {args.engine}: {len(pdf.pages)} pages; float before heading; '
          f'continuous/next/odd/even/default/columns/page-number all checked; heading baselines {y1}/{y2}')

chapter_name='sectionbreak-chapters-'+args.engine
p=subprocess.run([args.engine,'-halt-on-error','-interaction=nonstopmode',
                  f'-jobname={chapter_name}',f'-output-directory={out}','tests/sectionbreak-chapters.tex'],
                 cwd=root,capture_output=True,text=True,errors='replace',timeout=120)
(out/f'{chapter_name}-build.log').write_text(p.stdout+p.stderr)
assert p.returncode==0,p.stdout[-3500:]
with pdfplumber.open(out/f'{chapter_name}.pdf') as pdf:
    assert len(pdf.pages)==5,len(pdf.pages)
    for index,label in [(0,'Alphachapter'),(2,'Betachapter'),(4,'Gammachapter')]:
        text=''.join(c['text'] for c in pdf.pages[index].chars if c['size']>14).replace(' ','')
        assert label in text,(index,text)
    assert 'CHAPTER FLOAT' in (pdf.pages[1].extract_text() or '')
    assert not (pdf.pages[3].extract_text() or '').strip(),'inserted odd-page blank not empty'
print(f'CHAPTER BREAK PASS {args.engine}: float on page 2, chapters on pages 1/3/5, blank page 4')
chapter_positions=[]
for before in (0,24):
    job=f'chapter-spacing-{args.engine}-{before}'
    source=(r'\AddToHook{class/hithesis/after}{\hitsetup{styles={Heading1/if-raggedbottom='
            +f'{{paragraph={{spacing={{before={before}bp,after=0bp}}}}}}'
            +r'}}}\input{tests/sectionbreak-chapters.tex}')
    p=subprocess.run([args.engine,'-halt-on-error','-interaction=nonstopmode',
                      f'-jobname={job}',f'-output-directory={out}',source],cwd=root,
                     capture_output=True,text=True,errors='replace',timeout=120)
    (out/f'{job}-build.log').write_text(p.stdout+p.stderr)
    assert p.returncode==0,p.stdout[-3500:]
    with pdfplumber.open(out/f'{job}.pdf') as pdf:
        chapter_positions.append([baseline(pdf.pages[i],s) for i,s in
                                  [(0,'Alphachapter'),(2,'Betachapter'),(4,'Gammachapter')]])
for low,high in zip(*chapter_positions):
    assert abs(high-low-24)<.03,(args.engine,'chapter before-space lost',low,high)
print(f'CHAPTER SPACING PASS {args.engine}: all three chapter tops preserve the configured 24bp')
