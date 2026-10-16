return function(t)
  for _, mode in ipairs({ 11, 15 }) do
    local short = t.log:match("EN%-FIT short mode=" .. mode .. " removed=(%d+) fits=(%a+)")
    t:expect(short == "0", "普通英文内封不应删空段，mode=" .. mode)
    local removed, fits = t.log:match("EN%-FIT long mode=" .. mode .. " removed=(%d+) fits=(%a+)")
    t:expect(removed ~= nil and tonumber(removed) > 0 and fits == "yes",
      "长题目和多导师字段应通过减少空段放进一页，mode=" .. mode)
    local overflow_removed, overflow_fits = t.log:match("EN%-FIT overflow mode=" .. mode .. " removed=(%d+) fits=(%a+)")
    t:expect(overflow_removed == "3" and overflow_fits == "no",
      "极端内容应耗尽三档缩减并报告溢出，mode=" .. mode)
  end
  local start = 1
  for _ = 1, 2 do
    local candidate, _, _, at = t:find("LongCandidate", start)
    if t:expect(candidate ~= nil, "缺长题目页的作者字段") then
      for _, text in ipairs({ "AssociateValue", "IndustryValue", "SchoolofMechatronicsEngineering", "HarbinInstituteofTechnology" }) do
        local value = t:find(text, at)
        t:expect(value ~= nil and value.page == candidate.page,
          "字段“" .. text .. "”缺失或溢出长题目页")
      end
      start = at + 1
    end
  end
  t:expect(t:count("ShortCandidate") == 2, "普通内封内容缺失或重复")
  local overflow_count = t:count("ExcessCandidate")
  t:expect(overflow_count == 2, string.format("溢出回退应排出两次作者字段，实际找到 %d 次", overflow_count))
  local warnings = 0
  for _ in t.log:gmatch("英文内封排不下") do warnings = warnings + 1 end
  t:expect(warnings == 2, "应仅在两种兼容模式的极端内容上各警告一次")
end
