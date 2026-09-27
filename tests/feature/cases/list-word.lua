-- 编号在正文段首行缩进处（“正文。”那一段的首字），续行回到版心左缘；引用排出编号
return function(t)
  local body = t:find("正文。")
  if not t:expect(body ~= nil, "缺正文段") then return end
  local indent_x = body.glyphs[1].x
  local l = t:find("第一条")
  if not t:expect(l ~= nil, "缺第一条") then return end
  -- pdfLaTeX 的西文网格增量是 \letterspacefont 加宽的字体实例，字形居中在加宽后的步进里，
  -- 行首的西文字形比 Word 右移半份增量（小四 0.108），编号“(1)”落在首行缩进右边这么多
  local tol = t.engine == "pdflatex" and 0.2 or 0.1
  t:expect(math.abs(l.glyphs[1].x - indent_x) < tol,
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
