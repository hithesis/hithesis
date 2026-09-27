-- 题注：中文版“算法 1-1 迭代求解”，双语题注开着时下接“Algo. 1-1 Iterative solution”（深圳
-- “Algorithm”；深圳本科终稿改排本部模板，跟本部）；英文版只一行、题目取主参数。报告不排章，
-- 编号不带章号。关键字全大写且粗，冒号细。
return function(t)
  local num = t:fact("chapter") and "1-1" or "1"
  local en_label = (t:fact("shenzhen") and "Algorithm" or "Algo.") .. num
  if t:fact("en") then
    t:has(en_label .. "迭代求解")
    t:hasnt("Iterativesolution", "英文版不该再排一行英文题目")
  else
    t:has("算法" .. num .. "迭代求解")
    if t:fact("bilingual-caption") then
      t:has(en_label .. "Iterativesolution")
    else
      t:hasnt("Iterativesolution", "双语题注关着，不该排英文题目")
    end
  end
  t:bold("INPUT", true)
  t:bold("WHILE", true)
  local l, _, last = t:find("INPUT:")
  if l then
    t:expect(not l.glyphs[last].bold, "“INPUT:”的冒号该细")
  else
    t:fail("缺“INPUT:”")
  end
end
