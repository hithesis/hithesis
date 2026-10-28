"""Compile undergraduate types and check declaration text, headers and TOC names."""
import argparse
from pathlib import Path
import re
import shutil
import subprocess

import pypdfium2 as pdfium

ROOT = Path(__file__).resolve().parents[1]
TITLE = '本科论文排版验证'
# Text from the Academic Affairs Office's undergraduate declaration DOCX files.
DECLARATION = (
    '本人郑重声明：此处所提交的本科{kind}《' + TITLE + '》，'
    '是本人在导师指导下，在哈尔滨工业大学攻读学士学位期间独立进行研究工作所取得的成果，'
    '且{kind}中除已标注引用文献的部分外不包含他人完成或已发表的研究成果。'
    '对本{kind}的研究工作做出重要贡献的个人和集体，均已在文中以明确方式注明。'
    '本{kind}对使用AI工具的情况进行了明确标注。'
)
PERMISSION = (
    '本科{kind}是本科生在哈尔滨工业大学攻读学士学位期间完成的成果，'
    '知识产权归属哈尔滨工业大学。本科{kind}的使用权限如下：'
    '（1）学校可以采用影印、缩印或其他复制手段保存本科生上交的{kind}，'
    '并向有关部门报送本科{kind}；（2）根据需要，学校可以将本科{kind}部分或全部内容'
    '编入有关数据库进行检索和提供相应阅览服务；（3）本科生毕业后发表与此{kind}'
    '研究成果相关的学术论文和其他成果时，应征得导师同意，且第一署名单位为哈尔滨工业大学。'
    '保密论文在保密期内遵守有关保密规定，解密后适用于此使用权限规定。'
    '本人知悉本科{kind}的使用权限，并将遵守有关规定。'
)
CASES = (
    ('harbin-default', 'type=bachelor,campus=harbin', '毕业论文（设计）'),
    ('harbin-thesis', 'type=bachelor,campus=harbin,bachelortype=thesis', '毕业论文（设计）'),
    ('harbin-capstone', 'type=bachelor,campus=harbin,bachelortype=capstone', '综合设计（论文）'),
    ('harbin-thesis-humanities', 'type=bachelor,campus=harbin,bachelortype=thesis,tocfour=true', '毕业论文（设计）'),
    ('harbin-capstone-humanities', 'type=bachelor,campus=harbin,bachelortype=capstone,tocfour=true', '综合设计（论文）'),
    ('harbin-capstone-design', 'type=bachelor,campus=harbin,bachelortype=capstone,design=true', '综合设计（论文）'),
    ('weihai', 'type=bachelor,campus=weihai', '毕业设计（论文）'),
    ('shenzhen', 'type=bachelor,campus=shenzhen', '毕业论文（设计）'),
    ('master', 'type=master,campus=harbin', None),
)


def compact(text):
    return re.sub(r'\s+', '', text)


def compile_case(runtime, work, name, options, kind, fontset):
    folder = work / name
    folder.mkdir(parents=True, exist_ok=True)
    for pattern in ('*.cls', '*.cfg', '*.sty', '*.eps'):
        for path in runtime.glob(pattern):
            shutil.copy2(path, folder / path.name)
    source = (
        r'\documentclass[fontset=' + fontset + ',' + options + ']{hithesisbook}' '\n'
        r'\hitsetup{ctitle={' + TITLE + r'},ctitleone={本科论文},ctitletwo={排版验证},'
        r'cauthor={测试作者},csubject={测试专业},caffil={测试学院},'
        r'csupervisor={测试导师},cstudentid={1234567890},cdate={2026年10月}}' '\n'
        r'\begin{document}\frontmatter' '\n'
        + (r'\begin{cabstract}中文摘要。\end{cabstract}' '\n'
           r'\begin{eabstract}English abstract.\end{eabstract}\makecover' '\n'
           if name.startswith('harbin-') else '')
        + r'\tableofcontents\mainmatter\chapter{正文验证}' '\n'
        r'检查页眉名称与声明内容。\backmatter\authorization\end{document}' '\n'
    )
    (folder / 'fixture.tex').write_text(source, encoding='utf-8')
    with (folder / 'build.txt').open('w', encoding='utf-8') as output:
        for _ in range(2):
            subprocess.run(['xelatex', '-interaction=nonstopmode', '-halt-on-error',
                'fixture.tex'], cwd=folder, stdout=output, stderr=subprocess.STDOUT,
                check=True, timeout=120)
    pages = []
    with pdfium.PdfDocument(folder / 'fixture.pdf') as document:
        for page in document:
            textpage = page.get_textpage()
            pages.append(compact(textpage.get_text_range()))
            textpage.close()
            page.close()
    text = ''.join(pages)
    if name.startswith('harbin-'):
        heading = '哈尔滨工业大学本科' + kind
        declaration = pages[-1]
        assert '本科' + kind in pages[0], (name, 'Cover type')
        assert any(page.startswith(heading + '第1章') for page in pages), (name, 'Body header')
        assert heading + '原创性声明和使用权限' in declaration, (name, 'Declaration heading')
        assert '本科' + kind + '原创性声明' in declaration, (name, 'Originality subheading')
        assert '本科' + kind + '使用权限' in declaration, (name, 'Permission subheading')
        assert DECLARATION.format(kind=kind) in declaration, (name, 'Originality text')
        assert PERMISSION.format(kind=kind) in declaration, (name, 'Permission text')
        assert declaration.count('作者签名：') == 2, (name, 'Both author signatures on one page')
        assert declaration.count('导师签名：') == 1, (name, 'Supervisor signature on same page')
        assert declaration.count('日期：') == 3, (name, 'All three dates')
        toc = compact((folder / 'fixture.toc').read_text(encoding='utf-8'))
        assert heading + '原创性声明和使用权限' in toc, (name, 'TOC title')
        bookmarks = compact((folder / 'fixture.out').read_text(encoding='utf-8'))
        # hyperref serializes PDF bookmarks using octal UTF-16 bytes.
        encoded = ''.join('\\%03o' % b for b in (heading + '原创性声明和使用权限').encode('utf-16-be'))
        assert encoded in bookmarks, (name, 'PDF bookmark title')
        other = '综合设计（论文）' if kind == '毕业论文（设计）' else '毕业论文（设计）'
        assert other not in text, (name, 'Mixed undergraduate names')
    elif name == 'shenzhen':
        # dev deliberately maps Shenzhen undergraduates to the Harbin style.
        assert DECLARATION.format(kind=kind) in pages[-1], (name, 'Shared Harbin declaration')
        assert PERMISSION.format(kind=kind) in pages[-1], (name, 'Shared Harbin permission')
    else:
        assert '对使用AI工具' not in text, (name, 'Other declarations unchanged')
        if kind:
            assert kind in text, (name, 'Existing campus type')
        else:
            assert '学位论文原创性声明' in text, (name, 'Graduate declaration')
    print(name + ': PASS')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime', type=Path, default=ROOT)
    parser.add_argument('--work', type=Path, default=ROOT / 'tests/output/bachelor')
    parser.add_argument('--fontset', default='fandol')
    args = parser.parse_args()
    for case in CASES:
        compile_case(args.runtime.resolve(), args.work.resolve(), *case, args.fontset)


if __name__ == '__main__':
    main()
