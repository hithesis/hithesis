-- 目录页上“第1章”那一条：题名首字（“章”后面那个字）的横坐标，与下一行首字的横坐标相同；
-- 末行（下一行）以页码“1”收尾，且页码前有题名的字
return function(t)
  local lines = t:lines()
  for i, l in ipairs(lines) do
    local a = l.text:find("第1章基于", 1, true)
    if a then
      local first = utf8.len(l.text:sub(1, a - 1)) + 4
      local x0 = l.glyphs[first].x
      local nx = lines[i + 1]
      if not t:expect(nx and nx.page == l.page, "章条目没有折行") then return end
      t:expect(math.abs(nx.glyphs[1].x - x0) < 0.1,
        string.format("续行首字在 %.2f，题名首字在 %.2f，该悬挂到题名首字", nx.glyphs[1].x, x0))
      t:expect(nx.text:sub(-1) == "1", "末行该以页码收尾：" .. nx.text)
      t:expect(nx.text:find("研究", 1, true) ~= nil, "页码独占了一行：" .. nx.text)
      return
    end
  end
  t:fail("目录里找不到“第1章基于”")
end
