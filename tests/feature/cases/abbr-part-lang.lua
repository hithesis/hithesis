-- 两篇摘要各按自己的语种全写一次、之后排缩写，正文再全写一次（跟全文的语种）
return function(t)
  t:has("用有限元方法（FiniteElementMethod，FEM）求解")
  t:has("再用FEM验算")
  t:has("SolvedbyFiniteElementMethod(FEM).")
  t:has("CheckedbyFEMagain")
  if t.branch.lang == "en" then
    t:has("正文里的FiniteElementMethod(FEM)。")
  else
    t:has("正文里的有限元方法（FiniteElementMethod，FEM）。")
  end
end
