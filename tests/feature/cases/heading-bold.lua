-- 行里每个字都得是 want 那样的粗细
local function whole_line(t, s, want, what)
  local l = t:find(s)
  if not t:expect(l ~= nil, "缺“" .. s .. "”") then return end
  for _, g in ipairs(l.glyphs) do
    if g.bold ~= want then
      return t:fail(string.format("%s该整行%s，“%s”排成了%s（%s）", what, want and "粗" or "细",
        g.ch, g.bold and "粗" or "细", g.font))
    end
  end
end

return function(t)
  local b = t.branch
  local postdoc = b["degree-level"] == "postdoc"
  -- 英文关键词：“Keywords”粗，后面的全角冒号细；博士后照模板整个“Keywords:”粗
  if postdoc then
    t:bold("Keywords:", true)
  else
    local l, a, z = t:find("Keywords：")
    if t:expect(l ~= nil, "缺“Keywords：”") then
      for i = a, z - 1 do t:expect(l.glyphs[i].bold, "“Keywords”该粗") end
      t:expect(not l.glyphs[z].bold, "“Keywords”后面的冒号该细")
    end
  end
  -- 中文关键词标签：黑体不加粗（博士后照模板加粗）
  if not t:fact("en") then
    t:bold("关键词", postdoc)
  end
  -- 中文版里英文摘要的标题不加粗（范例与 iota 都是细的）
  if not t:fact("en") and not postdoc then
    for _, l in ipairs(t:lines()) do
      if l.text == "Abstract" and l.glyphs[1].size > 15 then
        t:expect(not l.glyphs[1].bold, "英文摘要的标题该细")
        break
      end
    end
  end
  -- 目录章条目：中文目录细（博士后另算），英文目录整行粗
  if not t:fact("en") and not postdoc then
    whole_line(t, "第1章绪论", false, "中文目录的章条目")
  end
  if t:find("Chapter1Introduction") then
    whole_line(t, "Chapter1Introduction", true, "英文目录的章条目")
  end
end
