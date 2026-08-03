-- l3build 构建配置。
--
-- l3build 随 TeX Live 发行，装了 TeX 就有，不依赖 make / bash / python，
-- 三个平台都能原生跑。常用命令：
--
--   l3build unpack     跑 docstrip 生成 cls/cfg/bst/ist/eps
--   l3build doc        编译用户手册 hithesis.pdf
--   l3build install    装进本地 TEXMFHOME
--   l3build ctan       打出符合 CTAN 规范的发布包（含 TDS zip）
--
-- Makefile 仍然保留：42 变体排版比对、回归测试、changes 检查这些是本项目特有的，
-- 不在 l3build 的职责范围内。两者分工是「l3build 管构建与打包，Makefile 管测试」。

module = "hithesis"

-- 源文件都在 src/，hithesis.ins 留在根目录：它的输出路径相对于调用目录，
-- 跟着搬会全部指错。
sourcefiles = {"src/*.dtx", "hithesis.ins"}
unpackfiles = {"hithesis.ins"}

-- 装进 TEXMF 的东西。examples 里那几份副本由 make distribute 分发，不属于安装内容。
installfiles = {"*.cls", "*.cfg", "*.ist", "*.bst", "*.eps", "*.sty"}

typesetfiles = {"hithesis.dtx"}
typesetexe   = "xelatex"
unpackexe    = "latex"

checkengines = {"xetex"}
stdengine    = "xetex"

-- 随包发布的文件。examples/ 不交给 l3build：它的 demofiles 会把目录树拍平，
-- 而示例必须保持 examples/hitbook/chinese/... 的层级用户才能直接编译。
-- 面向用户的完整模板包仍由 scripts/package.sh 打，CTAN 包只含源码与手册。
textfiles = {"README.md"}

-- 手册里的日期取 \today，不钉死的话每次构建产物都不同
typesetopts = "-interaction=nonstopmode"
unpackopts  = "-interaction=nonstopmode"


-- 手册的排版必须在主目录里跑，不能用 l3build 默认的 build/doc：
--   * 手册用 \lstinputlisting 把示例源码贴进正文，路径含目录层级
--     （examples/hitbook/english/thesis.tex），而 l3build 拷贝时会拍平
--   * 索引和修改记录要用 gind.ist / gglo.ist 跑两次 makeindex，
--     不是默认那套流程
-- 所以这里覆盖 typeset，走与 Makefile 的 doc 目标相同的序列，编完把 PDF
-- 交回 l3build 约定的位置，好让 ctan 能取到。
function typeset(file, dir)
  local job = "hithesis"
  local src = "src/" .. job .. ".dtx"
  local opts = "-interaction=nonstopmode"

  local steps = {
    typesetexe .. " " .. opts .. " " .. src,
    "makeindex -s gind.ist -o " .. job .. ".ind " .. job .. ".idx",
    "makeindex -s gglo.ist -o " .. job .. ".gls " .. job .. ".glo",
    typesetexe .. " " .. opts .. " " .. src,
    typesetexe .. " " .. opts .. " " .. src,
  }
  for _, cmd in ipairs(steps) do
    local errorlevel = run(maindir, cmd .. " > " .. os_null)
    -- makeindex 在没有条目时会报非零，不算失败；xelatex 用 nonstopmode，
    -- 真出错时后面 PDF 不会生成，由下面的检查兜住
    if errorlevel ~= 0 and cmd:find(typesetexe, 1, true) == 1 then
      return errorlevel
    end
  end

  if not fileexists(maindir .. "/" .. job .. ".pdf") then
    print("typeset: 没有产出 " .. job .. ".pdf")
    return 1
  end
  mkdir(dir)
  cp(job .. ".pdf", maindir, dir)
  return 0
end
