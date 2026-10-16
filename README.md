# Times Math

v0.1a · 2026-10-17 · LuaLaTeX / XeLaTeX

[English](#english) | [中文](#中文)

## English

`times-math` uses Times New Roman letters, digits and suitable symbols in
mathematics. XITS Math, TeX Gyre Termes Math and the bundled Times Math Integrals
font provide mathematical layout and the remaining glyphs. The package is based
on `unicode-math` and supports LuaLaTeX and XeLaTeX.

### Installation

Install Times New Roman separately. XITS Math, TeX Gyre Termes Math and the
TeX Gyre Termes text fonts are available in TeX Live.

Extract the package from the sources:

```sh
xetex times-math.ins
```

Place the extracted `times-math.sty` and the bundled `times-math-integrals.otf`
beside your document. The supplementary font is ready to use; normal typesetting
does not require Python or font-building tools.

Alternatively, run `l3build install` from the project root to install both in
your user TEXMF tree. For manual installation, use these locations:

```text
tex/latex/times-math/times-math.sty
fonts/opentype/public/times-math/times-math-integrals.otf
```

### Usage

```latex
\documentclass{article}
\usepackage{times-math}
\begin{document}
$E=mc^2$, $\alpha+\beta=\gamma$, $\mathbb{R}$.
\[
  \int_0^1 f(x)\,\mathrm{d}x,\qquad
  \fint_0^1 f(x)\,\mathrm{d}x.
\]
\end{document}
```

The package sets math fonts only. To use Times New Roman for body text as well,
add this to the preamble:

```latex
\setmainfont{Times New Roman}
```

### Options

| Option | Default | Purpose |
| --- | --- | --- |
| `text-font` | `Times New Roman` | Select the text-glyph configuration |
| `math-font` | `XITS Math` | Supply math parameters and final glyph fallback |
| `math-style`, `bold-style` | `unicode-math` defaults | Forward math alphabet styles to `unicode-math` |

`text-font` accepts `Times New Roman`, `TeX Gyre Termes` and `none`.
Matching ignores ordinary spaces and case. Unknown or empty values stop
compilation with an error. To select the TeX Gyre Termes text glyphs explicitly:

```latex
\usepackage[text-font=TeX Gyre Termes]{times-math}
```

If Times New Roman is unavailable, the package warns and skips the text-font
layer, using glyphs from the math fonts. `text-font=none` disables that layer
without a warning. The TeX Gyre Termes text layer is not enabled automatically,
and arbitrary text fonts are not supported.

`math-font` accepts the name or filename of a font with an OpenType MATH table.
Changing the base font retains Termes Math and the integral supplement.
See the manuals for further font and style examples.

### Package compatibility

`amsmath` and `unicode-math` are loaded automatically. For theorem environments,
extended equation commands and units, use this loading order:

```latex
\usepackage{mathtools,amsthm,siunitx}
\usepackage{times-math}
```

Do not load other math-font setups such as `newtxmath` or `txfonts`, or the
legacy packages `amssymb`, `amsfonts`, `latexsym`, `mathrsfs`, `eucal` and `bm`.
They may override glyphs, redefine commands or cause errors depending on loading
order.

`\mathrm`, `\mathbf`, `\mathit`, `\mathsf`, `\mathtt` and `\boldsymbol` are
redirected to math alphabet commands. Use `\text` for ordinary text in formulas.
Some legacy command interfaces are provided: `\bm` selects bold mathematical
letters rather than implementing arbitrary formula boldening, and `\mathbbm`
uses the current math font's blackboard glyphs. The manuals describe these
interfaces in full.

### Integral supplement

`times-math-integrals.otf` supplies sixteen additional integral operators,
including `\fint`, `\intbar`, `\pointint`, `\rppolint`, `\scpolint`, `\npolint`
and `\lowint`. They are composed from Termes integral outlines and symbol
components, with seven native MATH size variants per operator. The commands
are available after loading `times-math`.

The font can also be used independently in a `unicode-math` document:

```latex
\usepackage{unicode-math}
\setmathfont{TeX Gyre Termes Math}
\setmathfont{times-math-integrals.otf}[
  range={"2A0B,"2A0D-"2A10,"2A12-"2A1C}]
```

### Documentation

The distribution includes the English manual `times-math.pdf`, the Chinese
manual `times-math-cn.pdf` and the glyph reference `times-math-glyphs.pdf`.
Download the `documents` artifact from a successful
[GitHub Actions run](https://github.com/hithesis/times-math/actions/workflows/ci.yml).
The `release-archives` artifact contains the CTAN and TDS archives.

In the glyph reference, columns X, G, T and t show raw glyphs from XITS Math,
TeX Gyre Termes Math, Times New Roman and TeX Gyre Termes, respectively.
Column N shows actual package output with `literal` math styles. Dotted circles
(U+25CC) mark accent bases; the math-font columns use three circles for wide
accent examples.

### Building and maintenance

Building requires TeX Live with `l3build` and `latexmk`, Python 3 and GNU Make.
The integral raster checks also require MuPDF's `mutool`.

```sh
make sty
make doc
make glyphs
make check
make check-doc
make ctan
make clean
```

The extracted package goes to `build/unpacked/`, PDFs to `build/doc/`, and
test outputs to `test/output/`. Documentation and release builds keep their
font caches in `build/texmf-var/`. `make ctan` creates `times-math-ctan.zip`
and `times-math.tds.zip` in the project root. It does not upload to CTAN.

For supplementary-font or character-range maintenance, run:

```sh
make font
make check-font
make data
make sty
```

The font targets install the tools listed in `dev/requirements.txt` into
`build/font-tools/`. The font manifest records the source font version and
checksum. `make data` updates the ranges in `times-math.dtx` and the fixture
`test/test-coverage.tex`; `TIMES_MATH_TNR` can specify the Times New Roman
regular-face file used for range generation.

### Author and licence

Author and maintainer: Junhao Wu (吴俊豪), <andrew.junhao.wu@gmail.com>.

The sources use LPPL 1.3c or later; see [LICENSE](LICENSE). The supplementary
font uses the [GUST Font License 1.0](GUST-FONT-LICENSE.txt); its
[manifest](MANIFEST-times-math-integrals.txt) records the original authors and
source. Times New Roman, XITS Math and the original TeX Gyre Termes Math are
not bundled. The glyph-reference layout follows `unicode-math`'s
`unimath-symbols` and `euler-math`'s `unimath-euler.ltx`.

## 中文

`times-math` 将 Times New Roman 的字母、数字和适用符号用于数学排版。
数学排版参数与其余字形由 XITS Math、TeX Gyre Termes Math 和随包附带的
Times Math Integrals 提供。宏包基于 `unicode-math`，支持 LuaLaTeX 和 XeLaTeX。

### 安装

Times New Roman 需要自行安装。XITS Math、TeX Gyre Termes Math 和
TeX Gyre Termes 文字字体随 TeX Live 提供。

从源码提取宏包：

```sh
xetex times-math.ins
```

将生成的 `times-math.sty` 与附带的 `times-math-integrals.otf` 一起放到文档目录。
补充字体已生成，正常使用不需要 Python 或字体构建工具。

也可在项目根目录运行 `l3build install`，安装到用户 TEXMF 树。
手动安装时，文件位置为：

```text
tex/latex/times-math/times-math.sty
fonts/opentype/public/times-math/times-math-integrals.otf
```

### 使用

```latex
\documentclass{article}
\usepackage{times-math}
\begin{document}
$E=mc^2$, $\alpha+\beta=\gamma$, $\mathbb{R}$.
\[
  \int_0^1 f(x)\,\mathrm{d}x,\qquad
  \fint_0^1 f(x)\,\mathrm{d}x.
\]
\end{document}
```

宏包只设置数学字体。正文也需要 Times New Roman 时，在导言区另加：

```latex
\setmainfont{Times New Roman}
```

### 选项

| 选项 | 默认值 | 说明 |
| --- | --- | --- |
| `text-font` | `Times New Roman` | 选择文字字形配置 |
| `math-font` | `XITS Math` | 提供数学参数和最后一级字形回退 |
| `math-style`、`bold-style` | `unicode-math` 默认值 | 传给 `unicode-math` 的数学字母样式 |

`text-font` 接受 `Times New Roman`、`TeX Gyre Termes` 和 `none`。
匹配时忽略普通空格和大小写；未知值或空值会报错并中止编译。
例如，显式选用 TeX Gyre Termes 文字字形：

```latex
\usepackage[text-font=TeX Gyre Termes]{times-math}
```

Times New Roman 缺失时，宏包会警告并跳过文字字体层，使用数学字体提供的字形。
`text-font=none` 主动关闭该层且不警告。TeX Gyre Termes 文字字体不会自动启用，
也不支持任意指定其他文字字体。

`math-font` 接受含 OpenType MATH 表的字体名或文件名。
替换基底字体后，Termes Math 与补充积分号字体仍会加载。
其他字体配置及样式示例见手册。

### 宏包兼容性

`amsmath` 与 `unicode-math` 会自动加载。需要定理、扩展公式命令或单位排版时，
可使用以下加载顺序：

```latex
\usepackage{mathtools,amsthm,siunitx}
\usepackage{times-math}
```

不要再加载 `newtxmath`、`txfonts` 等替换数学字体的宏包，或重复加载
`amssymb`、`amsfonts`、`latexsym`、`mathrsfs`、`eucal`、`bm`。
这些包可能覆盖字形、重定义命令，或因加载顺序而报错。

`\mathrm`、`\mathbf`、`\mathit`、`\mathsf`、`\mathtt`、`\boldsymbol`
默认重定向到数学字母命令，公式中的普通文字应使用 `\text`。
宏包提供部分旧命令接口；其中 `\bm` 用于粗体数学字母，不实现任意公式加粗，
`\mathbbm` 使用当前数学字体的黑板体字形。完整说明见手册。

### 补充积分号字体

`times-math-integrals.otf` 提供 16 个补充积分号，包括 `\fint`、`\intbar`、
`\pointint`、`\rppolint`、`\scpolint`、`\npolint` 和 `\lowint`。
字形由 Termes 的积分曲线与符号构件组合，每个符号有 7 档原生 MATH 尺寸变体。
加载 `times-math` 后即可使用。

这份字体也可在普通 `unicode-math` 文档中单独使用：

```latex
\usepackage{unicode-math}
\setmathfont{TeX Gyre Termes Math}
\setmathfont{times-math-integrals.otf}[
  range={"2A0B,"2A0D-"2A10,"2A12-"2A1C}]
```

### 文档

发行包包含英文手册 `times-math.pdf`、中文手册 `times-math-cn.pdf` 和
字形清单 `times-math-glyphs.pdf`。
可从 [GitHub Actions](https://github.com/hithesis/times-math/actions/workflows/ci.yml)
成功运行的 `documents` 附件下载；`release-archives` 附件包含 CTAN 和 TDS 包。

字形清单的 X、G、T、t 列分别显示 XITS Math、TeX Gyre Termes Math、
Times New Roman 和 TeX Gyre Termes 的原始字形，N 列显示宏包在 `literal`
数学样式下的实际输出。重音用虚线圆圈（U+25CC）标出基字位置，
数学字体列的宽重音示例使用三个圆圈。

### 构建与维护

需要 TeX Live（含 `l3build`、`latexmk`）、Python 3 和 GNU Make。
积分排版的像素检查还需要 MuPDF 的 `mutool`。

```sh
make sty
make doc
make glyphs
make check
make check-doc
make ctan
make clean
```

提取的宏包位于 `build/unpacked/`，PDF 位于 `build/doc/`，测试输出位于
`test/output/`。文档与发行包构建使用 `build/texmf-var/` 下的独立字体缓存。
`make ctan` 在项目根目录生成 `times-math-ctan.zip` 和 `times-math.tds.zip`，
不会向 CTAN 上传。

维护补充字体或字符区间时，使用：

```sh
make font
make check-font
make data
make sty
```

字体构建工具按 `dev/requirements.txt` 在 `build/font-tools/` 中安装。
源字体版本与校验值记录在字体清单中。
`make data` 更新 `times-math.dtx` 的字符区间和 `test/test-coverage.tex`；
`TIMES_MATH_TNR` 可指定生成区间时读取的 Times New Roman 正体文件。

### 作者与许可

作者与维护者：吴俊豪（Junhao Wu），<andrew.junhao.wu@gmail.com>。

源码使用 LPPL 1.3c 或更高版本，见 [LICENSE](LICENSE)。
补充字体使用 [GUST Font License 1.0](GUST-FONT-LICENSE.txt)，
原作者与字体来源见 [字体清单](MANIFEST-times-math-integrals.txt)。
Times New Roman、XITS Math 和原始 TeX Gyre Termes Math 不随包分发。
字形清单的版式参考 `unicode-math` 的 `unimath-symbols` 和
`euler-math` 的 `unimath-euler.ltx`。
