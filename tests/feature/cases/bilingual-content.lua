return function(t)
  for _, text in ipairs({
    "子图甲", "Sub Alpha", "子图乙", "Sub Beta", "图甲", "Figure Alpha",
    "代码甲", "Code Alpha", "长表甲", "Table Alpha", "长表乙", "Table Beta",
    "算法甲", "Algorithm Alpha",
    "补充说明", "Additional Note",
  }) do
    t:has(text)
  end
  t:hasnt("[Code Alpha]", "代码题注不能把双语分隔符当成正文")
  t:hasnt("[Table Alpha]", "长表题注不能把双语分隔符当成正文")
end
