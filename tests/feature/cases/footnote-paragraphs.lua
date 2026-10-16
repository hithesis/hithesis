return function(t)
  local marks = {}
  for _, name in ipairs({"ParagraphReference", "ShortFirstStart", "ShortFirstEnd",
      "MiddleStart", "MiddleEnd", "ShortLastStart", "ShortLastEnd"}) do
    t:expect(t:count(name) == 1, "注段标记丢失或重复：" .. name)
    marks[name] = t:find(name)
  end
  for _, name in ipairs({"ParagraphReference", "ShortFirstStart", "ShortFirstEnd",
      "MiddleStart", "MiddleEnd", "ShortLastStart", "ShortLastEnd"}) do
    if not marks[name] then return end
  end
  t:expect(marks.ShortFirstStart.page == marks.ParagraphReference.page,
    "可装页的首段应与引用同页，不能随中间超高段整体延期")
  t:expect(marks.ShortFirstStart.page == marks.ShortFirstEnd.page, "首段应保持完整")
  t:expect(marks.MiddleStart.page > marks.ShortFirstEnd.page, "超高的中间段应先在新注页重试")
  t:expect(marks.MiddleEnd.page > marks.MiddleStart.page, "中间自动折行段必须能续页")
  t:expect(marks.ShortLastStart.page == marks.ShortLastEnd.page, "末段应保持完整")
  t:expect(marks.ShortLastStart.page >= marks.MiddleEnd.page, "末段不得越过中间段")
  if marks.ShortLastStart.page == marks.MiddleEnd.page then
    t:expect(marks.ShortLastStart.y > marks.MiddleEnd.y, "注段顺序错误")
  end
end
