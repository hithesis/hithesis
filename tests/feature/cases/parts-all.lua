-- 学位论文专有的几样只在学位论文里排；答辩页与声明除博士后都排，永久通讯地址只有博士后排
return function(t)
  local b = t.branch
  local final = b.stage == "final"
  local postdoc = b["degree-level"] == "postdoc"
  local zh = b.lang ~= "en"
  if not final then
    for _, s in ipairs({ "中文摘要正文", "Englishabstractbody", "结论正文", "致谢正文", "简历正文", "地址正文" }) do
      t:hasnt(s, "报告里不该排“" .. s .. "”")
    end
    return
  end
  t:has("Englishabstractbody")
  t:has("致谢正文")
  if postdoc then t:has("地址正文") else t:hasnt("地址正文", "只有博士后有永久通讯地址") end
  if zh then
    if postdoc then
      t:hasnt("原创性声明", "博士后没有原创性声明")
      t:hasnt("答辩决议", "博士后没有答辩页")
    else
      t:has("原创性声明")
      t:has("答辩决议")
    end
  end
end
