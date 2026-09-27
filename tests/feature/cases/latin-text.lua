-- 字母叠在一起时按横坐标排出来的字序是乱的，找不到原词；再看词宽，至少得有字号的两倍
return function(t)
  t:has("HelloWorld")
  t:has("2026")
  t:has("BOLD")
  local l, a, z = t:find("Hello")
  if l then
    local w = l.glyphs[z].x - l.glyphs[a].x
    t:expect(w > 1.5 * l.glyphs[a].size,
      string.format("“Hello”首尾两字只隔 %.2f，字母叠在一起了", w))
  end
end
