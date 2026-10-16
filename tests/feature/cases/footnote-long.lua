return function(t)
  for _, mode in ipairs({15}) do
    local fitting = {}
    for _, prefix in ipairs({"FitReference", "FitStart", "FitEnd"}) do
      local key = prefix .. mode
      fitting[#fitting + 1] = t:find(key)
      t:expect(t:count(key) == 1, "可装页注的标记丢失或重复：" .. key)
    end
    if fitting[1] and fitting[2] and fitting[3] then
      t:expect(fitting[1].page == fitting[2].page and fitting[2].page == fitting[3].page,
        "能装下一页的单段注仍应随引用整段移页，模式 " .. mode)
    end
    local first, last = t:find("LongStart" .. mode), t:find("LongEnd" .. mode)
    t:expect(t:count("LongReference" .. mode) == 1, "长注引用丢失或重复，模式 " .. mode)
    t:expect(t:count("LongStart" .. mode) == 1 and t:count("LongEnd" .. mode) == 1,
      "超页注首尾标记丢失或重复，模式 " .. mode)
    if first and last then
      t:expect(last.page > first.page, "自身超页的单段注必须能有限续排，模式 " .. mode)
    end
  end
end
