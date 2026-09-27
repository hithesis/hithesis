return function(t)
  t:has("表1-1试样渗透率测试数据")
  if t:fact("bilingual-caption") then
    t:has("Table1-1Dataofmeasuredpermeabilityofsamples")
  else
    t:hasnt("Dataofmeasured", "双语题注关着，不该排英文题目")
  end
  t:has("表1-2一个很长很长的表题")
  -- 表清单里各一条，英文那行不进
  t:expect(t:count("试样渗透率测试数据") == 2, "中文题注该在正文与表清单里各出现一次")
  t:expect(t:count("Dataofmeasured") <= 1, "英文题注不该进表清单")
end
