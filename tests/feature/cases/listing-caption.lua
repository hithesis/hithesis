-- 题注：中文版“代码 1-1 求渗透率”，双语题注开着时下接“Listing 1-1 Permeability”；英文版只一行
-- “Listing 1-1 求渗透率”。报告不排章，编号不带章号。续排的题注是“代码1-1（续代码）”，行号接着
-- 数（3、4）。没写题注的代码块不编行号。
return function(t)
  local num = t:fact("chapter") and "1-1" or "1"
  if t:fact("en") then
    t:has("Listing" .. num .. "求渗透率")
    t:hasnt("Permeability", "英文版不该再排一行英文题目")
    t:has("Listing" .. num .. "(Continued)")
  else
    t:has("代码" .. num .. "求渗透率")
    if t:fact("bilingual-caption") then
      t:has("Listing" .. num .. "Permeability")
    else
      t:hasnt("Permeability", "双语题注关着，不该排英文题目")
    end
    t:has("代码" .. num .. "（续代码）")
  end
  t:has("1defhead(n):")
  t:has("3deftail(n):")
  t:has("plain=True")
  t:hasnt("1plain=True", "正文代码块不该编行号")
end
