return function(t, reverse)
  local marks = {}
  for _, name in ipairs({"MixedRefOne", "MixedRefTwo", "MixedShortStart", "MixedShortEnd", "MixedLongStart", "MixedLongEnd"}) do
    if not t:expect(t:count(name) == 1, "混排脚注标记丢失或重复：" .. name) then return end
    marks[name] = t:find(name)
    if not marks[name] then return end
  end
  local function before(a, b)
    return a.page < b.page or (a.page == b.page and a.y < b.y)
  end
  t:expect(before(marks.MixedRefOne, marks.MixedRefTwo), "同段两引用行的顺序错误")
  t:expect(marks.MixedShortStart.page == marks.MixedShortEnd.page, "能装页的短注应保持完整")
  t:expect(marks.MixedLongEnd.page > marks.MixedLongStart.page, "自身超页的长注应正常续排")
  if reverse then
    t:expect(before(marks.MixedLongEnd, marks.MixedShortStart), "后来的短注不能越过先引用的长注提前输出")
  else
    t:expect(marks.MixedShortStart.page == marks.MixedRefOne.page, "前面的短注不能被第二条超页注一起推迟")
    t:expect(before(marks.MixedShortEnd, marks.MixedLongStart), "短长双注的输出顺序错误")
  end
end
