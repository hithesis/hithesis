"""Build a Chinese PDF/Markdown update report from recorded changes and commit metadata."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import shutil

NOTES = Path(__file__).resolve().parents[1] / 'release-notes/notes.json'
AI_LABEL = '此预览由 AI 比对生成'


def load(name):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name(name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def escape(text):
    replacements = {'\\': r'\textbackslash{}', '{': r'\{', '}': r'\}',
                    '#': r'\#', '$': r'\$', '%': r'\%', '&': r'\&', '_': r'\_',
                    '^': r'\textasciicircum{}', '~': r'\textasciitilde{}'}
    return ''.join(replacements.get(char, char) for char in str(text))


def breaking_details(commit):
    match = re.search(r'(?ims)^BREAKING[ -]CHANGE:[^\S\n]*(.*?)'
                      r'(?=^[A-Za-z][A-Za-z -]+:[^\S\n]|\Z)', commit['body'])
    description = match[1].strip() if match else ''
    if not description and not commit.get('migration'):
        return []
    lines = ['不兼容变化：' + description]
    if commit.get('impact'):
        lines += ['影响范围：' + commit['impact']]
    if commit.get('migration'):
        lines += ['怎么改：' + commit['migration']]
    return lines


def contents(info, commits):
    style = load('dev-report-style')
    normalize = lambda value: ' '.join(value.split())
    changes = {normalize(c.get('tex') or c['text']): c for c in info['changes']}
    notes = [note for note in json.loads(NOTES.read_text()) if normalize(note['change']) in changes] if NOTES.exists() else []
    covered = {normalize(note['change']) for note in notes}
    preview = info.get('preview', False)
    sections = []
    summary = info.get('summary', '本次更新的具体变化、适用范围和旧稿处理见下文。')
    if info.get('ai_draft'):
        draft = info['ai_draft']
        if draft.get('format_version') != style.FORMAT_VERSION:
            raise ValueError('Unsupported update report format')
        examples = {item['id']: item['code'] for item in info['ai_examples']}
        summary = draft['summary']
        for section in draft['sections']:
            sections.append(section | {'code': [examples[identifier] for identifier in section['example_ids']],
                                       'comparisons': section['comparison_ids']})
    else:
        for note in notes:
            sections.append({'kind': '调整', 'title': note['title'],
                'description': note['text'] + (' ' + note['after'] if note.get('after') else ''),
                'impact': note.get('impact', ''), 'action': 'optional' if note.get('upgrade') else 'unknown',
                'migration': note.get('upgrade', ''), 'code': [note['code']] if note.get('code') else [], 'comparisons': []})
        for commit in info.get('version_plan', {}).get('breaking_commits', []):
            details = breaking_details(commit)
            if details:
                sections.append({'kind': '调整', 'title': '不兼容用法调整', 'description': details[0],
                    'impact': commit.get('impact', ''), 'action': 'required' if commit.get('migration') else 'unknown',
                    'migration': commit.get('migration', ''), 'code': [], 'comparisons': []})
        remaining = [change['text'] for key, change in changes.items() if key not in covered]
        public = []
        for commit in commits:
            match = re.search(r'(?ims)^Release-Notes:[^\S\n]*(.*?)'
                              r'(?=^[A-Za-z][A-Za-z -]+:[^\S\n]|\Z)', commit['body'])
            if match and match[1].strip():
                public.append(match[1].strip())
        if remaining or public:
            sections.append({'kind': '维护', 'title': '其他更新', 'description': '；'.join(remaining + public),
                'impact': '', 'action': 'unknown', 'migration': '', 'code': [], 'comparisons': []})
    if not sections:
        sections.append({'kind': '维护', 'title': '维护更新', 'description': '本次没有登记用户可见的模板变化。',
            'impact': '', 'action': 'unknown', 'migration': '', 'code': [], 'comparisons': []})
    lines = [f'# {style.REPORT_TITLE} · {info["label"]}', '',
             ('预览日期：' if preview else '更新日期：') + info['published_on'] + '（北京时间）', AI_LABEL, '',
             '## ' + style.HEADINGS[0], '', summary, '', '## ' + style.HEADINGS[1], '']
    for section in sections:
        lines += ['### ' + section['kind'] + ' · ' + section['title'], '',
                  '变化：' + section['description'], '',
                  '适用范围：' + (section['impact'] or '影响范围尚未确认。'), '',
                  '旧稿处理：' + style.ACTIONS[section['action']] + section['migration'], '']
        for code in section['code']:
            lines += ['使用示例：', '', '```latex', *code, '```', '']
        if section['comparisons']:
            lines += ['对照结果：', '']
            for identifier in section['comparisons']:
                lines += ['[[comparison:' + identifier + ']]', '']
    lines += ['## ' + style.HEADINGS[2], '',
              '按各条目的“旧稿处理”决定是否修改论文；命令和参数以本版用户手册为准。', '',
              '## ' + style.HEADINGS[3], '']
    if preview:
        lines += ['预览稿，尚未发布。', '']
    else:
        lines += ['模板下载：', style.DOWNLOAD_URL, '', '本版用户手册：',
                  info.get('manual', {}).get('url', info['release_url'] + 'hithesis.pdf'), '',
                  '本次发布记录：', info['release_url'], '']
    return '\n'.join(lines)


def latex(markdown, info=None, comparisons=None):
    style = load('dev-report-style')
    lines = [r'\documentclass[UTF8,fontset=fandol,10pt]{ctexart}',
             r'\usepackage[a4paper,margin=20mm]{geometry}',
             r'\usepackage{xcolor,enumitem,graphicx}',
             r'\usepackage[unicode,colorlinks,urlcolor=blue!55!black]{hyperref}',
             r'\setlength{\parindent}{0pt}\setlength{\parskip}{3pt}',
             r'\ctexset{section={format=\large\bfseries\raggedright,beforeskip=8pt,afterskip=4pt}}',
             r'\setlist{nosep,leftmargin=1.5em}', r'\emergencystretch=3em',
             r'\hypersetup{pdfkeywords={' + style.PDF_MARKER + '}}',
             r'\pagestyle{plain}', r'\begin{document}']
    if info:
        digest = load('dev-report-gate').identity(info)
        lines.insert(-1, r'\hypersetup{pdfsubject={hithesis-report:' + digest + '}}')
    comparisons = {c['id']: c for c in comparisons or []}
    code = False
    for line in markdown.splitlines():
        if line.startswith('```'):
            lines.append(r'\end{quote}' if code else r'\begin{quote}\small\ttfamily\raggedright\setlength{\parskip}{0pt}')
            code = not code
        elif code:
            indent = len(line) - len(line.lstrip(' '))
            lines.append(r'\noindent\hspace*{' + str(indent * .5) + 'em}' + escape(line.lstrip(' ')) + r'\par')
        elif match := re.fullmatch(r'\[\[comparison:([a-z][a-z0-9-]+)\]\]', line):
            identifier = match[1]
            if identifier not in comparisons:
                raise ValueError('Unregistered comparison image')
            image = comparisons[identifier]
            placement = '左侧为旧版，右侧为本次' if image.get('layout') != 'stacked' else '上方为旧版，下方为本次'
            diagnostic = ('旧版未定义 ' + '、'.join(image['unsupported_commands']) + '，旧版一侧显示缺少命令的提示。') \
                if image.get('before_status') == 'unsupported' else ''
            if image.get('before_status') == 'compile-error':
                diagnostic = '旧版编译此例失败，左侧显示编译错误。'
            lines += [r'\begin{center}\includegraphics[width=\linewidth,height=.6\textheight,keepaspectratio]{comparison-' + identifier + '.png}',
                       r'\par{\small ' + escape(image['title']) + '。新旧模板使用同一示例，' + placement + '。' +
                       escape(diagnostic) + r'}\end{center}']
        elif line.startswith('# '):
            lines.append(r'{\LARGE\bfseries ' + escape(line[2:]) + r'\par}\bigskip')
        elif line.startswith('## '):
            lines.append(r'\section*{' + escape(line[3:]) + '}')
        elif line.startswith('### '):
            lines.append(r'\subsection*{' + escape(line[4:]) + '}')
        elif 'https://' in line:
            linked = ''.join(r'\url{' + escape(part) + '}' if part.startswith('https://') else escape(part)
                             for part in re.split(r'(https://\S+)', line))
            lines.append(r'{\small ' + linked + r'\par}')
        else:
            lines.append(escape(line) + r'\par')
    lines.append(r'\end{document}')
    return '\n'.join(lines) + '\n'


def build(info, commits, directory, ai_required=False):
    directory = directory.resolve()
    work = directory / 'report-build'
    work.mkdir(exist_ok=False)
    comparisons, record = [], {}
    if ai_required:
        preview = load('dev-previews').build(info, work / 'previews')
        comparisons = preview['comparisons']
        texts = {' '.join((c.get('tex') or c['text']).split()) for c in info['changes']}
        notes = [n for n in json.loads(NOTES.read_text()) if ' '.join(n['change'].split()) in texts]
        editor = load('dev-ai')
        data = editor.packet(info, commits, notes, comparisons, preview['evidence'])
        (work / 'AI_INPUT.json').write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
        record = editor.generate(data, comparisons, directory)
        info = info | {'ai_draft': record['draft'], 'ai_examples': data['examples']}
        for comparison in comparisons:
            shutil.copy2(comparison['image'], work / ('comparison-' + comparison['id'] + '.png'))
    markdown = contents(info, commits)
    public_markdown = re.sub(r'\[\[comparison:[a-z][a-z0-9-]+\]\]', '排版前后对照图见同版 PDF 附件。', markdown)
    (directory / 'DEV_UPDATE.md').write_text(public_markdown, encoding='utf-8')
    (work / 'DEV_UPDATE.tex').write_text(latex(markdown, info, comparisons), encoding='utf-8')
    with (work / 'compile.log').open('w') as output:
        for _ in range(2):
            subprocess.run(['xelatex', '-no-shell-escape', '-interaction=nonstopmode',
                            '-halt-on-error', 'DEV_UPDATE.tex'], cwd=work, check=True,
                           env={k: v for k, v in os.environ.items() if k not in ('DEV_REPORT_API_KEY', 'GH_TOKEN', 'GITHUB_TOKEN')},
                           stdout=output, stderr=subprocess.STDOUT, timeout=180)
    log = (work / 'DEV_UPDATE.log').read_text()
    if 'Missing character:' in log:
        raise ValueError('Update report contains missing glyphs; inspect ' + str(work))
    (directory / 'DEV_UPDATE.pdf').write_bytes((work / 'DEV_UPDATE.pdf').read_bytes())
    checked = load('dev-report-gate').validate(directory / 'DEV_UPDATE.pdf', info)
    print('PDF update report built:', directory / 'DEV_UPDATE.pdf')
    return {'validation': checked, 'model': record.get('model'),
            'input_sha256': record.get('input_sha256'),
            'message': record.get('draft', {}).get('message', '')}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--commits', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    build(json.loads(args.manifest.read_text()), json.loads(args.commits.read_text()), args.output)
