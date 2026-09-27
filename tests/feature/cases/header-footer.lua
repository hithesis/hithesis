-- 三页正文，每页页脚区（基线在 700 以下）有一行带数字；学位论文每页页眉区（基线在 125 以上）有一行字
return function(t)
  local rows = t:lines()
  for _, s in ipairs({ "第一页正文", "第二页正文", "第三页正文" }) do
    local pg = t:page_of(s)
    if t:expect(pg ~= nil, "缺“" .. s .. "”") then
      local foot, head = false, false
      for _, l in ipairs(rows) do
        if l.page == pg then
          if l.y > 700 and l.text:find("%d") then foot = true end
          if l.y < 125 then head = true end
        end
      end
      t:expect(foot, string.format("“%s”那一页（第 %d 页）没有页码", s, pg))
      if t:fact("chapter") then
        t:expect(head, string.format("“%s”那一页（第 %d 页）没有页眉", s, pg))
      end
    end
  end
end
