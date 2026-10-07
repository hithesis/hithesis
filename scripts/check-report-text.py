#!/usr/bin/env python3
"""检查深圳本科报告封面能否提取校名和报告名称。

用法：python3 scripts/check-report-text.py --stage opening path/to/report.pdf
需要 Poppler 的 pdftotext；不依赖本机中文字体，不进行 OCR。
"""

import argparse
from pathlib import Path
import shutil
import subprocess


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage', choices=['opening', 'midterm'], required=True)
    parser.add_argument('pdf', type=Path)
    args = parser.parse_args()
    if not args.pdf.is_file():
        parser.error(f'找不到 PDF：{args.pdf}')
    extractor = shutil.which('pdftotext')
    if extractor is None:
        parser.error('请先安装 Poppler 的 pdftotext 工具')
    result = subprocess.run(
        [extractor, '-f', '1', '-l', '1', '-enc', 'UTF-8', str(args.pdf.resolve()), '-'],
        capture_output=True, text=True, encoding='utf-8', errors='replace',
    )
    if result.returncode:
        parser.exit(1, f'封面文字提取失败：\n{result.stderr}')
    text = ''.join(result.stdout.split())
    stage = '开题' if args.stage == 'opening' else '中期'
    expected = ['哈尔滨工业大学深圳校区', f'毕业论文（设计）{stage}报告']
    missing = [title for title in expected if title not in text]
    if missing:
        parser.exit(1, '封面缺少可提取文字：' + '、'.join(missing) + '\n')
    print(f'封面文字检查通过：{args.pdf}')


if __name__ == '__main__':
    main()
