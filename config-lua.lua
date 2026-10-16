-- Lua 专用基线按 TeX Live 2026 核验；用 make check-lua 检查实际执行数量。
checkengines = {"luatex"}
includetests = {}
for line in io.lines(maindir .. "/tests/lua-cases.txt") do
  local name = line:gsub("#.*", ""):match("^%s*(.-)%s*$")
  if name ~= "" then includetests[#includetests + 1] = name end
end
assert(#includetests == 9, "Lua special-page checks require exactly nine cases")
