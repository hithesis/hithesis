-- Record font files of glyphs actually shipped, rather than merely declared.
local M = { used = {} }
local function clean(value)
  local result = tostring(value or ""):gsub("[\t\r\n]", " ")
  return result
end
local function visit(head)
  for n in node.traverse(head) do
    if n.id == node.id("glyph") then M.used[n.font] = true
    elseif n.id == node.id("hlist") or n.id == node.id("vlist") then
      if n.list then visit(n.list) end
    end
  end
end
function M.page()
  local box = tex.box[token.create("ShipoutBox").mode]
  if box and box.list then visit(box.list) end
end
function M.finish()
  local out = assert(io.open("used-fonts.tsv", "w"))
  out:write("id\tname\tfilename\tresolved\tsubfont\n")
  local ids = {}
  for id in pairs(M.used) do ids[#ids + 1] = id end
  table.sort(ids)
  for _, id in ipairs(ids) do
    local f = font.getfont(id) or {}
    local s, p = f.specification or {}, f.properties or {}
    out:write(table.concat({tostring(id), clean(f.fullname or f.fontname or f.name),
      clean(f.filename or p.filename or s.filename), clean(s.resolved),
      clean(f.subfont or s.sub or s.subfont)}, "\t"), "\n")
  end
  out:close()
end
return M
