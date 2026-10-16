return function(t)
  if not t:expect(t.log:find("SMALL%-MATH.-fits=yes") ~= nil,
    "小公式须先满足实际高深能装入普通撑杆，才能检查不撑高行距") then return end
  local names = {
    "PlainFirst", "PlainSecond", "MathFirst",
    "MathSecond", "AfterFirst", "AfterSecond",
  }
  local lines = {}
  for _, name in ipairs(names) do
    local line = t:find(name)
    if not t:expect(line ~= nil, "缺少行标记：" .. name) then return end
    lines[#lines + 1] = line
  end
  local expected = lines[2].y - lines[1].y
  for i = 2, #lines do
    t:expect(lines[i].page == lines[1].page, "小行内公式不应使短探针换页")
    local gap = lines[i].y - lines[i - 1].y
    t:expect(math.abs(gap - expected) <= 0.1,
      string.format("第 %d 条间距 %.3f bp；小公式撑高了原本 %.3f bp 的行距", i - 1, gap, expected))
  end
end
