local glyph, hlist, vlist = node.id('glyph'), node.id('hlist'), node.id('vlist')
local cases = 0
local function visit(box, fn)
  for n in node.traverse(box.head) do
    if n.id == glyph then fn(n)
    elseif n.id == hlist or n.id == vlist then visit(n, fn) end
  end
end
function baseline_check_box(index, role, enabled)
  local box, before, count, latin = tex.box[index], {}, 0, 0
  local width, height, depth = box.width, box.height, box.depth
  visit(box, function(n) before[node.direct.todirect(n)] = n.yoffset end)
  docxlike.run.baseline_shift(box)
  visit(box, function(n)
    local f = font.getfont(n.font)
    local r = f.properties and docxlike.run.baseline_records[f.properties.docxlike_baseline]
    if r then
      assert(r.role == role, 'wrong role: '..r.role..' expected '..role..' font='..tostring(f.fullname)..' char='..n.char
        ..' shared='..tostring(f.shared and f.shared.features and f.shared.features.docxbaseline)
        ..' spec='..tostring(f.specification and f.specification.features and f.specification.features.normal.docxbaseline))
      local expected = enabled and math.floor(r.delta*f.size+0.5) or 0
      assert(n.yoffset-before[node.direct.todirect(n)] == expected, 'incorrect glyph offset')
      assert(math.abs(r.center+r.delta-r.reference) < 0.001, 'ink center not aligned')
      count = count+1
    else
      assert(n.yoffset == before[node.direct.todirect(n)], 'Latin/math glyph moved')
      latin = latin+1
    end
  end)
  assert(count >= 5 and latin >= 3, 'missing tagged CJK or Latin glyphs')
  local once = {}
  visit(box, function(n) once[node.direct.todirect(n)] = n.yoffset end)
  docxlike.run.baseline_shift(box)
  visit(box, function(n) assert(n.yoffset == once[node.direct.todirect(n)], 'offset applied twice') end)
  assert(box.width == width and box.height == height and box.depth == depth, 'box resized')
  cases = cases+1
  texio.write_nl('term and log', 'BASELINE BOX PASS '..cases..' '..role)
end
local function signature(box)
  local out = {}
  local function walk(n)
    while n do
      local fields = {n.id,n.subtype}
      for _, k in ipairs({'char','font','width','height','depth','kern','penalty',
                          'stretch','shrink','stretch_order','shrink_order',
                          'shift','glue_set','glue_sign','glue_order'}) do
        local ok, value = pcall(function() return n[k] end)
        if ok and value ~= nil then fields[#fields+1] = k..'='..tostring(value) end
      end
      out[#out+1] = table.concat(fields,':')
      if n.id == hlist or n.id == vlist then walk(n.head) end
      n = n.next
    end
  end
  walk(box)
  return table.concat(out,'\n')
end
function baseline_check_layout(a,b)
  local x,y = tex.box[a],tex.box[b]
  assert(signature(x) == signature(y), 'layout differs before shipout')
  docxlike.run.baseline_shift(x)
  docxlike.run.baseline_shift(y)
  assert(signature(x) == signature(y), 'layout differs after correction')
  cases = cases+1
  texio.write_nl('term and log','BASELINE LAYOUT PASS')
end
function baseline_finish()
  assert(cases == 14, 'incomplete baseline tests')
  texio.write_nl('term and log','BASELINE ALL PASS: '..cases)
end
