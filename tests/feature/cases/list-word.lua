-- 编号在正文段首行缩进处（“正文。”那一段的首字），续行回到版心左缘；引用排出编号
return function(t)
  local body = t:find("正文。")
  if not t:expect(body ~= nil, "缺正文段") then return end
  local indent_x = body.glyphs[1].x
  local l = t:find("第一条")
  if not t:expect(l ~= nil, "缺第一条") then return end
  t:expect(math.abs(l.glyphs[1].x - indent_x) < 0.1,
    string.format("编号该在首行缩进处 %.2f，排在 %.2f", indent_x, l.glyphs[1].x))
  local lines = t:lines()
  for i, x in ipairs(lines) do
    if x == l then
      local nx = lines[i + 1]
      t:expect(nx.glyphs[1].x < indent_x - 10, "续行该回到版心左缘")
      break
    end
  end
  t:expect(l.text:find("^（1）第一条") or l.text:find("^%(1%)第一条") or l.text:find("^1%.第一条"),
    "编号的样子不对：" .. l.text:sub(1, 30))
  t:expect(t:find("见第（2）条") or t:find("见第(2)条") or t:find("见第2.条"), "引用该排出编号")
end
