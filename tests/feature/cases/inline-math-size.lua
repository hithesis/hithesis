return function(t)
  local text_height, text_depth = t.log:match("MATH%-TEXT height=([%d%.]+),%s*depth=([%d%.]+)")
  if not t:expect(text_height ~= nil, "缺少普通文字实际高深") then return end
  text_height, text_depth = tonumber(text_height), tonumber(text_depth)
  for _, name in ipairs({ "Fraction", "Matrix", "Boxed" }) do
    local height, depth = t.log:match("LARGE%-MATH " .. name .. " height=([%d%.]+),%s*depth=([%d%.]+)")
    if not t:expect(height ~= nil, "缺少公式实际高深：" .. name) then return end
    height, depth = tonumber(height), tonumber(depth)
    t:expect(height > text_height or depth > text_depth, "大公式探针应确实超出文字高深：" .. name)
    local before, large, after = t:find(name .. "Before"), t:find(name .. "Large"), t:find(name .. "After")
    if not t:expect(before and large and after, "缺少公式前后行：" .. name) then return end
    if t:expect(before.page == large.page and large.page == after.page, "短大公式探针应保持同页：" .. name) then
      local incoming, outgoing = large.y - before.y, after.y - large.y
      t:expect(incoming + 0.1 >= text_depth + height,
        string.format("%s 与上一行碰撞：间距 %.3f bp，实际盒至少需要 %.3f bp", name, incoming, text_depth + height))
      t:expect(outgoing + 0.1 >= depth + text_height,
        string.format("%s 与下一行碰撞：间距 %.3f bp，实际盒至少需要 %.3f bp", name, outgoing, depth + text_height))
    end
  end
end
