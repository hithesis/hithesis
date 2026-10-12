-- 题注主行跟随文档语言，双语开关控制副行；续排不占新号，代码行号连续。
return function(t)
  local num = t:fact("chapter") and "1-1" or "1"
  if t:fact("en") then
    t:has("Listing" .. num .. "Permeability")
    if t:fact("bilingual-caption") then
      t:has("代码" .. num .. "求渗透率")
    else
      t:hasnt("求渗透率", "关闭双语时只排文档语言题注")
    end
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
