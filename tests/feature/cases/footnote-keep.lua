return function(t)
  local before = t:find("PolicyBefore")
  local reference = t:find("PolicyReference")
  local after = t:find("PolicyAfter")
  if not t:expect(before and reference and after, "缺少学校脚注页底探针正文") then return end
  t:expect(reference.page > before.page, "页底放不下整注时，引用应随整注移到后页")
  local last = nil
  for _, text in ipairs({"NoteOne", "NoteTwo", "NoteThree", "NoteFour"}) do
    local line = t:find(text)
    if t:expect(line ~= nil, "缺少脚注行 " .. text) then
      t:expect(line.page == reference.page, "学校脚注不应跨页：" .. text)
      t:expect(t:count(text) == 1, "脚注文字不能因分页重试而重复：" .. text)
      if last then t:expect(line.y > last.y, "脚注行应依次向下排") end
      last = line
    end
  end
  t:expect(after.page > reference.page, "clearpage 后的正文应位于脚注后页")
end
