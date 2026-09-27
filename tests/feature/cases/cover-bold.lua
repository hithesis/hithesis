-- 第一页上的“哈尔滨工业大学”：楷体，每个字都粗
return function(t)
  for _, l in ipairs(t:lines()) do
    if l.page == 1 then
      local b = l.text:find("哈尔滨工业大学", 1, true)
      if b then
        local first = utf8.len(l.text:sub(1, b - 1)) + 1
        for i = first, first + 6 do
          local g = l.glyphs[i]
          t:expect(g.font:find("KaiTi") ~= nil, "封面校名该是楷体，排成了 " .. g.font)
          t:expect(g.bold, "封面校名的“" .. g.ch .. "”该粗")
        end
        return
      end
    end
  end
  t:fail("第一页上没有“哈尔滨工业大学”")
end
