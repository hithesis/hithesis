"""Compile a real bilingual update PDF and verify its text, links and page bounds."""
import argparse
from datetime import datetime
import importlib.util
import json
import io
from pathlib import Path
from unittest.mock import patch

import pypdfium2 as pdfium
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts' / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work', type=Path, default=ROOT / 'build' /
        ('dev-report-' + datetime.now().strftime('%Y%m%d-%H%M%S-%f')))
    args = parser.parse_args()
    args.work.mkdir(parents=True, exist_ok=False)
    releases, versions, report = load('dev-release'), load('dev-version'), load('dev-report')
    message = ('feat(keywords): change the default alignment\n\n'
        'Release-Notes: 关键词续行默认不再悬挂，旧用法继续支持。\n'
        'Impact: 使用多行关键词的中英文论文。\n'
        'Migration: 使用 \\hitsetup{keywords-hanging=true} 恢复旧版式。\n'
        'Validation: 关键词 PDF 几何与旧接口回归通过。')
    commit = {'sha': 'a' * 40, 'subject': message.splitlines()[0], 'body': message,
              'breaking': False, 'migration': versions.footer(message, 'Migration'),
              'impact': versions.footer(message, 'Impact'), 'validation': versions.footer(message, 'Validation')}
    official = versions.official_release([{'tag_name': 'v3.2a', 'published_at': '2026-10-12',
                                           'draft': False, 'prerelease': False}])
    info = releases.metadata('v3.2b', 'b' * 40, datetime.fromisoformat('2026-10-25T01:00:00+00:00'), 1, 1, 1)
    info.update(source_commit='a' * 40, compare_url='https://github.com/hithesis/hithesis/compare/v3.2a...dev',
        source_sha256='f' * 64,
        version_plan=versions.resolve(official, 'v3.2b', {}, [commit]),
        changes=[{'text': '增加 keywords-hanging 开关，关键词续行默认不再悬挂。'},
                 {'text': r'保留命令 \caption{中文}[English] 及文件名 example_1.tex，支持 50% 的示例文本。'}])
    built = report.build(info, [commit], args.work)
    assert info['version_plan']['version'] == 'v3.2b' and not info['version_plan']['breaking']
    gate, notifier = load('dev-report-gate'), load('notify-dev')
    checked = built['validation']
    info['report'] = {'filename': 'DEV_UPDATE.pdf', 'url': info['release_url'] + 'DEV_UPDATE.pdf',
                      **checked, 'model': 'deepseek-flash', 'input_sha256': 'c' * 64}
    info['files'] = {'DEV_UPDATE.pdf': {'sha256': checked['sha256'], 'size': checked['size']}}
    gate.publication(args.work, info)
    with patch.object(notifier, 'urlopen', return_value=io.BytesIO((args.work / 'DEV_UPDATE.pdf').read_bytes())):
        notifier.verify_report(info)
    reader = PdfReader(args.work / 'DEV_UPDATE.pdf')
    parts = []
    with pdfium.PdfDocument(args.work / 'DEV_UPDATE.pdf') as pdf:
        for page in pdf:
            text_page = page.get_textpage()
            parts.append(text_page.get_text_range())
            text_page.close()
            page.close()
    text = '\n'.join(parts)
    compact = ''.join(text.split())
    for expected in ['v3.2b-dev.1025', gate.AI_LABEL, '续行与正文左边界对齐',
                     r'\hitsetup{keywords-hanging=true}', 'example_1.tex', '50%']:
        assert ''.join(expected.split()) in compact, (expected, text)
    for internal in ['正式基准', '第二位上限', '源码提交', '构建与验证日志', 'Validation:', info['commit'], info['run_url']]:
        assert internal not in text, (internal, text)
    links = [str(ref.get_object().get('/A', {}).get('/URI', ''))
             for page in reader.pages for ref in page.get('/Annots', [])]
    assert 'https://hithesis.site/?version=dev' in links and info['release_url'] in links
    with pdfium.PdfDocument(args.work / 'DEV_UPDATE.pdf') as pdf:
        for index, page in enumerate(pdf):
            text_page = page.get_textpage()
            boxes = [text_page.get_charbox(i) for i in range(text_page.count_chars())
                     if text_page.get_text_range(i, 1).strip()]
            assert all(40 <= left <= right <= page.get_width() - 40 and
                       20 <= bottom <= top <= page.get_height() - 40
                       for left, bottom, right, top in boxes), ('Text outside page bounds', index + 1)
            if index == 0:
                page.render(scale=1.3).to_pil().save(args.work / 'preview.png')
            text_page.close()
            page.close()
    (args.work / 'results.json').write_text(json.dumps({'status': 'PASS', 'pages': len(reader.pages),
        'pdf': str(args.work / 'DEV_UPDATE.pdf'), 'links': len(links)}, ensure_ascii=False, indent=2) + '\n')
    print('Dev update PDF: text, TeX literals, migration, links and page bounds PASS;', len(reader.pages), 'pages')


if __name__ == '__main__':
    main()
