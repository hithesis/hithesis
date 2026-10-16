return function(t)
  local previous
  for n=101,160 do
    local name="N" .. n
    t:expect(t:count(name) == 1, "跨页人员缺失或重复：" .. name)
    local row=t:find(name)
    if previous and row then
      t:expect(row.page > previous.page or (row.page == previous.page and row.y > previous.y), "名单顺序错误")
    end
    previous=row
  end
  local first,last=t:find("N101"),t:find("N160")
  if t:expect(first and last,"缺少跨页首末人员") then
    t:expect(last.page > first.page,"长名单应真实跨页")
    local title=t:fact("en") and "Role" or "职务"
    for page=first.page,last.page do
      local found=false
      for _,line in ipairs(t:lines()) do
        if line.page == page and line.text:find(title,1,true) then found=true end
      end
      t:expect(found,"名单续页缺少表头：" .. page)
    end
  end
  for _,name in ipairs({"R101","C101","S101","LongDecisionStart","LongDecisionEnd"}) do t:has(name) end
  local secretary,decision=t:find("S101"),t:find("LongDecisionStart")
  if secretary and decision then
    t:expect(decision.page > secretary.page or (decision.page == secretary.page and decision.y > secretary.y),"决议应在全部名单之后")
  end
  t:expect(not t.log:find("Overfull \\[hv]box"),"长名单不应溢出")
end
