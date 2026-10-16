PACKAGE = times-math
LATEXMK = latexmk -lualatex -interaction=nonstopmode -halt-on-error -no-shell-escape -recorder -outdir=build/doc
CACHE_ENV = TEXMFVAR="$(CURDIR)/build/texmf-var" TEXMFCACHE="$(CURDIR)/build/texmf-var"
DOC_CACHE = build/texmf-var/.ready
MANUAL_SOURCES = $(PACKAGE).ltx $(PACKAGE)-doc.tex
FONT = times-math-integrals.otf
FONT_PYTHON = build/font-tools/bin/python
FONT_ENV = build/font-tools/.ready

.PHONY: all sty font check-font doc doc-en doc-zh glyphs check check-doc data ctan clean
all: doc

sty: build/unpacked/$(PACKAGE).sty
build/unpacked/$(PACKAGE).sty: $(PACKAGE).dtx $(PACKAGE).ins $(FONT) build.lua
	l3build unpack

$(FONT_ENV): dev/requirements.txt
	python3 -m venv build/font-tools
	$(FONT_PYTHON) -m pip install -r dev/requirements.txt
	touch $(FONT_ENV)

font: $(FONT_ENV)
	$(FONT_PYTHON) dev/build-integrals.py

check-font: $(FONT_ENV)
	$(FONT_PYTHON) dev/build-integrals.py --check

$(DOC_CACHE):
	mkdir -p build/texmf-var
	$(CACHE_ENV) luaotfload-tool --update --quiet
	touch $(DOC_CACHE)

doc: doc-en doc-zh
doc-en: build/doc/$(PACKAGE).pdf
doc-zh: build/doc/$(PACKAGE)-cn.pdf
glyphs: build/doc/$(PACKAGE)-glyphs.pdf

build/doc/$(PACKAGE).pdf: $(PACKAGE).tex $(MANUAL_SOURCES) build/unpacked/$(PACKAGE).sty $(FONT) Makefile $(DOC_CACHE)
	$(CACHE_ENV) TEXINPUTS="./:$(CURDIR)/build/unpacked//:" $(LATEXMK) $(if $(filter $(FONT),$?),-g,) $(PACKAGE).tex
build/doc/$(PACKAGE)-cn.pdf: $(PACKAGE)-cn.tex $(MANUAL_SOURCES) build/unpacked/$(PACKAGE).sty $(FONT) Makefile $(DOC_CACHE)
	$(CACHE_ENV) TEXINPUTS="./:$(CURDIR)/build/unpacked//:" $(LATEXMK) $(if $(filter $(FONT),$?),-g,) $(PACKAGE)-cn.tex
build/doc/$(PACKAGE)-glyphs.pdf: $(PACKAGE)-glyphs.tex build/unpacked/$(PACKAGE).sty $(FONT) Makefile $(DOC_CACHE)
	$(CACHE_ENV) TEXINPUTS="./:$(CURDIR)/build/unpacked//:" $(LATEXMK) $(if $(filter $(FONT),$?),-g,) $(PACKAGE)-glyphs.tex

check: sty
	texlua test/check-font.lua
	python3 test/run.py
	python3 test/check-options.py

check-doc: doc glyphs
	python3 test/check-doc.py

data:
	texlua dev/gen-ranges.lua
	texlua dev/gen-coverage.lua

ctan: $(DOC_CACHE)
	$(CACHE_ENV) l3build ctan
	python3 test/check-font-install.py

clean:
	l3build clean
	python3 test/clean.py
