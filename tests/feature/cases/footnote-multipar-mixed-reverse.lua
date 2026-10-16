local source = debug.getinfo(1, "S").source:gsub("^@", "")
local directory = source:match("^(.*[/\\])") or ""
local check = dofile(directory .. "footnote-multipar-mixed.lua")
return function(t) check(t, true) end
