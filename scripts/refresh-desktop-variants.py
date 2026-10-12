"""Refresh the desktop variants from a fresh source snapshot and publish Chinese paths."""
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from html import escape
from pathlib import Path
from urllib.parse import quote
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import time
import zipfile
from pypdf import PdfReader

ROOT=Path(__file__).resolve().parents[1]
ENGINE_NAMES={'lualatex':'主用编译（LuaLaTeX）','xelatex':'兼容编译（XeLaTeX）','pdflatex':'兼容编译（pdfLaTeX）'}
CAMPUS={'harbin':'哈尔滨校区','shenzhen':'深圳校区','weihai':'威海校区'}
DEGREE={'bachelor':'本科','master':'硕士','doctor':'博士','postdoc':'博士后'}
FONT={'windows':'中易字体','fandol':'Fandol字体','mac':'苹果系统字体','macos':'苹果系统字体',
      'auto':'自动字体','noto':'Noto字体','founder':'方正字体'}

def options_dict(options):
    return dict(item.split('=',1) for item in options.split(',') if '=' in item)

def chinese_path(engine,options):
    d=options_dict(options)
    degree=d.get('degree-level','doctor'); stage=d.get('stage','final')
    material={'final':'学位论文','proposal':'开题报告','interim':'中期报告'}[stage]
    if degree=='postdoc': material='博士后出站报告'
    path=Path(ENGINE_NAMES[engine])/material/CAMPUS[d.get('campus','harbin')]
    if degree!='postdoc': path/=DEGREE[degree]
    tags=['英文' if d.get('lang')=='en' else '中文']
    if degree=='bachelor' and stage=='final':
        tags.append('毕业设计' if d.get('form')=='practice' else '毕业论文')
    elif degree in ('master','doctor'):
        tags.append('专业学位' if d.get('degree-type')=='professional' else '学术学位')
    tags.append('人文社科类' if d.get('category')=='hass' else '理工类')
    requested=d.get('fontset','auto')
    if engine=='pdflatex' and requested not in ('windows','auto'):
        tags.append(f'中易或文鼎兼容字体（请求{FONT[requested]}）')
    else:
        tags.append(FONT[requested])
    if d.get('debug')=='true': tags.append('显示版心与行号')
    return path/('·'.join(tags)+'.pdf')

def load_jobs(dest,retry_failed=False,align_engines=False):
    manifest=dest/'变体清单.json'
    if manifest.exists():
        previous=json.loads(manifest.read_text())
        jobs=previous['variants']
        for job in jobs:
            job['old_path']=job['path']
            job.setdefault('source_sha256',previous['source_sha256'])
    else:
        rows={}
        for line in (dest/'变体说明.txt').read_text().splitlines():
            if '\t' in line:
                name,options=line.split('\t',1)
                rows[name]=options.replace('degree-level=bachelor*','degree-level=bachelor,form=practice')
        jobs=[]
        for engine in ENGINE_NAMES:
            for old in sorted((dest/engine).glob('*.pdf')):
                if old.stem not in rows:
                    raise RuntimeError(f'No options recorded for {old}')
                jobs.append(dict(engine=engine,name=old.stem,options=rows[old.stem],old_path=old.relative_to(dest).as_posix()))
    existing={(j['engine'],j['name']) for j in jobs}
    for engine in ENGINE_NAMES:
        for stage,short in [('proposal','prop'),('interim','int')]:
            for degree,abbr in [('master','mast'),('doctor','doct')]:
                name=f'r-{short}-{abbr}-sz-en'
                if (engine,name) not in existing:
                    jobs.append(dict(engine=engine,name=name,options=f'stage={stage},degree-level={degree},campus=shenzhen,lang=en,fontset=windows'))
    if align_engines:
        matrix={}
        for job in jobs:
            if job['name'] in matrix and matrix[job['name']]!=job['options']:
                raise RuntimeError(f'Conflicting options for {job["name"]}')
            matrix[job['name']]=job['options']
        existing={(j['engine'],j['name']) for j in jobs}
        for engine in ENGINE_NAMES:
            for name,options in sorted(matrix.items()):
                if (engine,name) not in existing:
                    jobs.append(dict(engine=engine,name=name,options=options))
    paths=set()
    for job in jobs:
        job['path']=chinese_path(job['engine'],job['options']).as_posix()
        assert job['path'] not in paths,job['path']
        paths.add(job['path'])
        if not retry_failed or job.get('status')!='已更新':
            job['status']='待刷新'
    return jobs

def snapshot(work):
    source=work/'source'
    demo=ROOT/'examples/demo'
    output_suffixes={'.aux','.log','.toc','.toe','.out','.bbl','.blg','.fls','.fdb_latexmk','.idx','.ind','.ilg','.hd'}
    def ignore(folder,names):
        return [n for n in names if n=='.DS_Store' or Path(n).suffix in output_suffixes
                or (Path(folder)==demo and n.endswith('.pdf')) or n.endswith('-BSTcontrol.bib')]
    shutil.copytree(demo,source,ignore=ignore)
    products=subprocess.check_output(['python3','scripts/products.py','--dist'],cwd=ROOT,text=True).split()
    for name in products:
        p=ROOT/name
        if not p.is_file(): raise RuntimeError(f'Missing generated product: {p}')
        target=source/name
        target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(p,target)
    digest=hashlib.sha256()
    for path in sorted(source.rglob('*')):
        if path.is_file():
            digest.update(path.relative_to(source).as_posix().encode())
            digest.update(path.read_bytes())
    return source,digest.hexdigest()

def prepare_names(dest,jobs,stamp):
    history=dest/'历史版本'
    history.mkdir(exist_ok=True)
    archive_path=history/f'刷新前备份-{stamp}.zip'
    with zipfile.ZipFile(archive_path,'x',zipfile.ZIP_DEFLATED) as z:
        for job in jobs:
            if 'old_path' in job and (dest/job['old_path']).exists():
                z.write(dest/job['old_path'],job['old_path'])
        for name in ('变体说明.txt','刷新记录.txt','刷新状态.txt','变体清单.json','变体总览.html'):
            if (dest/name).exists(): z.write(dest/name,name)
    with zipfile.ZipFile(archive_path) as z:
        assert z.testzip() is None
    for job in jobs:
        if 'old_path' not in job: continue
        old=dest/job['old_path']; new=dest/job['path']
        if old.exists() and old!=new:
            new.parent.mkdir(parents=True,exist_ok=True)
            if new.exists(): raise RuntimeError(f'Target already exists: {new}')
            shutil.copy2(old,new)
            assert hashlib.sha256(old.read_bytes()).digest()==hashlib.sha256(new.read_bytes()).digest()
            old.unlink()
    for engine in ENGINE_NAMES:
        folder=dest/engine
        if folder.is_dir():
            entries=list(folder.iterdir())
            if all(p.name=='.DS_Store' for p in entries):
                for p in entries: p.unlink()
                folder.rmdir()
    return archive_path

def publish_status(dest,work,jobs,stamp,fingerprint):
    complete=sum(j['status']=='已更新' for j in jobs)
    failed=sum(j['status']=='失败，保留旧件' for j in jobs)
    data=dict(updated=datetime.now().isoformat(timespec='seconds'),started=stamp,
              source=str(ROOT),source_sha256=fingerprint,work=str(work),pid=os.getpid(),
              completed=complete,failed=failed,total=len(jobs),variants=jobs)
    temp=dest/'变体清单.json.tmp'
    temp.write_text(json.dumps(data,ensure_ascii=False,indent=2))
    temp.replace(dest/'变体清单.json')
    status=f'当前代码快照：{fingerprint[:16]}\n已更新 {complete}/{len(jobs)}；失败 {failed}\n工作目录：{work}\n'
    status+=''.join(f"失败：{j['path']}\n日志：{j.get('log','')}\n" for j in jobs if j['status']=='失败，保留旧件')
    (dest/'刷新状态.txt').write_text(status)
    (work/'status.json').write_text(json.dumps(data,ensure_ascii=False,indent=2))
    sections=[]
    for engine,label in ENGINE_NAMES.items():
        rows=[]
        for job in sorted((j for j in jobs if j['engine']==engine),key=lambda j:j['path']):
            rel=Path(job['path']); exists=(dest/rel).exists()
            link=f'<a href="{quote(rel.as_posix())}">{escape(rel.name)}</a>' if exists else escape(rel.name)
            color='#187341' if job['status']=='已更新' else '#97631e'
            rows.append(f'<tr><td>{escape(" / ".join(rel.parts[1:-1]))}</td><td>{link}</td>'
                        f'<td style="color:{color}">{job["status"]}</td><td>{job.get("pages","")}</td></tr>')
        sections.append(f'<h2>{label}</h2><table><tr><th>分支</th><th>文件</th><th>状态</th><th>页数</th></tr>{"".join(rows)}</table>')
    gallery=(ROOT/'tests/output/shenzhen-fonts/index.html').as_uri()
    html=f'''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>hiThesis 变体总览</title><style>body{{font:15px/1.6 system-ui,sans-serif;max-width:1450px;margin:32px auto;padding:0 24px;background:#f6f8fb;color:#243145}}
table{{border-collapse:collapse;width:100%;background:white}}td,th{{padding:8px 12px;border-bottom:1px solid #e0e5ec;text-align:left}}a{{color:#165da7}}h2{{margin-top:32px}}code{{word-break:break-all}}</style>
<h1>hiThesis 变体总览</h1><p>已更新 {complete}/{len(jobs)} · 失败 {failed} · {data['updated']}</p>
<p>目录按“编译引擎 → 材料类型 → 校区 → 学位”整理。文件名标明语种、学位类型、学科门类及字体。
“待刷新”的链接仍指向旧件；编译成功后会替换。深圳博士报告暂时沿用对应硕士版式。</p>
<p>三个引擎采用同一变体清单。pdfLaTeX 的字体后端仍使用中易或文鼎兼容字体；
文件名中的“请求”记录类选项，不表示实际使用了该 Unicode 字体预设。
wiseref 由用户自行安装加载，本清单的示例不自动加载它。</p>
<p><a href="{gallery}">深圳硕士六种字体预览</a> · <a href="变体清单.json">完整选项清单</a> · <a href="刷新状态.txt">刷新状态</a></p>
{''.join(sections)}<p>来源：当前工作区（含未提交修改）。快照：<code>{fingerprint}</code></p></html>'''
    (dest/'变体总览.html').write_text(html)

def build(source,work,job,epoch):
    d=work/job['engine']/job['name']
    shutil.copytree(source,d)
    entry='final.tex' if options_dict(job['options']).get('stage')=='final' else 'report.tex'
    text=(d/entry).read_text()
    text,n=re.subn(r'(?m)^\\documentclass\[[^]]*\]\{[^}]*\}',
                   lambda _:r'\documentclass['+job['options']+']{hithesis}',text,count=1)
    assert n==1
    (d/'main.tex').write_text(text)
    env=os.environ.copy(); env.update(SOURCE_DATE_EPOCH=str(epoch),FORCE_SOURCE_DATE='1')
    flag={'lualatex':'-lualatex','xelatex':'-xelatex','pdflatex':'-pdf'}[job['engine']]
    log=d/'compile.log'
    start=time.monotonic()
    try:
        with log.open('w') as stream:
            p=subprocess.run(['latexmk',flag,'-interaction=nonstopmode','-halt-on-error','main.tex'],cwd=d,
                             env=env,stdout=stream,stderr=subprocess.STDOUT,timeout=900)
        if p.returncode: return dict(status='失败，保留旧件',log=str(log),error=f'latexmk exit {p.returncode}')
        last=(d/'main.log').read_text(errors='replace')
        if re.search(r'^!',last,re.M): return dict(status='失败，保留旧件',log=str(log),error='TeX error')
        pages=len(PdfReader(d/'main.pdf').pages)
        assert pages>0
        return dict(status='已更新',log=str(log),pdf=str(d/'main.pdf'),pages=pages,
                    seconds=round(time.monotonic()-start,1),overfull=len(re.findall(r'Overfull \\hbox',last)))
    except Exception as e:
        return dict(status='失败，保留旧件',log=str(log),error=str(e))

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--dest',type=Path,default=Path.home()/'Desktop/hithesis-变体')
    p.add_argument('--work',type=Path,required=True)
    p.add_argument('--jobs',type=int,default=6)
    p.add_argument('--retry-failed',action='store_true',help='Keep successful variants and rebuild only unfinished ones from a fresh snapshot')
    p.add_argument('--align-engines',action='store_true',help='Use the union of all variants for each engine')
    a=p.parse_args(); dest=a.dest.resolve(); work=a.work.resolve()
    assert dest.is_dir() and not work.exists()
    work.mkdir(parents=True)
    stamp=datetime.now().strftime('%Y%m%d-%H%M%S')
    jobs=load_jobs(dest,a.retry_failed,a.align_engines)
    source,fingerprint=snapshot(work)
    archive=prepare_names(dest,jobs,stamp)
    (dest/'变体说明.txt').write_text('文件按编译引擎、材料类型、校区、学位分类，名称全部展开为中文。\n'
      '入口：变体总览.html\n详细类选项：变体清单.json\n刷新进度：刷新状态.txt\n'
      f'旧版备份：{archive.relative_to(dest)}\n')
    publish_status(dest,work,jobs,stamp,fingerprint)
    epoch=int(time.time())
    # Reports go first so the newly changed Shenzhen variants become available early.
    queue=sorted((j for j in jobs if j['status']!='已更新'),key=lambda j:(options_dict(j['options']).get('stage')=='final',
                                   options_dict(j['options']).get('campus')!='shenzhen',j['engine'],j['name']))
    print(f'START {len(jobs)} variants; snapshot {fingerprint[:16]}; backup {archive}',flush=True)
    with ThreadPoolExecutor(max_workers=a.jobs) as pool:
        futures={pool.submit(build,source,work,j,epoch):j for j in queue}
        done=0
        for future in as_completed(futures):
            job=futures[future]; result=future.result(); job.update(result); done+=1
            if job['status']=='已更新':
                job['source_sha256']=fingerprint
                target=dest/job['path']; target.parent.mkdir(parents=True,exist_ok=True)
                temp=target.with_suffix('.pdf.new'); shutil.copy2(job['pdf'],temp); temp.replace(target)
            publish_status(dest,work,jobs,stamp,fingerprint)
            print(f'{done}/{len(jobs)} {job["status"]} {job["engine"]}/{job["name"]}',flush=True)
    failed=[j for j in jobs if j['status']!='已更新']
    if not failed:
        (dest/'刷新记录.txt').write_text(f'刷新完成：{datetime.now().isoformat(timespec="seconds")}\n成功 {len(jobs)}/{len(jobs)}\n来源：{ROOT}\n快照：{fingerprint}\n')
    print(f'FINISH success={len(jobs)-len(failed)} failed={len(failed)}',flush=True)
    raise SystemExit(bool(failed))

if __name__=='__main__': main()
