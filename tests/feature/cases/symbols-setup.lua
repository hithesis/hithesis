-- 单独的符号表与合页各排一遍；说明按语种取；组名当小标题
return function(t)
  local en = t:fact("en")
  if en then
    t:expect(t:count("Pressurealpha") == 2, "英文说明该出现两次（符号表与合页）")
    t:hasnt("压力甲", "英文版不该取中文说明")
  else
    t:expect(t:count("压力甲") == 2, "中文说明该出现两次（符号表与合页）")
    t:hasnt("Pressurealpha", "中文版不该取英文说明")
  end
  t:expect(t:count("黏度乙") == 2, "不分语种的说明该出现两次")
  t:expect(t:count("拉丁字母") == 2, "组名该当小标题排两次")
end
