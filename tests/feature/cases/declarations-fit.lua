-- 声明的小标题与导师签名在同一页
return function(t)
  local head = t:page_of("原创性声明") or t:page_of("Declaration")
  local sign = t:page_of("导师签名")
  if t:expect(head ~= nil and sign ~= nil, "缺声明标题或导师签名") then
    t:expect(head == sign, string.format("声明从第 %d 页起，导师签名排到第 %d 页", head, sign))
  end
end
