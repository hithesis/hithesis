return function(t)
  t:hasnt("Empty")
  t:hasnt("CaseValue")
  local function near(actual, expected, name)
    t:expect(math.abs(actual - expected) < 0.1,
      string.format("%s应为 %.1f bp，实际 %.3f bp", name, expected, actual))
  end
  for _, mode in ipairs({ "ModeEleven", "ModeFifteen" }) do
    local head, _, _, start = t:find(mode)
    if t:expect(head ~= nil, "缺兼容模式标记“" .. mode .. "”") then
      local positions = {}
      for _, text in ipairs({ "Single", "One", "Double", "TwoA", "TwoB",
          "Triple", "ThreeA", "ThreeB", "ThreeC", "Wrapped", "Condensed",
          "SchoolofMechatronicsEngineering", "Manual", "FourA", "FourB",
          "Last", "Final", "Styled", "CASEVALUE" }) do
        local line = t:find(text, start)
        if t:expect(line ~= nil and line.page == head.page, "缺字段“" .. text .. "”或字段溢出当前页") then
          positions[text] = line.y
        end
      end
      local function step(a, b, expected)
        if positions[a] and positions[b] then
          near(positions[b] - positions[a], expected, mode .. " " .. a .. "→" .. b)
        end
      end
      step("Single", "One", 0)
      step("Double", "TwoA", -3.2)
      step("TwoA", "TwoB", 18)
      step("ThreeA", "ThreeB", 18)
      step("ThreeB", "ThreeC", 18)
      step("Single", "Double", 22)
      step("Double", "Triple", 36)
      step("Triple", "Wrapped", 54)
      step("Wrapped", "Condensed", 72)
      step("Condensed", "Manual", 22)
      step("Manual", "Last", 36)
      step("Last", "Final", 0)
      step("Last", "Styled", 22)
    end
  end
end
