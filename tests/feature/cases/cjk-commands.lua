-- 字号、两个汉字宽的空、中文计数、字族切换都排对了
return function(t)
  local l, a = t:find("三号字样")
  if t:expect(l ~= nil, "缺“三号字样”") then
    t:expect(math.abs(l.glyphs[a].size - 16) < 0.1,
      string.format("\\zihao{3} 该是 16 磅，排成了 %.2f", l.glyphs[a].size))
  end
  l, a = t:find("小四字样")
  if t:expect(l ~= nil, "缺“小四字样”") then
    t:expect(math.abs(l.glyphs[a].size - 12) < 0.1,
      string.format("\\zihao{-4} 该是 12 磅，排成了 %.2f", l.glyphs[a].size))
  end
  l, a = t:find("甲乙")
  if t:expect(l ~= nil, "缺“甲\\hspace{2\\ccwd}乙”") then
    local d = l.glyphs[a + 1].x - l.glyphs[a].x
    local s = l.glyphs[a].size
    t:expect(d > 2.8 * s and d < 3.3 * s,
      string.format("甲与乙之间该空两个汉字，两字相距 %.2f（字号 %.2f）", d, s))
  end
  t:has("计数十二止")
  local hei, song = t:font("黑体字样"), t:font("宋体字样")
  t:expect(hei ~= nil and song ~= nil and hei ~= song,
    string.format("\\CJKfamily{zhhei} 没换字体：%s 对 %s", tostring(hei), tostring(song)))
  t:has("一、甲项")
  t:has("二、乙项")
end
