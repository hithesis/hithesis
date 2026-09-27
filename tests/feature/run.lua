#!/usr/bin/env texlua
-- 按功能拆开的回归：一个写法跑遍各分支（阶段 × 学位 × 校区 × 语种 × 引擎），逐份查对不对。
-- 平时不跑，改了某个功能、或者发版前跑一次。用法见 tests/README.md 的“按功能的回归”一节。
--
--   texlua tests/feature/run.lua [-j 并发数] [-e 引擎,…] [-b 分支条件] [--keep] [用例 …]
--
-- 用例是 tests/feature/cases/ 下同名的一对文件：<名>.tex 是文档（\documentclass 由这里按分支
-- 补上），<名>.lua 是检查（可以没有，没有就只查编没编出来、有没有报错和告警）。

local ROOT = arg[0]:match("^(.*)/tests/feature/run%.lua$") or "."
if ROOT == "" then ROOT = "." end
if ROOT:sub(1, 1) ~= "/" then ROOT = lfs.currentdir() .. "/" .. ROOT end
ROOT = ROOT:gsub("/%./", "/"):gsub("/%.$", "")
local HERE = ROOT .. "/tests/feature"
local CASES = HERE .. "/cases"
local WORK = HERE .. "/work"

-- 分支全集。与 tests/variants 的学位 × 校区一致，终稿加英文版，报告加深圳本科英文版。
-- 深圳本科终稿由类改排本部模板，照样列着：改排本身也要测。
local BRANCHES = {}
local function branch(id, stage, degree, campus, lang)
  BRANCHES[#BRANCHES + 1] = {
    id = id, stage = stage, ["degree-level"] = degree, campus = campus, lang = lang or "zh",
  }
end
branch("f-bach-hb", "final", "bachelor", "harbin")
branch("f-bach-sz", "final", "bachelor", "shenzhen")
branch("f-bach-sz-en", "final", "bachelor", "shenzhen", "en")
branch("f-bach-wh", "final", "bachelor", "weihai")
branch("f-mast-hb", "final", "master", "harbin")
branch("f-mast-sz", "final", "master", "shenzhen")
branch("f-mast-sz-en", "final", "master", "shenzhen", "en")
branch("f-doct-hb", "final", "doctor", "harbin")
branch("f-doct-hb-en", "final", "doctor", "harbin", "en")
branch("f-doct-sz", "final", "doctor", "shenzhen")
branch("f-post-hb", "final", "postdoc", "harbin")
for _, st in ipairs({ { "prop", "proposal" }, { "int", "interim" } }) do
  branch("r-" .. st[1] .. "-bach-hb", st[2], "bachelor", "harbin")
  branch("r-" .. st[1] .. "-bach-sz", st[2], "bachelor", "shenzhen")
  branch("r-" .. st[1] .. "-bach-sz-en", st[2], "bachelor", "shenzhen", "en")
  branch("r-" .. st[1] .. "-bach-wh", st[2], "bachelor", "weihai")
  branch("r-" .. st[1] .. "-mast-hb", st[2], "master", "harbin")
  branch("r-" .. st[1] .. "-mast-sz", st[2], "master", "shenzhen")
  branch("r-" .. st[1] .. "-mast-wh", st[2], "master", "weihai")
  branch("r-" .. st[1] .. "-doct-hb", st[2], "doctor", "harbin")
  branch("r-" .. st[1] .. "-doct-sz", st[2], "doctor", "shenzhen")
end
branch("r-prop-doct-wh", "proposal", "doctor", "weihai")

local ENGINES = { "lualatex", "xelatex", "pdflatex" }
local LATEXMK_FLAG = { lualatex = "-lualatex", xelatex = "-xelatex", pdflatex = "-pdf" }

-- 工具 ---------------------------------------------------------------------------------

local function read(path)
  local f = io.open(path, "rb")
  if not f then return nil end
  local s = f:read("a")
  f:close()
  return s
end

local function write(path, s)
  local f = assert(io.open(path, "wb"))
  f:write(s)
  f:close()
end

local function sh_quote(s) return "'" .. s:gsub("'", "'\\''") .. "'" end

local function split(s, sep)
  local out = {}
  for piece in (s .. sep):gmatch("(.-)" .. sep) do
    piece = piece:match("^%s*(.-)%s*$")
    if piece ~= "" then out[#out + 1] = piece end
  end
  return out
end

-- 条件与类的 \hitsetup[…] 同一套写法：逗号是且，分号是或，竖线是几个取值任一，
-- 取值前的 ! 是非。键是分支的四项、分支名 id 与 engine。
local function parse_cond(s)
  if not s or s:match("^%s*$") then return function() return true end end
  local alts = {}
  for _, alt in ipairs(split(s, ";")) do
    local terms = {}
    for _, term in ipairs(split(alt, ",")) do
      local key, val = term:match("^([%w%-]+)%s*=%s*(.-)$")
      if not key then error("条件写错了：" .. term) end
      local neg = val:sub(1, 1) == "!"
      if neg then val = val:sub(2) end
      local set = {}
      for _, v in ipairs(split(val, "|")) do set[v] = true end
      terms[#terms + 1] = { key = key, set = set, neg = neg }
    end
    alts[#alts + 1] = terms
  end
  return function(env)
    for _, terms in ipairs(alts) do
      local ok = true
      for _, t in ipairs(terms) do
        local hit = t.set[env[t.key] or ""] == true
        if hit == t.neg then ok = false break end
      end
      if ok then return true end
    end
    return false
  end
end

-- 用例 -----------------------------------------------------------------------------------

-- 文件头的 %! 行是指令：
--   %! branches: 条件        跑哪些分支（默认全部）
--   %! engines: 引擎,…      跑哪些引擎（默认三个）
--   %! options: 选项,…      给 \documentclass 多加的选项
--   %! files: 文件,…        一起拷进工作目录的文件（相对 cases/）
--   %! allow: Lua 模式       容许的告警，可写多行
local function load_case(name)
  local src = read(CASES .. "/" .. name .. ".tex")
  if not src then error("没有这个用例：" .. name) end
  local case = { name = name, src = src, allow = {}, files = {}, engines = ENGINES }
  for key, val in src:gmatch("\n?%%!%s*([%w]+)%s*:%s*([^\n]*)") do
    if key == "branches" then case.branches = val
    elseif key == "engines" then case.engines = split(val, ",")
    elseif key == "options" then case.options = val
    elseif key == "files" then case.files = split(val, ",")
    elseif key == "allow" then case.allow[#case.allow + 1] = val
    else error(name .. "：不认识的指令 " .. key) end
  end
  case.cond = parse_cond(case.branches)
  local chk = CASES .. "/" .. name .. ".lua"
  if read(chk) then case.check = assert(loadfile(chk))() end
  return case
end

local function list_cases()
  local out = {}
  for f in lfs.dir(CASES) do
    local n = f:match("^(.-)%.tex$")
    if n then out[#out + 1] = n end
  end
  table.sort(out)
  return out
end

-- PDF ------------------------------------------------------------------------------------

local function unescape(s)
  return (s:gsub("&#x(%x+);", function(h) return utf8.char(tonumber(h, 16)) end)
           :gsub("&#(%d+);", function(d) return utf8.char(tonumber(d)) end)
           :gsub("&lt;", "<"):gsub("&gt;", ">"):gsub("&quot;", '"')
           :gsub("&apos;", "'"):gsub("&amp;", "&"))
end

-- mutool trace 逐字取出来：页、基线、横坐标、字、字体、字号，粗不粗。合成粗体是同一个字
-- 再描一遍边（stroke_text），按坐标并回填充的那个字上；真粗体看字体名。
local function trace(pdf)
  local p = io.popen("mutool trace " .. sh_quote(pdf) .. " 2>/dev/null")
  local glyphs, index = {}, {}
  local page, kind, A, font, size = 0, nil, { 1, 0, 0, 1, 0, 0 }, "", 0
  for line in p:lines() do
    local n = line:match('^<page number="(%d+)"')
    if n then page = tonumber(n) end
    local k, attrs = line:match("^<(%a+_text)(.*)>")
    if k then
      kind = k
      local tm = attrs:match('transform="([^"]+)"')
      A = { 1, 0, 0, 1, 0, 0 }
      if tm then
        local i = 0
        for v in tm:gmatch("%S+") do i = i + 1; A[i] = tonumber(v) end
      end
    end
    local f, trm = line:match('<span font="([^"]+)".-trm="([^"]+)"')
    if f then font = f:gsub("^%u%u%u%u%u%u%+", ""); size = tonumber(trm:match("^%S+")) end
    local u, gx, gy = line:match('<g unicode="([^"]*)".-x="([%d.%-]+)" y="([%d.%-]+)"')
    if u and (kind == "fill_text" or kind == "stroke_text") then
      gx, gy = tonumber(gx), tonumber(gy)
      local x = A[1] * gx + A[3] * gy + A[5]
      local y = A[2] * gx + A[4] * gy + A[6]
      local key = string.format("%d:%.1f:%.1f", page, y, x)
      local g = index[key]
      if not g then
        g = { page = page, x = x, y = y, ch = unescape(u), font = font, size = size }
        index[key] = g
        glyphs[#glyphs + 1] = g
      end
      if kind == "stroke_text" then g.stroke = true else g.font = font end
    end
  end
  p:close()
  for _, g in ipairs(glyphs) do
    g.bold = g.stroke or g.font:find("Bold") ~= nil or g.font:find("Black") ~= nil
      or g.font:find("Heavy") ~= nil or g.font:find("%-Bd") ~= nil
  end
  -- 按页、按行（基线差 0.5 以内算一行）、按横坐标排
  table.sort(glyphs, function(a, b)
    if a.page ~= b.page then return a.page < b.page end
    if math.abs(a.y - b.y) > 0.5 then return a.y < b.y end
    return a.x < b.x
  end)
  local lines = {}
  local cur
  for _, g in ipairs(glyphs) do
    if not g.ch:match("^%s*$") then
      if not cur or cur.page ~= g.page or math.abs(cur.y - g.y) > 0.5 then
        cur = { page = g.page, y = g.y, glyphs = {} }
        lines[#lines + 1] = cur
      end
      cur.glyphs[#cur.glyphs + 1] = g
    end
  end
  for _, l in ipairs(lines) do
    local t = {}
    for i, g in ipairs(l.glyphs) do t[i] = g.ch end
    l.text = table.concat(t)
  end
  return lines
end

-- 检查用的对象 ---------------------------------------------------------------------------

local T = {}
T.__index = T

local function strip(s) return (s:gsub("%s+", "")) end

function T:fail(msg) self.failures[#self.failures + 1] = msg end
function T:expect(ok, msg) if not ok then self:fail(msg) end return ok end

function T:lines()
  if not self._lines then self._lines = trace(self.pdf) end
  return self._lines
end

-- 找一段字：跨不了行，空白不算。返回所在行与字的序号区间
function T:find(s, from)
  local want = strip(s)
  local start = from or 1
  for li = start, #self:lines() do
    local l = self:lines()[li]
    local chars = {}
    for i, g in ipairs(l.glyphs) do chars[i] = g.ch end
    local text = table.concat(chars)
    local b = text:find(want, 1, true)
    if b then
      -- 字节位置换成字的序号
      local first = utf8.len(text:sub(1, b - 1)) + 1
      return l, first, first + utf8.len(want) - 1, li
    end
  end
end

function T:has(s, msg)
  return self:expect(self:find(s) ~= nil, msg or ("缺“" .. s .. "”"))
end

function T:hasnt(s, msg)
  return self:expect(self:find(s) == nil, msg or ("不该有“" .. s .. "”"))
end

function T:count(s)
  local n, li = 0, 1
  while true do
    local l, _, _, at = self:find(s, li)
    if not l then return n end
    n, li = n + 1, at + 1
  end
end

-- 这段字粗不粗：want 为 true 要求每个字都粗，false 要求都不粗
function T:bold(s, want, msg)
  local l, a, b = self:find(s)
  if not self:expect(l ~= nil, "缺“" .. s .. "”，查不了粗细") then return end
  for i = a, b do
    local g = l.glyphs[i]
    if g.bold ~= want then
      return self:fail(msg or string.format("“%s”里的“%s”该%s，排成了%s（%s）",
        s, g.ch, want and "粗" or "细", g.bold and "粗" or "细", g.font))
    end
  end
end

-- 这段字用的字体（第一个字的）
function T:font(s)
  local l, a = self:find(s)
  return l and l.glyphs[a].font
end

-- 这段字首字的位置：页、横坐标、基线（自页顶往下量）
function T:pos(s)
  local l, a = self:find(s)
  if l then return l.page, l.glyphs[a].x, l.y end
end

-- 类写进日志的开关（tests/feature/feature-prelude.tex），取回来是布尔值
function T:fact(name)
  local v = self.log:match("FEATURE%-FACT " .. name:gsub("%-", "%%-") .. "=(%a+)")
  if v == nil then error("日志里没有 " .. name .. " 这个开关") end
  return v == "true"
end

function T:page_of(s)
  local l = self:find(s)
  return l and l.page
end

-- 跑 -------------------------------------------------------------------------------------

local function parse_args()
  local o = { jobs = 6, names = {} }
  local i = 1
  while i <= #arg do
    local a = arg[i]
    if a == "-j" then o.jobs = tonumber(arg[i + 1]); i = i + 1
    elseif a == "-e" then o.engines = split(arg[i + 1], ","); i = i + 1
    elseif a == "-b" then o.branches = arg[i + 1]; i = i + 1
    elseif a == "--keep" then o.keep = true
    elseif a == "--list" then o.list = true
    else o.names[#o.names + 1] = a end
    i = i + 1
  end
  return o
end

local opts = parse_args()
local names = #opts.names > 0 and opts.names or list_cases()
if opts.list then
  for _, n in ipairs(names) do print(n) end
  os.exit(0)
end
local extra = parse_cond(opts.branches)

lfs.mkdir(WORK)
local jobs = {}
for _, name in ipairs(names) do
  local case = load_case(name)
  local engines = case.engines
  if opts.engines then
    local keep = {}
    for _, e in ipairs(engines) do
      for _, w in ipairs(opts.engines) do if e == w then keep[#keep + 1] = e end end
    end
    engines = keep
  end
  for _, br in ipairs(BRANCHES) do
    for _, eng in ipairs(engines) do
      local env = { engine = eng }
      for k, v in pairs(br) do env[k] = v end
      if case.cond(env) and extra(env) then
        jobs[#jobs + 1] = { case = case, branch = br, engine = eng,
          dir = WORK .. "/" .. name .. "/" .. br.id .. "-" .. eng }
      end
    end
  end
end
if #jobs == 0 then
  print("没有要跑的：用例或条件把分支都筛掉了")
  os.exit(1)
end

-- 生成工作目录，并发编译
local list = {}
local abs_root = ROOT
for _, j in ipairs(jobs) do
  os.execute("rm -rf " .. sh_quote(j.dir) .. " && mkdir -p " .. sh_quote(j.dir))
  local b = j.branch
  local classopt = string.format("stage=%s,degree-level=%s,campus=%s,lang=%s",
    b.stage, b["degree-level"], b.campus, b.lang)
  if j.case.options then classopt = classopt .. "," .. j.case.options end
  write(j.dir .. "/main.tex",
    "\\documentclass[" .. classopt .. "]{hithesis}\n\\input{feature-prelude}\n" .. j.case.src)
  write(j.dir .. "/latexmkrc", assert(read(HERE .. "/latexmkrc")))
  for _, f in ipairs(j.case.files) do
    write(j.dir .. "/" .. f, assert(read(CASES .. "/" .. f), "缺文件 " .. f))
  end
  write(j.dir .. "/job.sh", table.concat({
    "cd " .. sh_quote(j.dir),
    "export TEXINPUTS=" .. sh_quote(abs_root .. ":" .. abs_root .. "/assets:" .. HERE .. ":"),
    "export INDEXSTYLE=" .. sh_quote(abs_root .. ":"),
    "export BSTINPUTS=" .. sh_quote(abs_root .. ":"),
    "export SOURCE_DATE_EPOCH=1790000000 FORCE_SOURCE_DATE=1",
    "latexmk " .. LATEXMK_FLAG[j.engine] .. " -f -g -interaction=nonstopmode main.tex >/dev/null 2>&1",
    "",
  }, "\n"))
  list[#list + 1] = j.dir .. "/job.sh"
end
-- 两次跑可能同时开着（不同用例），任务表各用各的
local joblist = os.tmpname()
write(joblist, table.concat(list, "\n") .. "\n")
io.write(string.format("编 %d 份（%d 并发）……\n", #jobs, opts.jobs))
io.flush()
os.execute("xargs -P " .. opts.jobs .. " -n 1 sh < " .. sh_quote(joblist))
os.remove(joblist)

-- 逐份查
local WARN = { "Package hithesis Warning", "Class hithesis Warning", "Package docxlike Warning",
  "LaTeX Font Warning: Font shape .- undefined" }
-- 引擎自己的已知局限，文档里写明了的，每次编都报一条，不算不过
local ENGINE_ALLOW = {
  pdflatex = { "not on the character grid under pdfLaTeX" },
}

-- 告警按条取：续行（行首是“(包名)”）接回第一行后面
local function warnings(log)
  local out, lines = {}, {}
  for l in log:gmatch("[^\n]*") do lines[#lines + 1] = l end
  local i = 1
  while i <= #lines do
    local l = lines[i]
    for _, w in ipairs(WARN) do
      if l:match(w) then
        local j = i + 1
        while lines[j] and lines[j]:match("^%(%a+%)%s") do
          l = l .. " " .. lines[j]:gsub("^%(%a+%)%s+", "")
          j = j + 1
        end
        out[#out + 1] = l
        break
      end
    end
    i = i + 1
  end
  return out
end
local failed, total = 0, 0
local by_case = {}
for _, j in ipairs(jobs) do
  total = total + 1
  local t = setmetatable({ branch = j.branch, engine = j.engine, id = j.branch.id .. "-" .. j.engine,
    pdf = j.dir .. "/main.pdf", failures = {} }, T)
  t.log = read(j.dir .. "/main.log") or ""
  if not read(t.pdf) then
    t:fail("没编出 PDF")
  else
    for l in t.log:gmatch("[^\n]+") do
      if l:match("^! ") then t:fail("报错：" .. l) break end
    end
    for _, l in ipairs(warnings(t.log)) do
      local ok = false
      for _, a in ipairs(j.case.allow) do if l:match(a) then ok = true end end
      for _, a in ipairs(ENGINE_ALLOW[j.engine] or {}) do if l:match(a) then ok = true end end
      if not ok then t:fail("告警：" .. l) end
    end
    if #t.failures == 0 and j.case.check then
      local ok, err = pcall(j.case.check, t)
      if not ok then t:fail("检查脚本出错：" .. tostring(err)) end
    end
  end
  local r = by_case[j.case.name] or { pass = 0, fail = {} }
  by_case[j.case.name] = r
  if #t.failures == 0 then
    r.pass = r.pass + 1
    if not opts.keep then os.execute("rm -rf " .. sh_quote(j.dir)) end
  else
    failed = failed + 1
    r.fail[#r.fail + 1] = { id = t.id, dir = j.dir, msgs = t.failures }
  end
end

for _, name in ipairs(names) do
  local r = by_case[name]
  if r then
    print(string.format("%-28s 过 %d，不过 %d", name, r.pass, #r.fail))
    for _, f in ipairs(r.fail) do
      print("  " .. f.id .. "（" .. f.dir .. "）")
      for i, m in ipairs(f.msgs) do
        if i > 5 then print("    ……另有 " .. (#f.msgs - 5) .. " 条") break end
        print("    " .. m)
      end
    end
  end
end
print(string.format("—— 共 %d 份，不过 %d", total, failed))
os.exit(failed == 0 and 0 or 1)
