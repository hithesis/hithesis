return function(t)
  for _, text in ipairs({ "评审甲", "评审乙", "评审丙", "主席甲", "委员甲", "委员乙", "联合研究中心", "名单试排后的决议标记" }) do
    t:has(text)
  end
  t:expect(t.log:find("ROSTER%-ROWS 3/1/5/1") ~= nil,
    "超额评阅人应借用一行空白委员行，总预留行数保持十行")
  t:expect(t:count("名单试排后的决议标记") == 1, "名单试排不能重复或丢失决议正文")
  local reviewer = t:page_of("评审甲")
  local last = t:page_of("联合研究中心")
  t:expect(reviewer ~= nil and reviewer == last, "长单位名称缺失或被切到另一页")
end
