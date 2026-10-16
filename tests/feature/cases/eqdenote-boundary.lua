return function(t)
  local suffixes = {"One", "Two", "Three", "After", "Heading", "End"}
  for _, context in ipairs({"Body", "Open", "Small", "Large", "Head", "Chain", "Top"}) do
    local marks = {}
    for _, kind in ipairs({"Table", "Plain"}) do
      local names = {"One", "Two", "Three", "After", "Heading", "End"}
      if context ~= "Top" then names[#names + 1] = "Before" end
      for _, suffix in ipairs(names) do
        local name = context .. kind .. suffix
        if not t:expect(t:count(name) == 1, "缺少或重复边界标记：" .. name) then return end
        marks[kind .. suffix] = t:find(name)
        if not marks[kind .. suffix] then return end
      end
    end
    local offset = context == "Top" and 0 or marks.TableBefore.y - marks.PlainBefore.y
    for _, suffix in ipairs(suffixes) do
      local difference = marks["Table" .. suffix].y - marks["Plain" .. suffix].y - offset
      t:expect(math.abs(difference) <= 0.5,
        string.format("%s/%s 说明表相对普通段落多出 %.3fbp", context, suffix, difference))
    end
    if context == "Top" then
      t:expect(marks.TableOne.page ~= marks.PlainOne.page, "页首对照必须在不同页")
    else
      t:expect(marks.TableBefore.page == marks.TableEnd.page and marks.PlainBefore.page == marks.PlainEnd.page,
        "短边界控制不应跨页：" .. context)
    end
  end
end
