return function(t)
  local before = t:find("TwoNoteBefore")
  local first = t:find("FirstReference")
  local second = t:find("SecondReference")
  local after = t:find("TwoNoteAfter")
  if not t:expect(before and first and second and after, "缺少两脚注分页探针正文") then return end
  t:expect(before.page == first.page, "能放下的第一条注及引用应留在当前页")
  t:expect(first.page < second.page, "两条独立脚注应允许分别换页")
  for _, group in ipairs({{first,"FirstNoteStart","FirstNoteEnd"},{second,"SecondNoteStart","SecondNoteEnd"}}) do
    local previous = nil
    for i = 2, 3 do
      local line = t:find(group[i])
      if t:expect(line ~= nil, "缺少脚注文字 " .. group[i]) then
        t:expect(line.page == group[1].page, "同条脚注不能拆，且应与引用同页")
        t:expect(t:count(group[i]) == 1, "脚注不能重复输出")
        if previous then t:expect(line.y > previous.y, "同条脚注文字顺序错误") end
        previous = line
      end
    end
  end
  t:expect(after.page > second.page, "后续正文不能越过待排脚注")
end
