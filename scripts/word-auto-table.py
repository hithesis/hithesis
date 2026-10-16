#!/usr/bin/env python3
"""Turn the approved hand-spliced Word example into one real, automatically paginated table."""
import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import xml.etree.ElementTree as ET
import zipfile

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('word_reference_xml',ROOT/'scripts/word-reference.py')
w=importlib.util.module_from_spec(spec);spec.loader.exec_module(w)
NS=w.NS;W='{'+w.W+'}'


def properties(parent, name):
    pr=parent.find('w:'+name,NS)
    if pr is None:pr=w.element(name);parent.insert(0,pr)
    return pr


def set_flag(pr,name,value):
    for n in list(pr):
        if n.tag==W+name:pr.remove(n)
    pr.append(w.element(name,val=1 if value else 0))


def flow_paragraph(p):
    pr=properties(p,'pPr')
    # Canonical order for the new flow properties; preserve font/spacing/indent.
    for n in list(pr):
        if n.tag in (W+'keepNext',W+'keepLines',W+'pageBreakBefore'):pr.remove(n)
    at=1 if pr.find('w:pStyle',NS) is not None else 0
    for offset,(name,value) in enumerate([('keepNext',0),('keepLines',1),('pageBreakBefore',0)]):
        pr.insert(at+offset,w.element(name,val=value))


def normalize_row(tr,header=False):
    pr=properties(tr,'trPr')
    for n in list(pr):
        if n.tag in (W+'cantSplit',W+'tblHeader'):pr.remove(n)
    pr.insert(0,w.element('cantSplit'))
    if header:pr.append(w.element('tblHeader'))
    for p in tr.findall('w:tc/w:p',NS):flow_paragraph(p)


def data_signature(rows):
    # Include symbols, inline math/OLE and run formatting, not just visible text.
    return [[b''.join(ET.tostring(n) for n in p if n.tag!=W+'pPr' and n.tag not in (W+'bookmarkStart',W+'bookmarkEnd'))
             for tc in tr.findall('w:tc',NS) for p in tc.findall('w:p',NS)] for tr in rows]


def logical_rows(table):
    rows=table.findall('w:tr',NS)
    if len(rows)!=5:raise ValueError('Expected approved five-row hand-built first fragment')
    cells=rows[-1].findall('w:tc',NS)
    counts=[len(tc.findall('w:p',NS)) for tc in cells]
    if counts!=[17]*6:raise ValueError('Expected seventeen paragraph rows inside each final cell')
    template=rows[1]
    result=[deepcopy(r) for r in rows[1:-1]]
    for i in range(17):
        row=deepcopy(template)
        for tc,source in zip(row.findall('w:tc',NS),cells):
            for child in list(tc):
                if child.tag!=W+'tcPr':tc.remove(child)
            tc.append(deepcopy(source.findall('w:p',NS)[i]))
        result.append(row)
    return result


def restore_bookmarks(root,original,caption):
    before={n.get(W+'id'):deepcopy(n) for n in original.findall('.//w:bookmarkStart',NS)}
    ends={n.get(W+'id'):deepcopy(n) for n in original.findall('.//w:bookmarkEnd',NS)}
    if set(before)!=set(ends):raise ValueError('Unbalanced source bookmarks')
    starts_now={n.get(W+'id') for n in root.findall('.//w:bookmarkStart',NS)}
    ends_now={n.get(W+'id') for n in root.findall('.//w:bookmarkEnd',NS)}
    moved=(set(before)-starts_now)|(set(ends)-ends_now)
    for parent in root.iter():
        for node in list(parent):
            if node.tag in (W+'bookmarkStart',W+'bookmarkEnd') and node.get(W+'id') in moved:parent.remove(node)
    for identifier in sorted(moved,key=int):caption.extend([before[identifier],ends[identifier]])
    final=root.findall('.//w:bookmarkStart',NS)
    if len(final)!=len(before) or {n.get(W+'name') for n in final}!={n.get(W+'name') for n in before.values()}:
        raise ValueError('Bookmark identity changed')
    return [before[i].get(W+'name') for i in sorted(moved,key=int)]


def clone_for_stress(row,block,index):
    result=deepcopy(row)
    for parent in result.iter():
        for n in list(parent):
            if n.tag in (W+'bookmarkStart',W+'bookmarkEnd'):parent.remove(n)
    for i,p in enumerate(result.findall('.//w:p',NS)):
        for attr in list(p.attrib):
            if attr.endswith('}paraId') or attr.endswith('}textId'):
                number=int(hashlib.sha256(f'{block}-{index}-{i}-{attr}'.encode()).hexdigest()[:8],16)&0x7fffffff
                p.set(attr,f'{number or 1:08X}')
    return result


def transform(root,copies=1):
    original=deepcopy(root);body=root.find('w:body',NS);children=list(body)
    tables=[(i,n) for i,n in enumerate(children) if n.tag==W+'tbl' and '供气压力' in w.text(n)]
    if len(tables)!=3:raise ValueError('Expected exactly the approved sample table and two continuation fragments')
    (first_at,first),(last_at,last)=tables[-2:]
    between=children[first_at+1:last_at]
    for n in between:
        if n.tag!=W+'p' or n.find('w:pPr/w:sectPr',NS) is not None:
            raise ValueError('Refuse to remove a non-paragraph or section boundary between fragments')
        if w.text(n).strip() and w.compact(w.text(n))!='表6-1（续表）':
            raise ValueError('Unexpected content between continuation fragments')
    cap=children[first_at-1]
    if '试样渗透率测试数据' not in w.text(cap):raise ValueError('Missing original first-fragment caption')
    rows=logical_rows(first)
    final_rows=last.findall('w:tr',NS)
    if len(final_rows)!=4:raise ValueError('Expected header plus three continued data rows')
    rows.extend(deepcopy(n) for n in final_rows[1:])
    if len(rows)!=23:raise ValueError('Unexpected logical data row count')
    expected=data_signature(rows)
    header=deepcopy(first.find('w:tr',NS))
    header_math=[ET.tostring(n) for n in header.findall('.//w:object',NS)]
    normalize_row(header,True)
    if header_math!=[ET.tostring(n) for n in header.findall('.//w:object',NS)]:raise ValueError('Header math changed')
    for row in rows:normalize_row(row)
    if expected!=data_signature(rows):raise ValueError('Data runs or symbols changed')
    caption=deepcopy(cap);flow_paragraph(caption)
    if copies>1:w.replace_text(caption,w.text(cap)+'（重复数据，仅用于加长分页测试）')
    caption_row=w.element('tr');normalize_row(caption_row,True)
    cell=w.element('tc');cell_pr=w.element('tcPr')
    total=sum(int(n.get(W+'w')) for n in first.findall('w:tblGrid/w:gridCol',NS))
    cell_pr.extend([w.element('tcW',w=total,type='dxa'),w.element('gridSpan',val=6)])
    borders=w.element('tcBorders')
    for side in ('top','left','bottom','right'):borders.append(w.element(side,val='nil'))
    cell_pr.append(borders);cell.extend([cell_pr,caption]);caption_row.append(cell)
    new=deepcopy(first)
    for n in list(new):
        if n.tag==W+'tr':new.remove(n)
    table_pr=new.find('w:tblPr',NS)
    for node in list(table_pr):
        if node.tag==W+'tblpPr':table_pr.remove(node)
    # Keep the caption above the three-line table rule, including repeated pages.
    table_borders=table_pr.find('w:tblBorders',NS)
    top=table_borders.find('w:top',NS) if table_borders is not None else None
    if top is not None:
        old_top=deepcopy(top);top.set(W+'val','nil')
        for tc in header.findall('w:tc',NS):
            pr=properties(tc,'tcPr');bs=pr.find('w:tcBorders',NS)
            if bs is None:
                bs=w.element('tcBorders')
                early={W+n for n in ('cnfStyle','tcW','gridSpan','hMerge','vMerge')}
                pr.insert(sum(n.tag in early for n in pr),bs)
            for n in list(bs):
                if n.tag==W+'top':bs.remove(n)
            bs.insert(0,deepcopy(old_top))
    new.extend([caption_row,header,*rows])
    # Length-only controls repeat ordinary numeric rows, not the original
    # ellipsis/OLE objects. Their data are explicitly marked as test repeats.
    for block in range(1,copies):new.extend(clone_for_stress(rows[i%3],block,i) for i in range(23))
    body.remove(cap);body.remove(first)
    for n in between:body.remove(n)
    body.remove(last)
    at=list(body).index(children[first_at-2])+1
    body.insert(at,new)
    moved=restore_bookmarks(root,original,caption)
    return {'data_rows':23*copies,'header_rows_repeated':2,'table_rows':2+23*copies,
        'original_data_rows':23,'stress_copies':copies,'header_math_unchanged':True,'data_runs_and_symbols_unchanged':True,
        'removed_blank_paragraphs_between_fragments':sum(not w.text(n).strip() for n in between),
        'bookmarks_relocated':moved,'caption_behavior':'same original caption repeats; no automatic continued-only suffix',
        'automatic_row_pagination':True,'data_rows_may_split_across_pages':False}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input',type=Path,default=ROOT/'build/word-reference/content-v6')
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--stress-copies',type=int,default=3)
    args=p.parse_args()
    if args.stress_copies<2:p.error('--stress-copies must be at least 2')
    if args.output.exists():raise FileExistsError('Output already exists: '+str(args.output))
    accepted=json.loads((ROOT/'tests/reference/word-content/manifest.json').read_text())
    prepared=[]
    for degree in ('doctor','bachelor'):
        source=args.input/(degree+'-content.docx')
        if w.digest(source)!=accepted['documents'][degree]['word_input_sha256']:raise ValueError('Unverified content-aligned Word source')
        with zipfile.ZipFile(source) as z:payload={n:z.read(n) for n in z.namelist()}
        for copies,label in ((1,''),(args.stress_copies,'-long')):
            root=ET.fromstring(payload['word/document.xml']);changes=transform(root,copies)
            result=payload|{'word/document.xml':w.serialize(root,payload['word/document.xml'])}
            prepared.append((degree+'-auto-table'+label,source,result,changes))
    args.output.mkdir(parents=True,exist_ok=False);documents=[]
    for name,source,payload,changes in prepared:
        path=args.output/(name+'.docx')
        with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
            for member,data in payload.items():
                info=zipfile.ZipInfo(member,(1980,1,1,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;z.writestr(info,data)
        documents.append({'name':name,'file':path.name,'sha256':w.digest(path),'source':str(source.resolve()),'source_sha256':w.digest(source),'changes':changes})
        print(name,changes)
    (args.output/'inputs.json').write_text(json.dumps({'kind':'word-real-row-automatic-table-copies','generator_sha256':w.digest(__file__),'documents':documents,
        'caption_limit':'Word repeats the same caption/header rows; continued-only conditional captions failed in actual Word probes'},ensure_ascii=False,indent=2)+'\n')


if __name__=='__main__':main()
