-- l3build 构建配置。
--
-- l3build 随 TeX Live 发行，装了 TeX 就有，不依赖 make / bash / python，
-- 三个平台都能原生跑。常用命令：
--
--   l3build unpack     跑 docstrip 生成 cls/bst/ist/eps（自解压 dtx，不走 .ins）
--   l3build distribute 把生成物拷进四个示例目录，等价于 make distribute
--   l3build doc        编译用户手册 hithesis.pdf
--   l3build install    装进本地 TEXMFHOME
--   l3build ctan       打出符合 CTAN 规范的发布包（含 TDS zip）
--
-- Makefile 仍然保留：42 变体排版比对、回归测试、changes 检查这些是本项目特有的，
-- 不在 l3build 的职责范围内。两者分工是“l3build 管构建与打包，Makefile 管测试”。

module = "hithesis"

-- 源文件都在 src/。解压规则写在 src/hithesis.dtx 的 install 守卫里，跑
-- xetex src/hithesis.dtx 就地解压，hithesis.ins 是它顺带生成的产物之一。
--
-- .ins 仍然列进 sourcefiles：CTAN 把“生成的 .ins”列为要随包保留的例外，
-- 拿到源码包的人跑 latex hithesis.ins 结果与自解压一致。开发时不走它。
--
-- unpackexe 用 xetex 而不是 tex：docstrip 逐字节搬运，plain tex 会把 dtx 里的
-- 中文写成 ^^e5 这种转义。
sourcefiles = {"src/*.dtx", "src/*/*.dtx", "hithesis.ins"}
unpackfiles = {"hithesis.dtx"}

-- 装进 TEXMF 的东西。examples 里那几份副本由下面的 distribute 目标分发，
-- 不属于安装内容。
--
-- 这里不用 *.sty 通配。dtx-style.sty 只在排手册时用，被通配捎进 TEXMF 会污染
-- 用户机器，而且 dtx-style 这个名字相当通用，别的包也叫这个就撞了。要装的
-- .sty 只有 hithesis.sty 一个，显式列出来。
--
-- hithesis.sty 是示例宏包，装进 TEXMF 是为了让 \usepackage{hithesis} 在任何目录下
-- 都能编过。它本来就是给用户改的，改法是在自己项目目录里放一份同名文件，那份优先。
installfiles = {
  "hit-thesis.cls", "hit-report.cls", "hithesis.cls",
  "hithesisbook.cls", "hithesisart.cls", "hithesisartplus.cls",
  "hithesis.sty",
  "hithesis.ist", "hithesis.bst", "hitszthesis.bst",
  "*.eps",
}

typesetfiles = {"hithesis.dtx"}
typesetexe   = "xelatex"
unpackexe    = "xetex"

checkengines = {"xetex"}
stdengine    = "xetex"

-- 随包发布的文件。examples/ 不交给 l3build：它的 demofiles 会把目录树拍平，
-- 而示例必须保持 examples/demo/... 的层级用户才能直接编译。
-- 面向用户的完整模板包仍由 scripts/package.sh 打，CTAN 包只含源码与手册。
textfiles = {"README.md"}

-- 手册里的日期取 \today，不钉死的话每次构建产物都不同
typesetopts = "-interaction=nonstopmode"
unpackopts  = "-interaction=nonstopmode"


-- 把生成物拷进示例目录，与用户解压发布包后的目录结构一致。装进 TEXMFHOME
-- 不能替代：.cls 能被找到，但 .eps 用 kpathsea 的图形检索格式、.bst 用
-- BSTINPUTS，都不在 tex/latex 路径下。
--
-- 用 Lua 而不是 shell，是为了 macOS/Windows 上不装 make 也能跑。Makefile 里的
-- distribute 目标是等价实现，但两边读的是同一份 tools/distfiles.txt，不会各自
-- 漂移。没让 Makefile 直接转调这里，是因为 l3build 不在 scheme-minimal 里，
-- 那样会把它变成 make 的硬依赖。
local function readlist()
  local plain, subdir = {}, {}
  for line in io.lines(maindir .. "/tools/distfiles.txt") do
    line = line:gsub("#.*", ""):gsub("^%s+", ""):gsub("%s+$", "")
    if line ~= "" and line:sub(1, 1) ~= "!" then
      local name, dest = line:match("^(%S+)%s*%->%s*(%S+)$")
      if name then
        subdir[#subdir + 1] = {name, dest}
      else
        plain[#plain + 1] = line
      end
    end
  end
  return plain, subdir
end

-- 生成物可能在两个地方：make cls 写在根目录，l3build unpack 写在 build/unpacked。
-- 两种都要能用。
local function srcdir(f)
  if fileexists(maindir .. "/" .. f) then return maindir end
  if fileexists(unpackdir .. "/" .. f) then return unpackdir end
  return nil
end

local function distribute()
  local plain, subdir = readlist()
  local dest = "examples/demo"

  local function one(f, to)
    local from = srcdir(f)
    if not from then
      print("distribute: 找不到 " .. f .. "，先跑 l3build unpack 或 make cls")
      return 1
    end
    cp(f, from, to)
    return 0
  end

  mkdir(dest)
  for _, f in ipairs(plain) do
    if one(f, dest) ~= 0 then return 1 end
  end
  for _, entry in ipairs(subdir) do
    mkdir(dest .. "/" .. entry[2])
    if one(entry[1], dest .. "/" .. entry[2]) ~= 0 then return 1 end
  end
  return 0
end

target_list = target_list or {}
target_list.distribute = {
  func = distribute,
  desc = "把生成物拷进示例目录",
}

-- 手册的排版必须在主目录里跑，不能用 l3build 默认的 build/doc：
--   * 手册用 \lstinputlisting 把示例源码贴进正文，路径含目录层级
--     （examples/demo/thesis-en.tex），而 l3build 拷贝时会拍平
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
