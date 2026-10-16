"""Continuation planning and source/output separation, without a Word VM."""
from copy import deepcopy
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as E

ROOT=Path(__file__).resolve().parents[1]
def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
m=load('word_continuations_tested',ROOT/'scripts/word-continuations.py')
fixture=load('continuation_row_fixture',ROOT/'tests/word-auto-table.py')
w=m.w;NS=m.NS;W=m.W

def package(with_figures=False):
    root=fixture.fixture();m.xml.transform(root)
    body=root.find('w:body',NS)
    target=[n for n in body if n.tag==W+'tbl'][-1]
    m.set_style(target.find('w:tr/w:tc/w:p',NS),m.SRC_TABLE)
    if with_figures:
        body.append(m.marker('source start',m.FIG_START))
        for number in range(2):
            p=fixture.paragraph();r=w.element('r');r.append(w.element('drawing'));p.append(r)
            body.extend([p,fixture.paragraph(f'Panel {number}')])
        cap=fixture.paragraph('图2-1 Test artwork');m.set_style(cap,m.FIG_CAP);body.append(cap)
        body.append(m.marker('source end',m.FIG_END))
    settings=w.element('settings');settings.append(w.element('compat'))
    data={'word/document.xml':E.tostring(root),'word/settings.xml':E.tostring(settings)}
    m.set_role(data,'source');return data

class ContinuationTests(unittest.TestCase):
    def test_numeric_title_is_not_merged_into_table_number(self):
        self.assertEqual(m.caption_label('表 6 - 1  1号试样渗透率数据','表'),'表6-1')
        self.assertEqual(m.caption_label('图1-1\u30002026年试验结果','图'),'图1-1')

    def test_tab_separates_caption_number_from_numeric_title(self):
        p=fixture.paragraph('表6-1');r=w.element('r');r.append(w.element('tab'));t=w.element('t');t.text='1号试样';r.append(t);p.append(r)
        self.assertEqual(m.caption_label(m.caption_text(p),'表'),'表6-1')

    def test_table_continuation_caption_and_data_order(self):
        source=package();before=E.fromstring(source['word/document.xml'])
        expected=m.xml.data_signature(m.models(before)[0][0]['rows'])
        result,spec=m.render(source,{'tables':{'0':[10,13]}})
        root=E.fromstring(result['word/document.xml'])
        tables=[n for n in root.find('w:body',NS) if n.tag==W+'tbl'][1:]
        self.assertEqual([len(t.findall('w:tr',NS))-2 for t in tables],[10,13])
        self.assertIn('试样渗透率测试数据',w.text(tables[0].find('w:tr',NS)))
        self.assertEqual(w.text(tables[1].find('w:tr',NS)),'表6-1（续表）')
        self.assertEqual(m.xml.data_signature([r for t in tables for r in t.findall('w:tr',NS)[2:]]),expected)
        self.assertEqual(m.role(result),'generated')
        self.assertEqual(len(spec['tables']),2)

    def test_one_page_table_has_no_stale_continued_caption(self):
        result,spec=m.render(package(),{'tables':{'0':[23]}})
        self.assertNotIn('（续表）',w.text(E.fromstring(result['word/document.xml'])))
        self.assertEqual(len(spec['tables']),1)

    def test_figure_titles_follow_page_groups_and_do_not_repeat_in_same_page(self):
        source=package(True)
        separate,_=m.render(source,{'figures':{'0':[[0],[1]]}})
        together,spec=m.render(source,{'figures':{'0':[[0,1]]}})
        self.assertIn('图2-1（续图）',w.text(E.fromstring(separate['word/document.xml'])))
        text=w.text(E.fromstring(together['word/document.xml']))
        self.assertNotIn('（续图）',text)
        self.assertEqual(text.count('图2-1 Test artwork'),1)
        self.assertEqual(len(spec['figures'][0]['captions']),1)
        self.assertNotIn('source start',text)

    def test_deterministic_source_to_generated_xml(self):
        source=package(True);plan={'tables':{'0':[10,13]},'figures':{'0':[[0],[1]]}}
        first,spec1=m.render(source,plan);second,spec2=m.render(source,plan)
        self.assertEqual(first,second);self.assertEqual(spec1,spec2)

    def test_invalid_partition_cannot_drop_or_duplicate_rows(self):
        with self.assertRaisesRegex(ValueError,'partition'):m.render(package(),{'tables':{'0':[10,12]}})

    def test_split_data_row_is_not_reported_as_valid_pagination(self):
        with self.assertRaisesRegex(ValueError,'single data row'):
            m.split_sizes([{'start_page':1,'end_page':2}])

    def test_generated_output_cannot_be_used_as_editable_source(self):
        data,_=m.render(package(),{})
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'generated.docx';m.write_package(path,data)
            with self.assertRaisesRegex(ValueError,'editable source'):
                m.update(path,Path(tmp)/'new-run')

    def test_figure_caption_orphan_is_not_reported_as_success(self):
        layout={'tables':[],'figures':[{'id':0,'units':[{'start_page':1,'end_page':1},{'start_page':1,'end_page':1}],
                 'captions':[{'start_page':2,'end_page':2}]}]}
        spec={'tables':[],'figures':[{'id':0,'groups':[[0,1]]}]}
        with self.assertRaisesRegex(ValueError,'caption cannot fit'):
            m.next_plan(layout,spec,{'figures':{'0':[[0,1]]}})

    def test_source_changes_during_measurement_do_not_produce_stale_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            source=Path(tmp)/'source.docx';m.write_package(source,package())
            class ChangedSource:
                @staticmethod
                def measure(*args):
                    source.write_bytes(b'new user version')
                    return {'pages':1,'tables':[],'figures':[]}
            with patch.object(m,'load',return_value=ChangedSource), self.assertRaisesRegex(RuntimeError,'Source changed'):
                m.update(source,Path(tmp)/'run')
            self.assertFalse((Path(tmp)/'run/output.docx').exists())


if __name__=='__main__':unittest.main()
