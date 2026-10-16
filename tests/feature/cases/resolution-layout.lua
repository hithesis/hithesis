return function(t)
  t:expect(t.log:find("RES%-SPLITPARAMS top%-ok depth%-ok") ~= nil,
    "决议续页应恢复调用者的 splittopskip 和 splitmaxdepth")
  for _, text in ipairs({ "张三", "李四", "王五", "赵六", "决议首段标记", "决议末段标记" }) do
    t:has(text)
  end
  t:bold("答辩委员会决议", true)
  t:expect(t:count("决议首段标记") == 1, "决议首段丢失或被试排重复输出")
  t:expect(t:count("决议末段标记") == 1, "决议末段丢失或被试排重复输出")
  local first, last = t:page_of("决议首段标记"), t:page_of("决议末段标记")
  if first and last then t:expect(last > first, "长决议没有接排到下一页") end
  local line, at = t:find("决议首段标记")
  if line then
    t:expect(math.abs(line.glyphs[at].size - 10.5) < 0.1, "人文社科决议正文应使用五号字")
  end
end
