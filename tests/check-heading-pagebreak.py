"""Compare first and subsequent page-top heading spacing in all four report variants."""
from pathlib import Path
from collections import defaultdict
import argparse
import subprocess
import pdfplumber

parser=argparse.ArgumentParser()
parser.add_argument('--out',type=Path,required=True)
parser.add_argument('--engine',default='lualatex',choices=['lualatex','xelatex'])
args=parser.parse_args()
root=Path(__file__).resolve().parents[1]
out=args.out.resolve()
assert out.is_dir()
for stage,lang,consecutive in [(s,l,c) for s in ('proposal','interim') for l in ('zh','en') for c in (False,True)]:
    name=f'heading-break-{args.engine}-{stage}-{lang}-{int(consecutive)}'
    options=f'stage={stage},lang={lang},campus=shenzhen,degree-level=master,fontset=fandol'
    prefix=r'\def\ConsecutiveHeadings{1}' if consecutive else ''
    source=prefix+rf'\PassOptionsToClass{{{options}}}{{hithesis}}\input{{tests/heading-pagebreak.tex}}'
    result=subprocess.run([args.engine,'-halt-on-error','-interaction=nonstopmode',
                           f'-jobname={name}',f'-output-directory={out}',source],cwd=root,
                          capture_output=True,text=True,timeout=120)
    (out/f'{name}-build.log').write_text(result.stdout+result.stderr)
    assert result.returncode==0,result.stdout[-2000:]
    found=[]
    with pdfplumber.open(out/f'{name}.pdf') as pdf:
        assert len(pdf.pages)==2,(name,len(pdf.pages))
        for page in pdf.pages:
            groups=defaultdict(list)
            for c in page.chars:
                if c['size']>14: groups[round(page.height-c['matrix'][5],3)].append(c)
            for y,cs in groups.items():
                text=''.join(c['text'] for c in sorted(cs,key=lambda c:c['x0']))
                if 'heading' in text: found.append(y)
    assert len(found)==2,(name,found)
    # Proposal merges the preceding heading's 12bp after-space; interim adds spacing.
    expected=12 if consecutive and stage=='proposal' else 0
    assert abs(found[0]-found[1]-expected)<.03,(name,found,expected)
    print('PASS',name,found,flush=True)
print('HEADING BREAK ALL PASS: 8 cases')
