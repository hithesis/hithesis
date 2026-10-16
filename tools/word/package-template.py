#!/usr/bin/env python3
"""Add the self-contained Word Ribbon to a VBA-enabled template built in Word."""
import argparse
from pathlib import Path
import xml.etree.ElementTree as ET
import zipfile

REL='http://schemas.openxmlformats.org/package/2006/relationships'
RIBBON='''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<customUI xmlns="http://schemas.microsoft.com/office/2006/01/customui">
  <ribbon><tabs><tab id="HITToolsTab" label="HIT 论文工具">
    <group id="HITNewSources" label="新建源稿">
      <button id="HITDoctor" label="博士源稿" size="large" imageMso="FileNew" onAction="HITRibbonDoctor" screentip="从模板内置内容新建博士源稿"/>
      <button id="HITBachelor" label="本科源稿" size="large" imageMso="FileNew" onAction="HITRibbonBachelor" screentip="从模板内置内容新建本科源稿"/>
      <button id="HITDemo" label="加长演示" size="large" imageMso="TableInsert" onAction="HITRibbonDemo" screentip="69 行表格及 4 个图块的测试源稿，重复数据仅作演示"/>
    </group>
    <group id="HITUpdate" label="分页后更新">
      <button id="HITUpdateAll" label="更新续表/续图" size="large" imageMso="RefreshAll" onAction="HITRibbonUpdate" screentip="保存源稿，按实际 Word 分页另存生成稿及 PDF" supertip="继续编辑源稿，再次点击更新。生成稿保存在源稿旁的更新结果目录。"/>
    </group>
  </tab></tabs></ribbon>
</customUI>
'''

def package(source,output):
    if output.exists():raise FileExistsError(output)
    with zipfile.ZipFile(source) as z:payload={n:z.read(n) for n in z.namelist()}
    if 'word/vbaProject.bin' not in payload:raise ValueError('Template has no VBA project')
    rels=ET.fromstring(payload['_rels/.rels'])
    kind='http://schemas.microsoft.com/office/2006/relationships/ui/extensibility'
    if any(n.get('Type')==kind for n in rels):raise ValueError('Template already has a Ribbon')
    ET.SubElement(rels,'{'+REL+'}Relationship',{'Id':'HITCustomUI','Type':kind,'Target':'customUI/customUI.xml'})
    payload['_rels/.rels']=ET.tostring(rels,encoding='utf-8',xml_declaration=True)
    payload['customUI/customUI.xml']=RIBBON.encode()
    with zipfile.ZipFile(output,'x',zipfile.ZIP_DEFLATED) as z:
        for name,value in sorted(payload.items()):
            info=zipfile.ZipInfo(name,(2026,1,1,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED
            z.writestr(info,value)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);p.add_argument('output',type=Path)
    args=p.parse_args();package(args.source,args.output)
