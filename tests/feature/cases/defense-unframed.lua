return function(t)
  for _, text in ipairs({"ChairOne", "MemberOne", "MemberTwo", "SecretaryOne", "UnitStart", "UnitEnd",
      "DecisionStart", "DecisionEnd", "AfterDefense"}) do
    t:expect(t:count(text) == 1, "无框名单或决议内容缺失/重复：" .. text)
  end
  t:expect(t.log:find("UNFRAMED%-TABLE%-COUNTER=17") ~= nil, "无框名单不应消耗表号")
  t:expect(t.log:find("UNFRAMED%-RESOLUTION%-CALLS=1") ~= nil, "决议正文应只执行一次")
  t:expect(not t.log:find("Overfull \\[hv]box"), "无框名单不应溢出版心")
  local a, b = t:find("UnitStart"), t:find("UnitEnd")
  if t:expect(a and b, "缺少长字段边界") then
    t:expect(a.page == b.page and b.y > a.y, "长单位名称应在同一人员行内折行")
  end
  local last, first, ending, after = t:find("SecretaryOne"), t:find("DecisionStart"), t:find("DecisionEnd"), t:find("AfterDefense")
  local function precedes(x,y) return x.page < y.page or (x.page == y.page and x.y < y.y) end
  if t:expect(last and first and ending and after, "名单/决议接排控制缺失") then
    t:expect(precedes(last,first) and precedes(first,ending) and precedes(ending,after), "名单、决议及后续正文顺序错误")
  end
  if t:fact("en") then
    t:has("Role"); t:has("Discipline"); t:has("Defense Committee Resolution")
    for _, line in ipairs(t:lines()) do
      t:expect(not line.text:match("^Reviewer"), "未填写评阅人时不应生成评阅人行")
    end
  else
    t:has("职务"); t:has("工作单位"); t:has("答辩委员会决议")
    t:hasnt("评阅人（根据实际")
  end
end
