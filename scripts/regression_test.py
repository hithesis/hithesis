#!/usr/bin/env python3
"""排版回归测试。

下载上一个正式 release 对应 tag 的源码存档，在里面跑一遍 latex hithesis.ins 生成
那一版的 .cls，用同一套 TeX Live 环境重编一遍，再跟当前工作树编出来的 PDF 逐页比。
两侧环境一样，比出来的差异就只可能来自模板改动。

参照物取的是 tag 的源码存档，不是 release 挂的资产。资产是人手动传的，传错了
（比如拿别的分支打的包）工具照样一片绿，比不检查还危险。

用法::

    scripts/regression_test.py                  # 本地跑全量，逐个人工确认
    scripts/regression_test.py --quick          # 只跑 tests/quick-set.txt 里的
    scripts/regression_test.py --against v3.1e  # 指定参照版本
    scripts/regression_test.py --ci             # CI 用，不交互，出报告和差异图

退出码::

    0   没差异
    1   有排版差异
    2   编译失败或者别的错
    3   跳过，没找到能当参照的 tag

只用标准库。差在第几页靠 ghostscript 渲染 PNG 逐页比出来，装了 ImageMagick 还会
叠出标红的差异图。diff-pdf 是可选的，本地装了才能逐页叠加着翻。
"""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CACHE_DIR = ROOT / "target" / "regression-cache"
RUN_DIR = ROOT / "target" / "regression"
REPORT_DIR = RUN_DIR / "report"

EXIT_OK, EXIT_DIFF, EXIT_ERROR, EXIT_SKIP = 0, 1, 2, 3


# ---------------------------------------------------------------- 变体定义


class Variant:
    """tests/variants/*.conf 里的一条。"""

    def __init__(self, name: str, conf: Path) -> None:
        self.name = name
        values = {}
        for line in conf.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            values[key.strip()] = value.strip()
        self.base = values["BASE"]
        self.entry = values.get("ENTRY", "thesis.tex")

    @property
    def pdf_name(self) -> str:
        return self.entry[:-4] + ".pdf" if self.entry.endswith(".tex") else self.entry + ".pdf"


def load_variants(selected: str | None, quick: bool) -> list[Variant]:
    conf_dir = ROOT / "tests" / "variants"
    names = sorted(p.stem for p in conf_dir.glob("*.conf"))

    if selected:
        wanted = [n.strip() for n in selected.split(",") if n.strip()]
        missing = [n for n in wanted if n not in names]
        if missing:
            sys.exit(f"error: 没这几个变体：{', '.join(missing)}")
        names = wanted
    elif quick:
        quick_file = ROOT / "tests" / "quick-set.txt"
        wanted = [
            line.strip()
            for line in quick_file.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.startswith("#")
        ]
        names = [n for n in wanted if n in names]

    return [Variant(n, conf_dir / f"{n}.conf") for n in names]


# ---------------------------------------------------------------- 参照物


def detect_repo() -> str:
    """返回 owner/repo。"""
    if os.environ.get("GITHUB_REPOSITORY"):
        return os.environ["GITHUB_REPOSITORY"]
    for remote in ("upstream", "origin"):
        try:
            url = subprocess.run(
                ["git", "remote", "get-url", remote],
                cwd=ROOT, capture_output=True, text=True, check=True,
            ).stdout.strip()
        except subprocess.CalledProcessError:
            continue
        match = re.search(r"[:/]([^/:]+/[^/]+?)(?:\.git)?$", url)
        if match:
            return match.group(1)
    return "hithesis/hithesis"


def api_get(url: str) -> object:
    request = urllib.request.Request(url, headers={
        "Accept": "application/vnd.github+json",
        "User-Agent": "hithesis-regression-test",
    })
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        request.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.load(response)


def find_reference_tag(repo: str, tag: str | None) -> str | None:
    """确定拿哪个 tag 当参照，默认最近一个正式 release。"""
    if tag:
        return tag
    try:
        releases = api_get(f"https://api.github.com/repos/{repo}/releases?per_page=30")
    except urllib.error.URLError as exc:
        print(f"访问 GitHub API 失败：{exc}")
        return None
    for release in releases:  # type: ignore[union-attr]
        if release.get("prerelease") or release.get("draft"):
            continue
        return release["tag_name"]
    return None


def source_archive_url(repo: str, tag: str) -> str:
    """tag 的源码存档地址。

    刻意不用 release 资产：资产是人手动传的，传错了（比如拿别的分支打的包）
    工具照样一片绿，比不检查还危险。zipball 由 GitHub 按 tag 自动生成，
    永远等于那个 tag 的真实代码，搞不错。
    """
    return f"https://api.github.com/repos/{repo}/zipball/{tag}"


def find_template_root(extracted: Path) -> Path | None:
    """定位解压出来的模板根目录，也就是含 examples/ 的那一层。

    scripts/package.sh 打的包是 examples/ 直接在顶层；GitHub 自动生成的源码存档
    会多套一层 hithesis-x.y/。两种都认。
    """
    if (extracted / "examples").is_dir():
        return extracted
    wrapped = [p for p in extracted.iterdir() if p.is_dir() and (p / "examples").is_dir()]
    return wrapped[0] if len(wrapped) == 1 else None


def ensure_generated_files(root: Path) -> bool:
    """源码存档里没有生成好的 .cls，得先跑一遍 latex hithesis.ins。"""
    if (root / "examples" / "hitbook" / "chinese" / "hithesisbook.cls").exists():
        return True
    if not (root / "hithesis.ins").exists():
        print(f"{root} 里既没有生成好的 cls，也没有 hithesis.ins，当不了参照")
        return False

    print("参照版本是源码存档，先跑一遍 latex hithesis.ins 生成 cls……")
    result = subprocess.run(
        ["latex", "-interaction=nonstopmode", "hithesis.ins"],
        cwd=root, capture_output=True, text=True,
    )
    if not (root / "examples" / "hitbook" / "chinese" / "hithesisbook.cls").exists():
        print("生成失败：\n" + "\n".join(result.stdout.strip().splitlines()[-15:]))
        return False
    return True


def prepare_reference(repo: str, tag: str | None) -> tuple[str, Path] | None:
    """下载并解压参照版本，返回 (tag, 模板根目录)。

    也可以离线用：自己把模板解到 target/regression-cache/<tag>/ 就行。
    """
    tag = find_reference_tag(repo, tag)
    if tag is None:
        return None

    target = CACHE_DIR / tag
    cached = find_template_root(target) if target.is_dir() else None
    if cached:
        print(f"用现成的缓存 {cached}")
        return (tag, cached) if ensure_generated_files(cached) else None

    target.mkdir(parents=True, exist_ok=True)
    archive = target / "source.zip"
    url = source_archive_url(repo, tag)
    print(f"下载 {tag} 的源码存档……")
    try:
        request = urllib.request.Request(url, headers={"User-Agent": "hithesis-regression-test"})
        with urllib.request.urlopen(request, timeout=300) as response, archive.open("wb") as f:
            shutil.copyfileobj(response, f)
    except urllib.error.URLError as exc:
        print(f"下载失败：{exc}")
        return None

    print(f"解压到 {target}")
    with zipfile.ZipFile(archive) as f:
        f.extractall(target)

    root = find_template_root(target)
    if root is None:
        print(f"{tag} 的存档里找不到 examples/，当不了参照")
        return None
    if not ensure_generated_files(root):
        return None

    return tag, root


# ---------------------------------------------------------------- 编译与比对


def compile_variant(variant: Variant, src_root: Path, side_dir: Path) -> tuple[bool, str]:
    """调 tools/compile-variant.sh 编一个变体。"""
    env = dict(os.environ)
    env["SRC_ROOT"] = str(src_root)
    env["WORK_DIR"] = str(side_dir / "work" / variant.name)
    env["PNG_DIR"] = str(side_dir / "png")
    env.setdefault("SOURCE_DATE_EPOCH", "1700000000")
    env.setdefault("FORCE_SOURCE_DATE", "1")

    result = subprocess.run(
        ["bash", "tools/compile-variant.sh", variant.name],
        cwd=ROOT, env=env, capture_output=True, text=True,
    )
    return result.returncode == 0, result.stdout + result.stderr


def compare_pages(variant: Variant, ref_png: Path, cur_png: Path) -> dict:
    """逐页比 PNG，返回差异摘要。"""
    ref_pages = sorted(ref_png.glob(f"{variant.name}-p*.png"))
    cur_pages = sorted(cur_png.glob(f"{variant.name}-p*.png"))

    differing = []
    for ref, cur in zip(ref_pages, cur_pages):
        if ref.read_bytes() != cur.read_bytes():
            differing.append(int(re.search(r"-p(\d+)\.png$", ref.name).group(1)))

    return {
        "variant": variant.name,
        "ref_pages": len(ref_pages),
        "cur_pages": len(cur_pages),
        "differing": differing,
        "changed": bool(differing) or len(ref_pages) != len(cur_pages),
    }


def make_diff_pdf(variant: Variant, ref_pdf: Path, cur_pdf: Path) -> Path | None:
    """用 diff-pdf 生成叠加式差异 PDF，没装就返回 None。

    diff-pdf 不在 Ubuntu 源里，CI 上装不了，只有本地 brew/自行编译才有。
    CI 那边靠 make_diff_image 出逐页差异图。
    """
    if shutil.which("diff-pdf") is None:
        return None
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    output = REPORT_DIR / f"{variant.name}.diff.pdf"
    subprocess.run(
        ["diff-pdf", f"--output-diff={output}", str(ref_pdf), str(cur_pdf)],
        capture_output=True,
    )
    return output if output.exists() else None


def make_diff_image(ref: Path, cur: Path, out: Path) -> bool:
    """用 ImageMagick 的 compare 把两页叠出一张标红的差异图。

    compare 在两图不同时返回 1，那是正常结果，所以只看有没有生成文件。
    """
    tool = shutil.which("compare") or shutil.which("magick")
    if tool is None:
        return False
    cmd = [tool, "compare"] if tool.endswith("magick") else [tool]
    subprocess.run([*cmd, str(ref), str(cur), str(out)], capture_output=True)
    return out.exists()


def save_page_images(variant: Variant, result: dict, ref_png: Path, cur_png: Path,
                     limit: int = 5) -> None:
    """把开头几张有差异的页面存进报告目录，省得再去翻 PDF。"""
    if not result["differing"]:
        return
    out = REPORT_DIR / variant.name
    out.mkdir(parents=True, exist_ok=True)
    for page in result["differing"][:limit]:
        name = f"{variant.name}-p{page:03d}.png"
        saved = {}
        for side, folder in (("ref", ref_png), ("cur", cur_png)):
            source = folder / name
            if source.exists():
                target = out / f"p{page:03d}-{side}.png"
                shutil.copy2(source, target)
                saved[side] = target
        if len(saved) == 2:
            make_diff_image(saved["ref"], saved["cur"], out / f"p{page:03d}-diff.png")


# ---------------------------------------------------------------- 报告


def publish(text: str) -> None:
    """写进报告目录，同时贴到 GitHub 的 Job Summary。"""
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    (REPORT_DIR / "summary.md").write_text(text, encoding="utf-8")

    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        with open(summary_path, "a", encoding="utf-8") as f:
            f.write(text + "\n")

    print()
    print(text)


def write_skip_note(reason: str) -> None:
    """跳过时也留一份报告，否则 CI 上是一片静默的绿。"""
    publish(f"# 排版回归报告\n\n本次跳过：{reason}\n")


def write_report(tag: str, results: list[dict], failures: list[tuple[str, str]]) -> None:
    changed = [r for r in results if r["changed"]]

    lines = [f"# 排版回归报告（参照 {tag}）", ""]
    if failures:
        lines += ["## 编译失败", ""]
        lines += [f"- `{name}`：{reason}" for name, reason in failures]
        lines.append("")

    if not changed:
        lines += [f"{len(results)} 个变体跟 {tag} 完全一样。", ""]
    else:
        lines += [
            f"{len(changed)}/{len(results)} 个变体的版面变了。",
            "",
            "| 变体 | 参照页数 | 当前页数 | 有差异的页 |",
            "| --- | --- | --- | --- |",
        ]
        for r in changed:
            pages = ", ".join(str(p) for p in r["differing"][:20]) or "—"
            if len(r["differing"]) > 20:
                pages += f" …（共 {len(r['differing'])} 页）"
            lines.append(f"| {r['variant']} | {r['ref_pages']} | {r['cur_pages']} | {pages} |")
        lines += ["", "逐页截图（ref / cur / diff）在本 artifact 的同名目录下。", ""]

    publish("\n".join(lines))


def review_interactively(tag: str, results: list[dict], pdfs: dict[str, tuple[Path, Path]]) -> bool:
    """逐个变体过一遍人工确认，返回是否判失败。"""
    changed = [r for r in results if r["changed"]]
    if not changed:
        print(f"{len(results)} 个变体都跟 {tag} 一样。")
        return False

    has_diff_pdf = shutil.which("diff-pdf") is not None
    if not has_diff_pdf:
        print("没装 diff-pdf，只能报页码。装上就能逐页叠加着看：")
        print("    brew install diff-pdf   （Ubuntu 源里没有，得自己编）")

    failed = False
    for r in changed:
        pages = ", ".join(str(p) for p in r["differing"]) or "页数不同"
        print(f"\n{r['variant']}：{pages}")
        if has_diff_pdf:
            ref_pdf, cur_pdf = pdfs[r["variant"]]
            subprocess.run(["diff-pdf", "--view", str(ref_pdf), str(cur_pdf)])
        answer = input("输入 x 判失败，直接回车表示这个改动是预期内的 >> ")
        if answer.lower().strip() == "x":
            print(f"{r['variant']} 判为回归。")
            failed = True
    return failed


# ---------------------------------------------------------------- 主流程


def main() -> int:
    parser = argparse.ArgumentParser(
        description="跟上一个正式 release 逐页比排版",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--against", metavar="TAG", help="参照的 tag，默认取最近一个正式 release")
    parser.add_argument("--variants", metavar="LIST", help="只跑这几个变体，逗号分隔")
    parser.add_argument("--quick", action="store_true", help="只跑 tests/quick-set.txt 里的那几个")
    parser.add_argument("--jobs", type=int, default=os.cpu_count() or 4, help="并发编译数")
    parser.add_argument("--ci", action="store_true", help="不交互，出报告和 artifact，不逐个问")
    args = parser.parse_args()

    variants = load_variants(args.variants, args.quick)
    if not variants:
        print("error: 一个变体都没选中")
        return EXIT_ERROR

    repo = detect_repo()
    print(f"参照仓库 {repo}")
    reference = prepare_reference(repo, args.against)
    if reference is None:
        write_skip_note(
            "没拿到可用的参照版本。默认取最近一个正式 release 对应的 tag，"
            "下载它的源码存档来当参照。上面的日志里有具体是哪一步没过去。"
        )
        return EXIT_SKIP
    tag, ref_root = reference

    # 参照版本里可能还没有某些 example 目录，比如后来才加的 reportplus
    runnable, skipped = [], []
    for variant in variants:
        (runnable if (ref_root / variant.base).is_dir() else skipped).append(variant)
    for variant in skipped:
        print(f"{tag} 里没有 {variant.base}，跳过 {variant.name}")
    if not runnable:
        write_skip_note(f"{tag} 里一个能对上的 example 目录都没有，没得比。")
        return EXIT_SKIP

    ref_dir = RUN_DIR / tag
    cur_dir = RUN_DIR / "current"
    shutil.rmtree(REPORT_DIR, ignore_errors=True)

    print(f"编译 {len(runnable)} 个变体 × 两侧（参照 {tag}、当前工作树），并发 {args.jobs}……")

    failures: list[tuple[str, str]] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs) as pool:
        jobs = {}
        for variant in runnable:
            jobs[(variant.name, "ref")] = pool.submit(compile_variant, variant, ref_root, ref_dir)
            jobs[(variant.name, "cur")] = pool.submit(compile_variant, variant, ROOT, cur_dir)

        broken: set[str] = set()
        for (name, side), future in jobs.items():
            ok, log = future.result()
            if ok:
                continue
            broken.add(name)
            tail = "\n".join(log.strip().splitlines()[-15:])
            failures.append((name, f"{side} 侧编译失败\n```\n{tail}\n```"))
            print(f"{name}（{side} 侧）编译失败")

    compared = [v for v in runnable if v.name not in broken]
    results = [compare_pages(v, ref_dir / "png", cur_dir / "png") for v in compared]
    pdfs = {
        v.name: (ref_dir / "work" / v.name / v.pdf_name, cur_dir / "work" / v.name / v.pdf_name)
        for v in compared
    }

    if args.ci:
        for variant, result in zip(compared, results):
            if not result["changed"]:
                continue
            save_page_images(variant, result, ref_dir / "png", cur_dir / "png")
            make_diff_pdf(variant, *pdfs[variant.name])
        write_report(tag, results, failures)
        judged_failure = any(r["changed"] for r in results)
    else:
        judged_failure = review_interactively(tag, results, pdfs)

    if failures:
        return EXIT_ERROR
    return EXIT_DIFF if judged_failure else EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
