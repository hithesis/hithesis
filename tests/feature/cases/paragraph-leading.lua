return function(t)
  local markers = {
    "LeadingOneA", "LeadingOneB", "LeadingTwoA",
    "LeadingTwoB", "LeadingThreeA", "LeadingThreeB",
  }
  local lines = {}
  for _, marker in ipairs(markers) do
    local line = t:find(marker)
    if not t:expect(line ~= nil, "缺少行标记：" .. marker) then return end
    lines[#lines + 1] = line
  end
  local expected = lines[2].y - lines[1].y
  t:expect(expected > 12, "倍数行距未生效")
  for i = 2, #lines do
    t:expect(lines[i].page == lines[1].page, "短多段探针应保持同页")
    local gap = lines[i].y - lines[i - 1].y
    t:expect(math.abs(gap - expected) <= 0.1,
      string.format("第 %d 条行间距 %.3f bp，与段内间距 %.3f bp 不一致", i - 1, gap, expected))
  end
end
