kpse.set_program_name("lualatex")

local function load(path)
  local handle = assert(fontloader.open(path), "Cannot open " .. path)
  local data = fontloader.to_table(handle)
  fontloader.close(handle)
  local names, slots = {}, {}
  for _, glyph in pairs(data.glyphs) do
    names[glyph.name] = glyph
    if glyph.unicode and glyph.unicode >= 0 then
      slots[glyph.unicode] = glyph
    end
  end
  return data, names, slots
end

local data, names, slots = load("times-math-integrals.otf")
local original = load(assert(kpse.find_file("texgyretermes-math.otf", "opentype fonts")))
assert(data.fontname == "TimesMathIntegrals-Regular")
assert(data.units_per_em == original.units_per_em)
assert(data.math.AxisHeight == original.math.AxisHeight)
local count, variants = 0, 0
for cp, glyph in pairs(slots) do
  if cp ~= 0x20 then
    assert(cp == 0x2A0B or (cp >= 0x2A0D and cp <= 0x2A10) or (cp >= 0x2A12 and cp <= 0x2A1C))
    local size = 0
    for name in glyph.vert_variants.variants:gmatch("%S+") do
      local variant = assert(names[name])
      assert(variant.boundingbox[1] >= 79)
      assert(variant.width - variant.boundingbox[3] >= 79)
      assert((variant.italic_correction or 0) == 0)
      size = size + 1
      variants = variants + 1
    end
    assert(size == 7, glyph.name)
    count = count + 1
  end
end
assert(count == 16 and variants == 112)
print("OTF: 16 Unicode operators, 112 native MATH size variants, valid ink bounds and sidebearings")
