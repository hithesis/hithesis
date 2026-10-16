return function(t, reverse)
  local marks = {}
  for _, name in ipairs({"RefOne", "RefTwo", "SeparateStart", "SeparateEnd", "FirstStart", "FirstEnd",
      "MiddleStart", "MiddleEnd", "LastStart", "LastEnd"}) do
    if not t:expect(t:count(name) == 1, "多段长注混排标记丢失或重复：" .. name) then return end
    marks[name] = t:find(name)
    if not marks[name] then return end
  end
  local function before(a, b)
    return a.page < b.page or (a.page == b.page and a.y < b.y)
  end
  t:expect(before(marks.RefOne, marks.RefTwo), "引用行顺序错误")
  for _, pair in ipairs({{"SeparateStart", "SeparateEnd"}, {"FirstStart", "FirstEnd"}, {"LastStart", "LastEnd"}}) do
    t:expect(marks[pair[1]].page == marks[pair[2]].page, "能装页的短注段应保持完整：" .. pair[1])
  end
  t:expect(marks.MiddleStart.page > marks.FirstEnd.page, "自身超页的中段应在新注页重试")
  t:expect(marks.MiddleEnd.page > marks.MiddleStart.page, "中段应正常续排")
  t:expect(before(marks.MiddleEnd, marks.LastStart), "末段不能越过中段")
  if reverse then
    t:expect(marks.FirstStart.page == marks.RefOne.page, "长注可装页的首段应与其引用同页")
    t:expect(before(marks.LastEnd, marks.SeparateStart), "后引用的短注不能越过多段长注")
  else
    t:expect(marks.SeparateStart.page == marks.RefOne.page, "先引用的短注应留在其引用页")
    t:expect(before(marks.SeparateEnd, marks.FirstStart), "两条注的顺序错误")
    t:expect(marks.FirstStart.page == marks.RefTwo.page, "长注首段不应随中间超页段延期")
  end
end
