"""Test Word row reconstruction, flow settings and bookmark preservation."""
from copy import deepcopy
import importlib.util
from pathlib import Path
import unittest
import xml.etree.ElementTree as E

ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('auto_table',ROOT/'scripts/word-auto-table.py')
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
w=m.w;NS=m.NS;W=m.W

def paragraph(text=''):
    p=w.element('p');p.append(w.run(text));return p

def table(counts):
    t=w.element('tbl');pr=w.element('tblPr');pr.append(w.element('tblW',w=8400,type='dxa'))
    borders=w.element('tblBorders');borders.append(w.element('top',val='single',sz=12));pr.append(borders);t.append(pr)
    grid=w.element('tblGrid');grid.extend(w.element('gridCol',w=1400) for _ in range(6));t.append(grid)
    for i,count in enumerate(counts):
        tr=w.element('tr')
        for column in range(6):
            tc=w.element('tc');tcp=w.element('tcPr');tcp.append(w.element('tcW',w=1400,type='dxa'));tc.append(tcp)
            for k in range(count):tc.append(paragraph('供气压力' if i==0 else f'{i}-{column}-{k}'))
            tr.append(tc)
        t.append(tr)
    return t

def fixture():
    root=w.element('document');body=w.element('body');root.append(body)
    body.extend([paragraph('Preserved before'),table([1,1]),paragraph('Explanation'),paragraph(),paragraph('表6-1 试样渗透率测试数据')])
    first=table([1,1,1,1,17]);body.append(first)
    symbol=first.findall('w:tr',NS)[-1].findall('w:tc',NS)[0].findall('w:p',NS)[15]
    symbol.append(w.element('r'));symbol[-1].append(w.element('sym',font='Symbol',char='F04D'))
    gap=paragraph();gap.extend([w.element('bookmarkStart',id=11,name='_TableContinuation'),w.element('bookmarkEnd',id=11)])
    body.extend([gap,paragraph('表6-1（续表）'),table([1,1,1,1]),paragraph('Preserved after')])
    return root

class WordAutoTableTests(unittest.TestCase):
    def test_rebuilds_real_rows_with_repeated_caption_and_header(self):
        root=fixture();before=deepcopy(root)
        candidates=[t for t in before.find('w:body',NS) if t.tag==W+'tbl']
        expected=m.data_signature(m.logical_rows(candidates[-2])+[deepcopy(r) for r in candidates[-1].findall('w:tr',NS)[1:]])
        result=m.transform(root)
        tables=[t for t in root.find('w:body',NS) if t.tag==W+'tbl']
        self.assertEqual(len(tables),2)
        rows=tables[-1].findall('w:tr',NS)
        self.assertEqual(len(rows),25)
        self.assertEqual(m.data_signature(rows[2:]),expected)
        self.assertEqual([r.find('w:trPr/w:tblHeader',NS) is not None for r in rows],[True,True]+[False]*23)
        self.assertTrue(all(r.find('w:trPr/w:cantSplit',NS) is not None for r in rows))
        self.assertEqual(result['data_rows'],23)
        self.assertIn('Preserved before',w.text(root));self.assertIn('Preserved after',w.text(root))

    def test_removed_bookmark_is_relocated_not_lost_or_duplicated(self):
        root=fixture();result=m.transform(root,3)
        starts=root.findall('.//w:bookmarkStart',NS);ends=root.findall('.//w:bookmarkEnd',NS)
        self.assertEqual(len(starts),1);self.assertEqual(len(ends),1)
        self.assertEqual(starts[0].get(W+'id'),ends[0].get(W+'id'))
        self.assertEqual(result['bookmarks_relocated'],['_TableContinuation'])
        tables=[t for t in root.find('w:body',NS) if t.tag==W+'tbl']
        self.assertEqual(len(tables[-1].findall('w:tr',NS)),71)

    def test_non_table_content_between_fragments_is_not_deleted(self):
        root=fixture();body=root.find('w:body',NS)
        marker=next(p for p in body if w.text(p)=='表6-1（续表）')
        marker.append(w.run(' User content'))
        with self.assertRaisesRegex(ValueError,'Unexpected content'):
            m.transform(root)

    def test_section_boundary_is_not_deleted(self):
        root=fixture();body=root.find('w:body',NS)
        marker=next(p for p in body if w.text(p)=='表6-1（续表）')
        m.properties(marker,'pPr').append(w.element('sectPr'))
        with self.assertRaisesRegex(ValueError,'section boundary'):
            m.transform(root)


if __name__=='__main__':unittest.main()
