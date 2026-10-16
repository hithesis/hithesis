local source = debug.getinfo(1, "S").source:gsub("^@", "")
local directory = source:match("^(.*[/\\])") or ""
return dofile(directory .. "footnote-paragraphs.lua")
