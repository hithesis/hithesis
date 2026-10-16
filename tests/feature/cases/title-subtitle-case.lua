return function(t)
  for _, marker in ipairs({"PLAINTITLE", "CHINESEONLYTITLE", "HIDDENTITLE"}) do
    local count = 0
    for _, line in ipairs(t:lines()) do
      if line.text:find(marker, 1, true) then
        count = count + 1
        t:expect(not line.text:find(marker .. "：", 1, true)
            and not line.text:find(marker .. ":", 1, true),
          "没有英文副题时多排分隔符：" .. line.text)
      end
    end
    t:expect(count == 2, marker .. " 应分别在外封与英文内封出现一次")
  end
  t:expect(t:count("WITHSUBTITLE") == 2 and t:count("ENGLISHSUB") == 2,
    "有英文副题时，外封和英文内封均应保留全部大写的主副题")
  local start = 1
  for _ = 1, 2 do
    local main, _, last, at = t:find("WITHSUBTITLE", start)
    local sub, first = t:find("ENGLISHSUB", start)
    if main and sub then
      t:expect(main.page == sub.page, "主副题应在同页")
      local colon = false
      for _, line in ipairs(t:lines()) do
        if line.page == main.page then
          for _, glyph in ipairs(line.glyphs) do
            if glyph.ch == "：" and glyph.x > main.glyphs[last].x
                and glyph.x < sub.glyphs[first].x and math.abs(glyph.y - main.y) < 1.5 then
              colon = true
            end
          end
        end
      end
      t:expect(colon, "主副题之间应保留分隔符，允许中西文字体的基线校正")
    end
    if not at then break end
    start = at + 1
  end
  t:hasnt("HIDDENSUB", "show-subtitle=false 应隐藏英文副题")
end
