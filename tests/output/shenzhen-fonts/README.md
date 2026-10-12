# 深圳硕士报告字体预览

打开 `index.html` 查看缩略图、实际字体与回退说明。

- 六档字体：auto、windows、macos、founder、noto、fandol。
- 四套完整示例：中文开题、英文开题、中文中期、英文中期。
- 各 PDF 使用相同的元信息和对应正文，均由 LuaLaTeX 编译，默认启用中文基线校正。
- `compare-*.pdf` 按字体集顺序收录各份的封面和正文首页，带书签。
- `manifest.json` 记录页数、实际解析字体、PDF 内嵌字体与编译提示。
- `shenzhen-font-previews.zip` 包含总览页、PDF、图片及清单，可整体复制或解压后浏览。

在仓库根目录重新生成：

```sh
make cls
python3 scripts/preview-shenzhen-fonts.py
```

需要 latexmk、LuaLaTeX，以及 Python 的 pdfplumber、pypdfium2、pypdf、Pillow。
