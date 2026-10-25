"""Verify the exact PDF required by a development publication and notification."""
import hashlib
import importlib.util
import json
from pathlib import Path
import re

AI_LABEL = '此预览由 AI 比对生成'
MAX_PDF_BYTES = 20 * 1024 * 1024


def report_style():
    spec = importlib.util.spec_from_file_location('dev_report_style', Path(__file__).with_name('dev-report-style.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def identity(info):
    fields = {name: info.get(name, '') for name in
              ('build_id', 'commit', 'source_commit', 'source_sha256', 'version', 'published_on')}
    return hashlib.sha256(json.dumps(fields, sort_keys=True).encode()).hexdigest()


def validate(path, info):
    # Import PDF readers only when a real publication/notification is validated.
    from pypdf import PdfReader
    import pypdfium2 as pdfium
    path = Path(path)
    if not path.is_file():
        raise ValueError('PDF required: DEV_UPDATE.pdf is missing; publication is blocked')
    data = path.read_bytes()
    if not 1024 <= len(data) <= MAX_PDF_BYTES or not data.startswith(b'%PDF-'):
        raise ValueError('PDF required: invalid or oversized update PDF')
    try:
        reader = PdfReader(path, strict=True)
        if reader.is_encrypted or not 1 <= len(reader.pages) <= 24:
            raise ValueError('Encrypted, empty or excessively long PDF')
        if not reader.metadata or reader.metadata.subject != 'hithesis-report:' + identity(info):
            raise ValueError('PDF does not belong to this source/build identity')
        style = report_style()
        marker = reader.metadata.keywords or ''
        if marker.startswith('hithesis-dev-report-') and marker != style.PDF_MARKER:
            raise ValueError('Unsupported PDF report format')
        fixed = marker == style.PDF_MARKER
        declared_format = info.get('report', {}).get('format_version')
        if declared_format is not None and (type(declared_format) is not int or not fixed or declared_format != style.FORMAT_VERSION):
            raise ValueError('PDF report format does not match its manifest')
        with pdfium.PdfDocument(path) as document:
            first = document[0]
            text_page = first.get_textpage()
            text = text_page.get_text_range()
            text_page.close()
            first.close()
            all_text = text
            if fixed:
                for index in range(1, len(document)):
                    page = document[index]
                    text_page = page.get_textpage()
                    all_text += '\n' + text_page.get_text_range()
                    text_page.close()
                    page.close()
        compact = ''.join(text.split())
        for value in (AI_LABEL, info['label'], info['published_on']):
            if ''.join(value.split()) not in compact:
                raise ValueError('PDF missing AI label, version or date')
        if len(compact) < 80:
            raise ValueError('PDF has no substantive update content')
        if fixed:
            complete = ''.join(all_text.split())
            positions = [complete.find(heading) for heading in style.HEADINGS]
            if any(position < 0 for position in positions) or positions != sorted(positions):
                raise ValueError('PDF missing or reordering the fixed report sections')
    except Exception as error:
        raise ValueError('PDF required: validation failed: ' + str(error)) from error
    return {'identity': identity(info), 'sha256': hashlib.sha256(data).hexdigest(),
            'size': len(data), 'pages': len(reader.pages), 'ai_label': AI_LABEL,
            **({'format_version': style.FORMAT_VERSION} if fixed else {})}


def manifest(info):
    style = report_style()
    if info.get('schema') != 2:
        raise ValueError('PDF required: invalid development-build schema')
    for field, pattern in (('commit', r'[0-9a-f]{40}'), ('source_commit', r'[0-9a-f]{40}'),
                           ('source_sha256', r'[0-9a-f]{64}'), ('version', r'v\d+\.\d+[a-z]?'),
                           ('published_on', r'\d{4}-\d{2}-\d{2}')):
        if not re.fullmatch(pattern, info.get(field, '')):
            raise ValueError('PDF required: missing or invalid source/build identity')
    report = info.get('report') or {}
    version = report.get('format_version', style.FORMAT_VERSION)
    if type(version) is not int or version != style.FORMAT_VERSION:
        raise ValueError('Unsupported report manifest format')
    if report.get('filename') != 'DEV_UPDATE.pdf':
        raise ValueError('PDF required: missing update PDF manifest')
    build_id = info.get('build_id', '')
    if not re.fullmatch(r'dev-\d{8}-[0-9a-f]{12}-\d+-\d+', build_id):
        raise ValueError('Invalid report build identifier')
    date = info['published_on'].replace('-', '')
    if not build_id.startswith('dev-' + date + '-' + info['commit'][:12] + '-'):
        raise ValueError('PDF build does not match the source/date')
    if info.get('label') != info['version'] + '-dev.' + date[4:]:
        raise ValueError('PDF label does not match the source/date')
    url = f'https://hithesis.site/dev-builds/{build_id}/DEV_UPDATE.pdf'
    if info.get('release_url') != f'https://hithesis.site/dev-builds/{build_id}/':
        raise ValueError('PDF build page does not match this build')
    if report.get('url') != url or report.get('identity') != identity(info):
        raise ValueError('PDF manifest does not match this release')
    if not re.fullmatch(r'[0-9a-f]{64}', report.get('sha256', '')):
        raise ValueError('PDF required: missing PDF checksum')
    if report.get('model') != 'deepseek-flash' or not re.fullmatch(r'[0-9a-f]{64}', report.get('input_sha256', '')):
        raise ValueError('PDF required: missing DeepSeek comparison provenance')
    return report


def publication(directory, info):
    report = manifest(info)
    checked = validate(Path(directory) / 'DEV_UPDATE.pdf', info)
    record = info.get('files', {}).get('DEV_UPDATE.pdf', {})
    if report['sha256'] != checked['sha256'] or record.get('sha256') != checked['sha256']:
        raise ValueError('PDF required: report/asset checksum mismatch')
    if record.get('size') != checked['size']:
        raise ValueError('PDF required: report/asset size mismatch')
    return checked
