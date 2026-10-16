return function(t)
  local before1 = t:find("BeforeOne")
  local before2 = t:find("BeforeTwo")
  local caption1 = t:find("CaptionOne")
  local caption2 = t:find("CaptionTwo")
  local ending = t:find("题注终点")
  if not t:expect(before1 and before2 and caption1 and caption2 and ending,
      "缺少长表首行位置探针标记") then return end
  t:expect(caption1.page == before1.page and caption2.page == before2.page,
    "短长题注都应留在各自的表前正文页")
  t:expect(ending.page == caption2.page and ending.y > caption2.y + 20,
    "长题注应实际折成多行")
  local a = caption1.y - before1.y
  local b = caption2.y - before2.y
  t:expect(math.abs(a - b) < 0.1,
    string.format("题注首行受总盒高影响：短题 %.3f bp，长题 %.3f bp", a, b))
  t:has("短表甲")
  t:has("长表甲")
  t:has("AfterOne")
  t:has("AfterTwo")
end
