"""Compile this release's five preview cases and a report using a mocked AI response."""
import argparse
import base64
import hashlib
import importlib.util
import io
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pypdfium2 as pdfium

ROOT = Path(__file__).resolve().parents[1]


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts' / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def text(path):
    parts = []
    with pdfium.PdfDocument(path) as pdf:
        for page in pdf:
            content = page.get_textpage()
            parts.append(content.get_text_range())
            content.close()
            page.close()
    return ''.join(''.join(parts).split())


def preview_draft(notes, records, format_version):
    descriptions = {
        'pdf-properties': ('新增', '论文信息可用于填写 PDF 标题、作者和关键词。'),
        'beijing-date': ('调整', '自动日期按北京时间换算，跨日时显示对应日期。'),
        'url': ('调整', '正文和参考文献的 URL 字符间距默认不拉伸。'),
        'example-11': ('新增', '新增列表式符号表，条目可以自动换页。'),
        'example-12': ('新增', '新增公式符号说明环境，说明可以折行和跨页。'),
    }
    sections = []
    for index, note in enumerate(notes, 1):
        record = next(r for r in records.values() if r['change'] == note['change'])
        kind, description = descriptions[record['id']]
        sections.append({'kind': kind, 'title': note['title'], 'description': description,
                         'impact': '', 'action': 'none', 'migration': '',
                         'evidence_ids': [f'change-{index}', 'preview-' + record['id']],
                         'example_ids': [f'example-{index}'] if note.get('code') else [],
                         'comparison_ids': [record['id']] if record['status'] == 'changed' else []})
    return {'format_version': format_version,
            'summary': '本次检查了 PDF 属性、日期、URL 和两种符号说明的实际结果。',
            'message': '本次更新的用法和实际效果见 PDF。', 'sections': sections}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work', type=Path, required=True)
    parser.add_argument('--baseline', default='46e43590ae23e44ee32b1ee488f8bbe8fa50fa8b')
    args = parser.parse_args()
    args.work.mkdir(parents=True, exist_ok=False)
    previews, report, ai = load('dev-previews'), load('dev-report'), load('dev-ai')
    notes = json.loads(previews.NOTES.read_text())[-5:]
    commit = ai.git('rev-parse', 'HEAD').strip()
    info = {'label': 'v3.2b-dev.1026', 'version': 'v3.2b', 'published_on': '2026-10-26',
            'build_id': 'dev-20261026-' + commit[:12] + '-1-1', 'commit': commit,
            'source_commit': commit, 'source_sha256': hashlib.sha256((ROOT / 'hithesis.dtx').read_bytes()).hexdigest(),
            'preview': True, 'previous_source_commit': args.baseline,
            'version_plan': {'official_release': {'tag': 'v3.2a'}},
            'changes': [{'text': note['change']} for note in notes]}
    result = previews.build(info, args.work / 'previews')
    records = {record['id']: record for record in result['coverage']}
    assert len(records) == 5 and all(r['status'] != 'no-reviewed-example' for r in records.values())
    properties = records['pdf-properties']
    assert properties['status'] == 'no-visual-change', properties
    assert properties['before_properties']['Title'] == '', properties
    assert properties['after_properties']['Title'] == '文档属性示例', properties
    assert properties['after_properties']['Author'] == '张三', properties
    assert all(word in properties['after_properties']['Keywords'] for word in ('alpha', 'beta'))
    assert records['url']['after_values'] == {'url-body': '0.0mu', 'url-bibliography': '0.0mu'}
    # This baseline also uses zero glue in the fixture; report that honestly.
    assert records['url']['before_values'] == {'url-body': '0.0mu', 'url-bibliography': '0.0mu'}
    for identifier in ('example-11', 'example-12'):
        assert records[identifier]['before_status'] == 'unsupported', records[identifier]
        assert records[identifier]['status'] == 'changed', records[identifier]
    assert '2026年10月25日' in text(args.work / 'previews/beijing-date-before/main.pdf')
    assert '2026年10月26日' in text(args.work / 'previews/beijing-date-after/main.pdf')
    comparisons = result['comparisons']
    assert {'example-11', 'example-12', 'beijing-date'} <= {c['id'] for c in comparisons}
    assert not {'keywords', 'english-cover', 'pdf-properties'} & {c['id'] for c in comparisons}
    sheets = {c['ai_image'] for c in comparisons}
    assert len(sheets) <= 2 and all(Path(path).stat().st_size < 3 * 1024 * 1024 for path in sheets)
    failure_source = previews.document(r'\ifcsname eqdenote\endcsname Supported.\else\UnknownPreviewCommand\fi')
    failed = args.work / 'old-compile-error'
    assert previews.compile_case(args.work / 'previews/baseline', failure_source, failed, allow_failure=True) is None
    successful = previews.compile_case(ROOT, failure_source, args.work / 'new-compile-success')
    diagnostic = previews.compiler_error((failed / 'main.log').read_text())
    assert 'Undefined control sequence' in diagnostic
    counts, pages = previews.pictures(None, successful, args.work / 'compile-error.png', diagnostic)
    assert counts == [0, 1] and pages == [1]
    draft = preview_draft(notes, records, ai.style.FORMAT_VERSION)
    response = {'choices': [{'finish_reason': 'stop', 'message': {'content': json.dumps(draft)}}]}
    opener = Mock()
    encoded = json.dumps(response).encode()
    opener.open.side_effect = lambda *_args, **_kwargs: io.BytesIO(encoded)
    output = args.work / 'report'
    output.mkdir()
    original_load = report.load
    def modules(name):
        if name == 'dev-previews':
            return SimpleNamespace(build=lambda *_: result)
        return ai if name == 'dev-ai' else original_load(name)
    with patch.object(report, 'load', side_effect=modules), \
            patch.object(ai, 'build_opener', return_value=opener), \
            patch.dict(ai.os.environ, {'DEV_REPORT_API_KEY': 'test-only'}):
        built = report.build(info, [], output, ai_required=True)
    opener.open.assert_called_once()
    request = json.loads(opener.open.call_args.args[0].data)
    content = request['messages'][1]['content']
    assert sum(part['type'] == 'image_url' for part in content) == len(sheets)
    sent_images = {part['image_url']['url'].split(',', 1)[1] for part in content if part['type'] == 'image_url'}
    assert sent_images == {base64.b64encode(Path(path).read_bytes()).decode() for path in sheets}
    identifiers = {identifier for part in content if part['type'] == 'text' and part['text'].startswith('comparison_ids: ')
                   for identifier in part['text'].removeprefix('comparison_ids: ').split(', ')}
    assert identifiers == {c['id'] for c in comparisons}
    rendered = text(output / 'DEV_UPDATE.pdf')
    assert '旧版未定义' in rendered and 'symbols' in rendered and 'eqdenote' in rendered
    assert '此预览由AI比对生成' in rendered
    (args.work / 'results.json').write_text(json.dumps(
        {'status': 'PASS', 'cases': 5, 'comparisons': len(comparisons), 'ai_images': len(sheets),
         'report': built['validation']}, ensure_ascii=False, indent=2) + '\n')
    print('Daily previews: five real cases, metadata evidence, new-command diagnostics and mock AI/PDF flow PASS')


if __name__ == '__main__':
    main()
