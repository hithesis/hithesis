# wiseref 集成测试

wiseref 的实现和独立测试在相邻的 `latex-wiseref` 仓库中，本目录只保存 hithesis 的接入测试。
模板不分发或自动加载 wiseref；用户安装后通过 `\usepackage{wiseref}` 启用。

```sh
make cls
python3 tests/wiseref/run-integration.py --work /tmp/hithesis-wiseref
```

可用 `--candidate /path/to/wiseref.sty` 指定待测版本。工作目录须尚不存在；中断后可用
`--resume` 补跑未成功项。每项独立复制当前模板生成物与候选包，并编译三遍。

三引擎 × 中英文 × 终稿/深圳开题，共 12 项，检查：

- 用户加载后，名称取 cfg 的图、表、公式词条；
- 语言选择用 `lang` 读取模板的当前语言，改变选择不重置用户格式；
- 用户随后设置 wiseref 时，覆盖模板配置而不被再次覆盖；
- 公式引用复用 `equation-numbering-fullwidth`，英文保持半角；
- 子图包含父编号和字母，PDF 链接目标实际存在；
- 混合引用及星号无链接引用的文本正确。

加 `--preload-only` 另跑三引擎的提前加载场景，确认宏包已加载时，模板配置会等到
文档类初始化完成后注入。

独立仓库的 `test/run.py` 另跑 36 项标准类组合，比较加载前后的标准标签、文本、字符位置
及链接，并断言实际记录的类型、附录、无编号目标、tag/tag*。
6 项 API 组合各有 34 个文本断言，覆盖局部前后缀、单复数、排序、压缩和三种链接模式。
这些标准文档测试明确禁止加载 hithesis、docxlike、cleveref 或 smartref。

## 3.1e 旧版验证

`legacy-3.1e.py` 与 `legacy-3.1e.tex` 验证从 `v3.1e` 标签提取的原版类。
需要相邻的 `latex-wiseref` 仓库，以及运行过 `xetex hithesis.ins` 的旧版快照。

```sh
python3 tests/wiseref/legacy-3.1e.py --source /path/to/extracted-v3.1e \
  --work /tmp/hithesis-31e-wiseref
```

2026-10-11 使用当前 wiseref v1.2026a（`a2bf559`）和 TeX Live 2026 重新验证：
完整矩阵 46 项，44 项通过、2 项原版自定义公式标记基线错误，wiseref 失败 0 项。
语言配置、公式索引局部配置及测试范围见 [3.1e 验证记录](legacy-3.1e.md)。
