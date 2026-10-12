"""Compile optional wiseref integration against current hithesis products."""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
from pypdf import PdfReader
import pypdfium2 as pdfium
import threading

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('variants',ROOT/'scripts/refresh-desktop-variants.py')
v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
LOCK=threading.Lock()

def build(source, work, candidate, engine, lang, stage, preload=False):
    folder=work/(f'{engine}-{lang}-{stage}'+('-preload' if preload else ''))
    shutil.copytree(source,folder,dirs_exist_ok=True)
    shutil.copy2(candidate,folder/'wiseref.sty')
    options=f'stage={stage},degree-level=master,campus=shenzhen,lang={lang},fontset=windows'
    text=(ROOT/'tests/wiseref/integration.tex').read_text().replace(r'\WiseOptions',options)
    if stage=='final': text=r'\def\WiseFinal{1}'+text
    if lang=='en': text=r'\def\WiseEnglish{1}'+text
    if preload:text=r'\RequirePackage{wiseref}'+text
    (folder/'main.tex').write_text(text)
    with (folder/'compile.log').open('w') as log:
        for _ in range(3):
            subprocess.run([engine,'-interaction=nonstopmode','-halt-on-error','-recorder','main.tex'],cwd=folder,
                           stdout=log,stderr=subprocess.STDOUT,check=True,timeout=120)
    with LOCK, pdfium.PdfDocument(folder/'main.pdf') as doc:
        text=''
        for page in doc:
            tp=page.get_textpage(); text+=tp.get_text_range();tp.close();page.close()
    found={}
    for name in (('FIG','TAB','EQ','PANEL','MIX','STAR','KEEP-FIG','KEEP-EQ','LATE') + (('CH','TH') if stage=='final' else ())):
        m=re.search(f'M-{name}-B(.*?)M-{name}-E',text,re.S)
        assert m,(folder,name,text)
        found[name]=re.sub(r'\s+','',m[1])
    assert found['FIG'].startswith('Photo' if lang=='en' else '照片'),found
    assert found['TAB'].startswith('CUSTOM'),found
    assert found['EQ'].startswith('Equation(' if lang=='en' else ('等式（' if stage=='final' else '等式(')),found
    assert found['PANEL'].startswith('Photo' if lang=='en' else '照片'),found
    assert found['PANEL'][-1] in 'a)',found
    assert found['STAR']==found['FIG']
    assert found['KEEP-FIG']==found['FIG'] and found['KEEP-EQ']==found['EQ'],found
    assert found['LATE'].startswith('NewPhoto' if lang=='en' else '新照片'),found
    if stage=='final':
        assert found['CH']==('Chapter1' if lang=='en' else '第1章'),found
        assert found['TH'].startswith('Theorem' if lang=='en' else '定理'),found
    reader=PdfReader(folder/'main.pdf');dest=reader.named_destinations
    links=[]
    for page in reader.pages:
        for a in page.get('/Annots',[]):
            obj=a.get_object();action=obj.get('/A',{})
            if action.get('/S')=='/GoTo':
                target=action['/D'];assert target in dest,target;links.append(target)
    assert links,folder
    aux=(folder/'main.aux').read_text()
    assert r'\wiserefRecord{panel}{subfigure}' in aux,aux
    assert r'\wiserefRecord{balance}{equation}' in aux,aux
    return dict(case=folder.name,status='PASS',output=found,links=len(links))

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--work',type=Path,required=True)
    p.add_argument('--candidate',type=Path,default=ROOT.parent/'latex-wiseref/wiseref.sty')
    p.add_argument('--resume',action='store_true')
    p.add_argument('--preload-only',action='store_true')
    a=p.parse_args()
    if a.resume:
        source=a.work/'source'
        results=[r for r in json.loads((a.work/'results.json').read_text()) if r['status']=='PASS']
    else:
        a.work.mkdir(parents=True,exist_ok=False)
        source,_=v.snapshot(a.work);results=[]
    done={r['case'] for r in results}
    cases=([(e,'zh','final',True) for e in v.ENGINE_NAMES] if a.preload_only else
           [(e,l,s,False) for e in v.ENGINE_NAMES for l in ('zh','en') for s in ('final','proposal')])
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures={pool.submit(build,source,a.work,a.candidate,e,l,s,pre):f'{e}-{l}-{s}'+('-preload' if pre else '')
                 for e,l,s,pre in cases if (f'{e}-{l}-{s}'+('-preload' if pre else '')) not in done}
        for future in as_completed(futures):
            try:r=future.result()
            except Exception as error:r=dict(case=futures[future],status='FAIL',error=str(error))
            print(r,flush=True);results.append(r)
            (a.work/'results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2))
    raise SystemExit(any(r['status']!='PASS' for r in results))

if __name__=='__main__':main()
