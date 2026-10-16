kpse.set_program_name("lualatex")

local function hex4(n)
  return string.format('"%04X', n)
end

local function merged_ranges(list)
  local out, a, b = {}, nil, nil
  for _, u in ipairs(list) do
    if a == nil then
      a, b = u, u
    elseif u == b + 1 then
      b = u
    else
      out[#out + 1] = (a == b) and hex4(a) or (hex4(a) .. "-" .. hex4(b))
      a, b = u, u
    end
  end
  if a then
    out[#out + 1] = (a == b) and hex4(a) or (hex4(a) .. "-" .. hex4(b))
  end
  return table.concat(out, ",")
end

local function cmap_set(path)
  local f = assert(fontloader.open(path), "open failed: " .. tostring(path))
  local t = fontloader.to_table(f)
  fontloader.close(f)
  local set = {}
  for _, g in pairs(t.glyphs or {}) do
    if g.unicode and g.unicode >= 0x20 then
      set[g.unicode] = true
    end
    if type(g.unicodes) == "table" then
      for _, u in ipairs(g.unicodes) do
        if u >= 0x20 then
          set[u] = true
        end
      end
    end
  end
  return set
end

local function file_exists(path)
  local fh = io.open(path, "rb")
  if fh then
    fh:close()
    return true
  end
  return false
end

local function find_tnr()
  local env = os.getenv("TIMES_MATH_TNR")
  local dirs = {
    "/System/Library/Fonts/Supplemental/",
    "/Library/Fonts/",
    "/Users/" .. (os.getenv("USER") or "") .. "/Library/Fonts/",
    "C:/Windows/Fonts/",
    "C:\\Windows\\Fonts\\",
    "/usr/share/fonts/truetype/msttcorefonts/",
    "/usr/share/fonts/truetype/msttcorefonts/Times_New_Roman/",
    "/usr/share/fonts/wine/",
  }
  local name_sets = {
    {"Times New Roman.ttf", "Times New Roman Italic.ttf", "Times New Roman Bold Italic.ttf"},
    {"times.ttf", "timesi.ttf", "timesbi.ttf"},
    {"Times_New_Roman.ttf", "Times_New_Roman_Italic.ttf", "Times_New_Roman_Bold_Italic.ttf"},
    {"timesnewroman.ttf", "timesnewromanitalic.ttf", "timesnewromanbolditalic.ttf"},
  }
  if env and file_exists(env) then
    local dir = env:match("^(.*)/") or "."
    local base = env:match("([^/]+)$") or env
    local i1 = base:gsub("%.ttf$", " Italic.ttf")
    local i2 = base:gsub("%.ttf$", " Bold Italic.ttf")
    if file_exists(dir .. "/" .. i2) then
      return {dir .. "/" .. base, dir .. "/" .. i1, dir .. "/" .. i2}
    end
    return {env, env, env}
  end
  for _, dir in ipairs(dirs) do
    for _, names in ipairs(name_sets) do
      if file_exists(dir .. names[1]) and file_exists(dir .. names[2]) and file_exists(dir .. names[3]) then
        return {dir .. names[1], dir .. names[2], dir .. names[3]}
      end
    end
  end
  return nil
end

local function find_tgt()
  local r = assert(kpse.find_file("texgyretermes-regular.otf", "opentype fonts"))
  local i = assert(kpse.find_file("texgyretermes-italic.otf", "opentype fonts"))
  local b = assert(kpse.find_file("texgyretermes-bolditalic.otf", "opentype fonts"))
  return {r, i, b}
end

local table_path = assert(kpse.find_file("unicode-math-table.tex"))
local sty_path = assert(kpse.find_file("unicode-math-luatex.sty"))

local slots, mathclass, wide_accents, integrals = {}, {}, {}, {}
for line in io.lines(table_path) do
  local hex, class = line:match('\\UnicodeMathSymbol%{"([0-9A-Fa-f]+)}.-}{\\math([a-z]+)}')
  if hex then
    local cp = tonumber(hex, 16)
    slots[cp] = true
    mathclass[cp] = mathclass[cp] or class
    if class == "accentwide" or class == "botaccentwide" then
      wide_accents[#wide_accents + 1] = {cp = cp, class = class}
    end
    if class == "op" and ((cp >= 0x222B and cp <= 0x2233)
      or (cp >= 0x2A0B and cp <= 0x2A1C)) then
      integrals[#integrals + 1] = cp
    end
  end
end

local alph = {}
for line in io.lines(sty_path) do
  local a, b = line:match("\\__um_new_alphabet_config:nnn%s+{(.-)}%s+{(.-)}")
  if a then
    alph[#alph + 1] = {a, b}
  end
end

local usv = {}
for line in io.lines(sty_path) do
  local s, l, v = line:match("\\usv_set:nnn%s+{(.-)}%s+{(.-)}%s+{([^\\}]+)}")
  if s and l and v then
    local hex = v:match('^"(.-)$')
    local cp = hex and tonumber(hex, 16) or tonumber(v)
    if cp then
      usv[s] = usv[s] or {}
      usv[s][l] = cp
    end
  end
end

local TEXT_FONT_SKIP = {
  open = true, close = true, fence = true,
  op = true,
  accent = true, accentwide = true, botaccent = true,
  botaccentwide = true, accentoverlay = true, under = true,
}
local MATH_FONT_SKIP = {
  accent = true, accentwide = true, botaccentwide = true,
}
local TEXT_FONT_ALLOW = {[0x0021] = true}

local function slot_list(cmap, skip)
  local list = {}
  for u in pairs(slots) do
    if cmap[u] and (not (skip and skip[mathclass[u]]) or TEXT_FONT_ALLOW[u]) then
      list[#list + 1] = u
    end
  end
  table.sort(list)
  return list
end

local function exists(style, letters, cmap)
  if letters == "misc" then
    return false
  end
  local cp = usv[style] and usv[style][letters]
  return cp ~= nil and cmap[cp] == true
end

local function keep_up(style, letters, cmap)
  if letters ~= "latin" and letters ~= "Latin" and letters ~= "greek"
    and letters ~= "Greek" and letters ~= "num" then
    return false
  end
  return style == "bfup" or exists(style, letters, cmap)
end

local function clauses(fn)
  local out = {}
  for _, c in ipairs(alph) do
    if fn(c[1], c[2]) then
      out[#out + 1] = c[1] .. "/{" .. c[2] .. "}"
    end
  end
  return table.concat(out, ",")
end

local function base_block(base, cmap)
  local list = slot_list(cmap, TEXT_FONT_SKIP)
  local extra = clauses(function(s, l)
    return (s == "up" or s == "bfup") and keep_up(s, l, cmap)
  end)
  return {
    "\\setmathfont{" .. base .. "}[range={" .. merged_ranges(list) .. "," .. extra .. "}]",
  }
end

local function italic_block(base, face_cmap)
  local lines = {
    "\\setmathfont{" .. base .. "~Italic}[range=it/{latin,Latin,greek,Greek}]",
    "\\setmathfont{" .. base .. "~Bold~Italic}[range=bfup/{latin,Latin,greek,Greek}]",
  }
  local miss = {}
  for _, cp in ipairs({0x03F0, 0x03F4}) do
    if not face_cmap[cp] then
      miss[#miss + 1] = hex4(cp)
    end
  end
  if #miss > 0 then
    lines[#lines + 1] = "\\setmathfont{TeX~Gyre~Termes~Math}[range={" .. table.concat(miss, ",") .. "}]"
  end
  lines[#lines + 1] = "\\setmathfont{TeX~Gyre~Termes~Math}[range={\"1D6A8-\"1D7C9}]"
  return lines
end

local tgm = cmap_set(assert(kpse.find_file("texgyretermes-math.otf", "opentype fonts")))
local tgm_extra = clauses(function(s, l)
  return exists(s, l, tgm)
end)
local l_tgm = slot_list(tgm, MATH_FONT_SKIP)
local common = {
  "\\setmathfont{TeX~Gyre~Termes~Math}[range={" .. merged_ranges(l_tgm) .. "," .. tgm_extra .. "}]",
}
local wide_classes = {accentwide = true, botaccentwide = true}
for _, accent in ipairs(wide_accents) do
  if not tgm[accent.cp] then
    wide_classes[accent.class] = false
  end
end
local wide_commands = {}
for _, class in ipairs({"accentwide", "botaccentwide"}) do
  if wide_classes[class] then
    wide_commands[#wide_commands + 1] = "\\math" .. class
  end
end
if #wide_commands > 0 then
  common[#common + 1] = "\\setmathfont{TeX~Gyre~Termes~Math}[range={" .. table.concat(wide_commands, ",") .. "}]"
end

local supplement = cmap_set("times-math-integrals.otf")
local integral_slots = {}
for _, cp in ipairs(integrals) do
  if not tgm[cp] and supplement[cp] then
    integral_slots[#integral_slots + 1] = cp
  end
end
local integral_block = {}
if #integral_slots > 0 then
  integral_block = {
    "\\setmathfont{times-math-integrals.otf}[range={" .. merged_ranges(integral_slots) .. "}]",
  }
end

local tgt = find_tgt()
local tgt_cmol = cmap_set(tgt[1])
local tgt_cmi = cmap_set(tgt[2])
local tgt_base = base_block("TeX~Gyre~Termes", tgt_cmol)
local tgt_ital = italic_block("TeX~Gyre~Termes", tgt_cmi)

local tnr = find_tnr()
local tnr_base, tnr_ital
if tnr then
  local cmol = cmap_set(tnr[1])
  local cmi = cmap_set(tnr[2])
  tnr_base = base_block("Times~New~Roman", cmol)
  tnr_ital = italic_block("Times~New~Roman", cmi)
else
  texio.write_nl("notice: Times New Roman not found; tnr blocks left unchanged")
end

local function report(label, cmap)
  local n = 0
  for _ in pairs(cmap) do
    n = n + 1
  end
  texio.write_nl(("font %s: cmap=%d"):format(label, n))
end
report("TGM", tgm)
report("TGT", tgt_cmol)

local path = "times-math.dtx"
local f = assert(io.open(path, "r"), "Cannot find times-math.dtx; run this script from the project root")
local body = f:read("*a")
f:close()

local function escape_pattern(s)
  return (s:gsub("[%%%^%$%(%)%.%[%]%*%+%-%?]", "%%%0"))
end

local function replace_block(tag, content)
  if content == nil then
    return
  end
  local open_pat = "%=== gen:" .. tag .. " ==="
  local close_pat = "%--- gen:" .. tag .. " ---"
  local pat = "(" .. escape_pattern(open_pat) .. ")(.-\n)(%s*" .. escape_pattern(close_pat) .. ")"
  local new, n = body:gsub(pat, "%1\n" .. content:gsub("%%", "%%%%") .. "\n%3")
  assert(n == 1, "Missing or duplicate data marker: " .. tag)
  body = new
end

replace_block("common", table.concat(common, "\n    "))
replace_block("integrals", table.concat(integral_block, "\n    "))
replace_block("tnr", tnr_base and table.concat(tnr_base, "\n    ") or nil)
replace_block("tgt", table.concat(tgt_base, "\n    "))
replace_block("tnr-italic", tnr_ital and table.concat(tnr_ital, "\n    ") or nil)
replace_block("tgt-italic", table.concat(tgt_ital, "\n    "))

local out = assert(io.open(path, "w"))
out:write(body)
out:close()
texio.write_nl("updated " .. path)
