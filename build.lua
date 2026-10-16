module = "times-math"

local status = os.execute("python3 test/stage.py")
assert(status == 0, "Failed to stage release sources")
sourcefiledir = "build/release-source"
docfiledir = sourcefiledir
textfiledir = sourcefiledir

sourcefiles = {"times-math.dtx", "times-math.ins", "times-math-integrals.otf", "build.lua"}
installfiles = {"times-math.sty", "times-math-integrals.otf"}
tdslocations = {"fonts/opentype/public/times-math/*.otf"}
unpackfiles = {"times-math.ins"}
unpackexe = "xetex"
unpackopts = "-interaction=nonstopmode -halt-on-error"

typesetfiles = {"times-math.tex", "times-math-cn.tex", "times-math-glyphs.tex"}
typesetsourcefiles = typesetfiles
docfiles = {"times-math-doc.tex", "times-math.ltx"}
typesetdir = "build/typeset"
typesetexe = "lualatex"
typesetopts = "-interaction=nonstopmode -halt-on-error -no-shell-escape -recorder"
typesetruns = 3
typesetwarnings = true

textfiles = {"README.md", "LICENSE", "GUST-FONT-LICENSE.txt", "MANIFEST-times-math-integrals.txt", "Makefile", "dev", "test"}
ctanreadme = "README.md"
excludefiles = {"*~"}
binaryfiles = {"*.pdf", "*.zip", "*.otf"}
packtdszip = true

local file = assert(io.open("times-math.dtx", "r"))
local source = file:read("*a")
file:close()
local date, version = source:match("\\ProvidesExplPackage{times%-math}{([^}]+)}{([^}]+)}")
assert(date and version, "Missing times-math package version")

uploadconfig = {
  pkg = "times-math",
  author = "Junhao Wu",
  uploader = "Junhao Wu",
  email = "andrew.junhao.wu@gmail.com",
  summary = "Times New Roman glyphs for Unicode mathematics",
  license = {"lppl1.3c", "gfl"},
  version = "v" .. version .. " " .. date,
  ctanPath = "/macros/latex/contrib/times-math",
  description = [[
    times-math uses Times New Roman glyphs in mathematics, with TeX Gyre
    Termes Math and XITS Math supplying mathematical layout and additional
    symbols. A bundled Termes-derived OpenType math font supplies additional
    integral operators. It supports LuaLaTeX and XeLaTeX through unicode-math.
  ]],
  update = false,
}
