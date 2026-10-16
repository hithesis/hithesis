return function(t)
  local reference = t:find("PageReference")
  if not t:expect(reference ~= nil, "缺少页首正文对照") then return end
  local first_on_page, previous, first, step = {}, nil, nil, nil
  for i = 1, 50 do
    local name = "SplitRow" .. tostring(100 + i)
    if not t:expect(t:count(name) == 1, "跨页说明丢失或重复：" .. name) then return end
    local row = t:find(name)
    if not row then return end
    if not first then first = row end
    if not first_on_page[row.page] then first_on_page[row.page] = row end
    if previous then
      t:expect(row.page > previous.page or (row.page == previous.page and row.y > previous.y), "跨页说明顺序错误")
      if row.page == previous.page then
        local actual = row.y - previous.y
        if not step then step = actual end
        t:expect(math.abs(actual - step) <= 0.5, "同页说明行距不一致")
      end
    end
    previous = row
  end
  t:expect(previous.page > first.page, "长说明表必须实际跨页")
  for _, row in pairs(first_on_page) do
    t:expect(math.abs(row.y - reference.y) <= 0.5, "跨页首行应与正常页首正文同位")
  end
  t:has("AfterSplit")
  local a, b, last, after = t:find("WrappedStart"), t:find("WrappedEnd"), t:find("WrappedLast"), t:find("AfterWrapped")
  if t:expect(a and b and last and after, "折行说明或其后正文缺失") then
    t:expect(a.page == b.page and b.y > a.y, "折行控制应在同页实际折行")
    t:expect(last.page == b.page and last.y > b.y, "折行说明不能与下一条重叠")
    t:expect(after.page > last.page or after.y > last.y, "表后正文不能与末条重叠")
  end
  t:hasnt("DiscardedProbe")
  t:hasnt("DiscardedOne")
  local live, control = t:find("LiveBefore"), t:find("ControlBefore")
  if not t:expect(live and control, "缺少试排/正式边界对照") then return end
  for _, suffix in ipairs({"One", "Two", "After"}) do
    local x, y = t:find("Live" .. suffix), t:find("Control" .. suffix)
    if t:expect(x and y, "试排后说明丢失：" .. suffix) then
      t:expect(math.abs((x.y - live.y) - (y.y - control.y)) <= 0.5, "试排不应改变外层说明的接排")
    end
  end
  t:expect(t:count("EqNoteToken") == 1, "说明表测量不能重复或丢失前一段的脚注")
  local before_note, first_note_row, after_note = t:find("BeforeNote"), t:find("NoteOne"), t:find("AfterNote")
  if t:expect(before_note and first_note_row and after_note, "缺少带脚注的接排控制") then
    t:expect(before_note.page == first_note_row.page and after_note.page == first_note_row.page,
      "短注及说明表控制应能放在同页")
    t:expect(first_note_row.y > before_note.y and after_note.y > first_note_row.y, "带脚注的说明表接排顺序错误")
  end
end
