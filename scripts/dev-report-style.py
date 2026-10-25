"""One report contract shared by the prompt, validator, renderer and PDF gate."""
import json
from pathlib import Path
import re

FORMAT_VERSION = 1
PDF_MARKER = 'hithesis-dev-report-v1'
REPORT_TITLE = 'hiThesis 开发版更新说明'
DOWNLOAD_URL = 'https://hithesis.site/download.html?version=dev'
HEADINGS = ('本次概览', '更新内容', '升级提示', '下载与手册')
KINDS = ('新增', '修复', '调整', '维护')
ACTIONS = {'none': '无需修改现有写法。', 'optional': '可按需调整。',
           'required': '需要修改。', 'unknown': '尚无已确认的改稿步骤。'}
LIMITS = {'summary': 180, 'message': 500, 'title': 24, 'description': 280,
          'impact': 100, 'migration': 180}
MAX_SECTIONS = 8
MAX_SENTENCE = 100
GUIDE = Path(__file__).resolve().parents[1] / 'release-notes/STYLE.md'
BANNED = ('重磅', '全面升级', '赋能', '保驾护航', '焕然一新', '显著提升', '大幅提升',
          '极大提升', '一站式', '更上一层楼', '值得注意的是', '综上所述', '总而言之',
          '全面兼容', '绝对稳定', '敬请期待', '作为 AI', '作为人工智能')
INTERNAL = re.compile(r'\b(?:CI|PR|SHA|Validation|Compatibility)\b|GitHub Actions|'
                      r'版本(?:计算|算法)|提交(?:哈希|散列)|\b[0-9a-f]{12,64}\b', re.I)
MARKUP = re.compile(r'(?m)^\s*(?:#{1,6}\s|[-*]\s|\d+[.)、]\s*)|```|!\[|<[^>]+>|`|https?://|\[CQ:')
MIXED_SPACING = re.compile(r'[\u3400-\u9fff][A-Za-z0-9]|[A-Za-z0-9][\u3400-\u9fff]')


def prompt():
    schema = {'format_version': FORMAT_VERSION, 'summary': '本次实际变化', 'message': '发群摘要，不含链接',
              'sections': [{'kind': '新增|修复|调整|维护', 'title': '简短标题',
                            'description': '具体变化', 'impact': '有证据的适用范围，不明确可空',
                            'action': 'none|optional|required|unknown',
                            'migration': '已确认的操作步骤；none/unknown 时必须为空',
                            'evidence_ids': ['change-1'], 'example_ids': [], 'comparison_ids': []}]}
    return ('\n' + GUIDE.read_text() + '\n输出契约：只返回 JSON 对象，不附其他字段。\n' +
            json.dumps(schema, ensure_ascii=False) + '\n各文字字段最大字符数：' +
            json.dumps(LIMITS, ensure_ascii=False) + f'。条目 1 到 {MAX_SECTIONS} 条，每句最多 {MAX_SENTENCE} 字。\n'
            'summary 和条目字段均为单段纯文本；message 最多三个短段落。'
            'optional/required 必须填写 migration，并引用已确认示例或维护者给出的操作步骤。'
            'required 必须引用 breaking_evidence_ids；其他情况不能把旧稿处理写成必须修改。'
            '所有 change-* 证据必须覆盖，同一 change-* 只在一条中解释。')


def text(field, value):
    if not isinstance(value, str) or len(value) > LIMITS[field] or value != value.strip():
        raise ValueError('Invalid or overlong report field: ' + field)
    if field != 'message' and '\n' in value:
        raise ValueError('Report field must be a single paragraph: ' + field)
    if field == 'message' and len([line for line in value.splitlines() if line.strip()]) > 3:
        raise ValueError('Report message must fit three short paragraphs')
    if '\\' in value or MARKUP.search(value):
        raise ValueError('Report prose must be plain text; reference reviewed example IDs for code')
    if INTERNAL.search(value):
        raise ValueError('Report prose contains internal maintenance information')
    if MIXED_SPACING.search(value):
        raise ValueError('Add a space between Chinese and Latin text/numbers: ' + field)
    if any(phrase in value for phrase in BANNED):
        raise ValueError('Report prose contains prohibited promotional or filler wording')
    if any(len(sentence.strip()) > MAX_SENTENCE for sentence in re.split(r'[。！？!?；;\n]', value)):
        raise ValueError('Report sentence is too long: ' + field)
    if field == 'title' and re.search(r'[。！？!?：:]$', value):
        raise ValueError('Report title must not end with sentence punctuation')


def validate(draft, data):
    if not isinstance(draft, dict) or set(draft) != {'format_version', 'summary', 'message', 'sections'}:
        raise ValueError('AI draft must match the fixed report schema')
    if type(draft['format_version']) is not int or draft['format_version'] != FORMAT_VERSION:
        raise ValueError('Unsupported report format version')
    for field in ('summary', 'message'):
        text(field, draft[field])
        if not draft[field]:
            raise ValueError('Empty report ' + field)
    sections = draft['sections']
    if not isinstance(sections, list) or not 1 <= len(sections) <= MAX_SECTIONS:
        raise ValueError('Invalid number of AI report sections')
    expected = {'kind', 'title', 'description', 'impact', 'action', 'migration',
                'evidence_ids', 'example_ids', 'comparison_ids'}
    titles, changes, required_actions = set(), set(), set()
    breaking = set(data.get('breaking_evidence_ids', []))
    for section in sections:
        if not isinstance(section, dict) or set(section) != expected:
            raise ValueError('AI section contains unsupported fields')
        if not isinstance(section['kind'], str) or section['kind'] not in KINDS or \
                not isinstance(section['action'], str) or section['action'] not in ACTIONS:
            raise ValueError('Invalid report kind or old-draft action')
        for field in ('title', 'description', 'impact', 'migration'):
            text(field, section[field])
        if not section['title'] or not section['description']:
            raise ValueError('AI section needs a title and description')
        title = section['title'].casefold()
        if title in titles:
            raise ValueError('Duplicate update title')
        titles.add(title)
        for field in ('evidence_ids', 'example_ids', 'comparison_ids'):
            if not isinstance(section[field], list) or any(not isinstance(ref, str) for ref in section[field]):
                raise ValueError('Report references must be ID lists')
            if len(section[field]) != len(set(section[field])):
                raise ValueError('Duplicate report reference')
        refs = set(section['evidence_ids'])
        if not refs:
            raise ValueError('AI report section needs evidence')
        current = {ref for ref in refs if ref.startswith('change-')}
        if changes & current:
            raise ValueError('A change must not be repeated in multiple sections')
        changes |= current
        action = section['action']
        if action in ('none', 'unknown') and section['migration']:
            raise ValueError('none/unknown actions cannot invent migration steps')
        if action in ('optional', 'required') and not section['migration']:
            raise ValueError('Confirmed old-draft actions need migration steps')
        if action == 'required' and not refs & breaking:
            raise ValueError('Required migration needs reviewed breaking evidence')
        if action == 'required':
            required_actions |= refs & breaking
    required = {e['id'] for e in data['evidence'] if e['id'].startswith('change-')}
    if not required <= changes:
        raise ValueError('AI omitted a recorded user-facing change')
    if not breaking <= required_actions:
        raise ValueError('AI omitted required old-draft handling for a reviewed breaking change')
    return draft
