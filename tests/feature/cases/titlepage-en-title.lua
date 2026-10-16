local function title(t, text, size)
  local line, first, last = t:find(text)
  if not t:expect(line ~= nil, "缺英文题目“" .. text .. "”") then return end
  for i = first, last do
    local glyph = line.glyphs[i]
    t:expect(math.abs(glyph.size - size) < 0.1,
      string.format("“%s”应为 %.0f 磅，实际 %.2f", text, size, glyph.size))
    t:expect(glyph.bold, "“" .. text .. "”应使用标题的粗体")
  end
end

return function(t)
  title(t, "FIRSTTITLE", 18)
  title(t, "SECONDTITLE", 22)
  title(t, "THIRDTITLE", 18)
  title(t, "AAAAAAAAAA", 18)
  t:hasnt("FirstTitle")
  t:hasnt("SecondTitle")
  t:hasnt("ThirdTitle")
end
