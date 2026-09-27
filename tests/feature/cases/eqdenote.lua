-- 三行的破折号横坐标相同，说明的首字横坐标相同
return function(t)
  local xs, ts = {}, {}
  for _, s in ipairs({ "斜率甲", "自变量乙", "截距丙" }) do
    local l, a = t:find(s)
    if t:expect(l ~= nil, "缺“" .. s .. "”") then
      ts[#ts + 1] = l.glyphs[a].x
      for i = a - 1, 1, -1 do
        if l.glyphs[i].ch == "—" then xs[#xs + 1] = l.glyphs[i].x; break end
      end
    end
  end
  for i = 2, #xs do
    t:expect(math.abs(xs[i] - xs[1]) < 0.05, string.format("第 %d 行的破折号在 %.2f，第一行在 %.2f", i, xs[i], xs[1]))
  end
  for i = 2, #ts do
    t:expect(math.abs(ts[i] - ts[1]) < 0.05, string.format("第 %d 行的说明从 %.2f 起，第一行从 %.2f", i, ts[i], ts[1]))
  end
  t:has("末段正文")
end
