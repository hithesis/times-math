import argparse
from datetime import datetime, timezone
from functools import lru_cache
import math
from pathlib import Path
import subprocess
import tempfile

import pathops
from fontTools.fontBuilder import FontBuilder
from fontTools.misc.bezierTools import solveCubic
from fontTools.otlLib.builder import buildMathTable
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.t2CharStringPen import T2CharStringPen
from fontTools.ttLib import TTFont, newTable
from fontTools.ttLib.tables import otTables

ROOT = Path(__file__).resolve().parents[1]
OPERATORS = {
    0x2A0B: 'sumint', 0x2A0D: 'intbar', 0x2A0E: 'intBar', 0x2A0F: 'fint',
    0x2A10: 'cirfnint', 0x2A12: 'rppolint', 0x2A13: 'scpolint', 0x2A14: 'npolint',
    0x2A15: 'pointint', 0x2A16: 'sqint', 0x2A17: 'intlarhk', 0x2A18: 'intx',
    0x2A19: 'intcap', 0x2A1A: 'intcup', 0x2A1B: 'upint', 0x2A1C: 'lowint',
}
PS_NAME = 'TimesMathIntegrals-Regular'
FAMILY = 'Times Math Integrals'


def rectangle(left, bottom, right, top):
    path = pathops.Path()
    path.moveTo(left, bottom)
    path.lineTo(right, bottom)
    path.lineTo(right, top)
    path.lineTo(left, top)
    path.close()
    return path


def union(*paths):
    result = pathops.Path()
    for path in paths:
        result = pathops.op(result, path, pathops.PathOp.UNION)
    return result


def intersection(path, clip):
    return pathops.op(path, clip, pathops.PathOp.INTERSECTION)


def crossings(path, y):
    recording = RecordingPen()
    path.draw(recording)
    start = current = None
    values = []

    def line(end):
        if current[1] != end[1]:
            t = (y - current[1]) / (end[1] - current[1])
            if 0 <= t < 1:
                values.append(current[0] + t * (end[0] - current[0]))

    for command, points in recording.value:
        if command == 'moveTo':
            start = current = points[0]
        elif command == 'lineTo':
            line(points[0])
            current = points[0]
        elif command == 'curveTo':
            p0, p1, p2, p3 = current, *points
            a = -p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]
            b = 3 * p0[1] - 6 * p1[1] + 3 * p2[1]
            c = -3 * p0[1] + 3 * p1[1]
            for t in solveCubic(a, b, c, p0[1] - y):
                if 0 <= t < 1:
                    values.append((1 - t) ** 3 * p0[0] + 3 * (1 - t) ** 2 * t * p1[0]
                                  + 3 * (1 - t) * t ** 2 * p2[0] + t ** 3 * p3[0])
            current = p3
        elif command in ('closePath', 'endPath'):
            if current != start:
                line(start)
            current = start
        else:
            raise ValueError(f'Unsupported outline command: {command}')
    return sorted(set(round(value, 6) for value in values))


class Termes:
    def __init__(self, path):
        self.font = TTFont(path)
        if self.font['name'].getDebugName(1) != 'TeX Gyre Termes Math':
            raise ValueError('The source must be TeX Gyre Termes Math')
        self.glyphs = self.font.getGlyphSet()
        self.cmap = self.font.getBestCmap()
        self.math = self.font['MATH'].table
        self.axis = self.math.MathConstants.AxisHeight.Value
        self.rule = self.math.MathConstants.FractionRuleThickness.Value
        self.integral = self.construction(0x222B)
        self.contour = self.construction(0x222E)

    def construction(self, cp):
        variants = self.math.MathVariants
        index = variants.VertGlyphCoverage.glyphs.index(self.cmap[cp])
        return variants.VertGlyphConstruction[index]

    @lru_cache(None)
    def path(self, name):
        result = pathops.Path()
        self.glyphs[name].draw(result.getPen())
        return pathops.simplify(result)

    def character(self, cp):
        return self.path(self.cmap[cp])

    def centered(self, cp, x, y, scale=1):
        path = self.character(cp)
        left, bottom, right, top = path.bounds
        return path.transform(scale, 0, 0, scale,
                              x - scale * (left + right) / 2,
                              y - scale * (bottom + top) / 2)

    def ring(self, cp, x, y, diameter, stroke):
        contours = sorted(self.character(cp).contours, key=lambda path: abs(path.area), reverse=True)
        outer, inner = contours

        def fit(path, size):
            left, bottom, right, top = path.bounds
            sx, sy = size / (right - left), size / (top - bottom)
            return path.transform(sx, 0, 0, sy,
                                  x - sx * (left + right) / 2,
                                  y - sy * (bottom + top) / 2)

        return pathops.op(fit(outer, diameter), fit(inner, diameter - 2 * stroke),
                          pathops.PathOp.DIFFERENCE)

    def bar(self, x, y, length, stroke, angle=0):
        path = self.character(0x2212)
        left, bottom, right, top = path.bounds
        sx, sy = length / (right - left), stroke / (top - bottom)
        path = path.transform(sx, 0, 0, sy,
                              -sx * (left + right) / 2, -sy * (bottom + top) / 2)
        c, s = math.cos(angle), math.sin(angle)
        return path.transform(c, s, -s, c, x, y)

    def profile(self, index):
        integral = self.path(self.integral.MathGlyphVariantRecord[index].VariantGlyph)
        contour = self.path(self.contour.MathGlyphVariantRecord[index].VariantGlyph)
        line = crossings(integral, self.axis + .125)
        ring = crossings(contour, self.axis + .125)
        assert len(line) == 2 and len(ring) >= 4
        center = (line[0] + line[-1]) / 2
        diameter = ring[-1] - ring[0]
        stroke = min(ring[1] - ring[0], ring[-1] - ring[-2])
        return integral, center, diameter, stroke

    def pole(self, kind, stem, x, y, diameter, stroke):
        radius = diameter / 2
        circle_x = x + .65 * radius if kind == 'npolint' else x
        marker = self.ring(0x25A1 if kind == 'rppolint' else 0x25CB,
                           circle_x, y, diameter, stroke)
        contours = sorted(marker.contours, key=lambda path: abs(path.area), reverse=True)
        native = pathops.op(stem, contours[1], pathops.PathOp.DIFFERENCE)
        swapped = marker.transform(0, 1, 1, 0, 0, 0)
        join_x = crossings(stem, y)[0] + 1
        for _ in range(3):
            ends = crossings(swapped, join_x)
            join_x = max(crossings(stem, ends[0])[0], crossings(stem, ends[-1])[0]) + 1
        if kind == 'npolint':
            ends = crossings(swapped, join_x)
            native = pathops.op(native, rectangle(-10000, ends[1], 10000, ends[-2]),
                                pathops.PathOp.DIFFERENCE)
        marker = intersection(marker, rectangle(join_x, -10000, 10000, 10000))
        dot = self.character(0x22C5)
        dot_scale = diameter * .22 / (dot.bounds[2] - dot.bounds[0])
        return union(native, marker, self.centered(0x22C5, circle_x, y, dot_scale))

    def compose(self, kind, stem, x, y, diameter, stroke):
        scale = stroke / self.rule
        radius = diameter / 2
        dot = lambda center: self.centered(0x22C5, center, y, scale)

        def break_stem(lower, upper):
            return pathops.op(stem, rectangle(-10000, lower, 10000, upper), pathops.PathOp.DIFFERENCE)

        if kind == 'sumint':
            sigma = self.character(0x2211)
            height = sigma.bounds[3] - sigma.bounds[1]
            target = min(diameter * 1.3, (stem.bounds[3] - stem.bounds[1]) * .7)
            return union(stem, self.centered(0x2211, x, y, target / height))
        if kind == 'intbar':
            return union(stem, self.bar(x, y, diameter * .9, stroke))
        if kind == 'intBar':
            return union(stem, self.centered(0x3D, x, y, scale))
        if kind == 'fint':
            return union(stem, self.bar(x, y, diameter * 1.05, stroke, math.pi / 4))
        if kind in ('upint', 'lowint'):
            edge = stem.bounds[3] if kind == 'upint' else stem.bounds[1]
            direction = 1 if kind == 'upint' else -1
            return union(stem, self.bar(x, edge + direction * stroke * 1.5, diameter * .9, stroke))
        if kind == 'intlarhk':
            return union(stem, self.centered(0x21A9, x, y, scale))
        if kind == 'intx':
            return union(stem, self.centered(0xD7, x, y, scale))
        if kind in ('intcap', 'intcup'):
            return union(stem, self.centered(0x2229 if kind == 'intcap' else 0x222A, x, y, scale))
        if kind in ('rppolint', 'scpolint', 'npolint'):
            return self.pole(kind, stem, x, y, diameter, stroke)
        if kind == 'sqint':
            return union(stem, self.ring(0x25A1, x, y, diameter, stroke))
        circle = self.ring(0x25CB, x, y, diameter, stroke)
        if kind == 'cirfnint':
            circle = intersection(circle, rectangle(-10000, -10000, x + .6 * radius, 10000))
            return union(stem, circle)
        if kind == 'pointint':
            join = radius - stroke / 2
            return union(break_stem(y - join, y + join), circle, dot(x))
        raise ValueError(kind)


def math_script(font):
    table = newTable('GSUB')
    table.table = otTables.GSUB()
    table.table.Version = 0x00010000
    table.table.ScriptList = otTables.ScriptList()
    table.table.ScriptList.ScriptRecord = []
    for tag in ('DFLT', 'math'):
        record = otTables.ScriptRecord()
        record.ScriptTag = tag
        record.Script = otTables.Script()
        record.Script.DefaultLangSys = otTables.LangSys()
        record.Script.DefaultLangSys.LookupOrder = None
        record.Script.DefaultLangSys.ReqFeatureIndex = 0xFFFF
        record.Script.DefaultLangSys.FeatureIndex = []
        record.Script.LangSysRecord = []
        table.table.ScriptList.ScriptRecord.append(record)
    table.table.FeatureList = otTables.FeatureList()
    table.table.FeatureList.FeatureRecord = []
    table.table.LookupList = otTables.LookupList()
    table.table.LookupList.Lookup = []
    font['GSUB'] = table


def build(source, output):
    termes = Termes(source)
    outlines = {'.notdef': termes.path('.notdef'), 'space': pathops.Path()}
    metrics = {'.notdef': termes.font['hmtx']['.notdef'], 'space': (250, 0)}
    cmap = {0x20: 'space'}
    vertical, attachments = {}, {}

    def add(name, path, advance=None):
        path = pathops.simplify(path, keep_starting_points=False)
        left, _, right, _ = path.bounds
        shift = 80 - left
        outlines[name] = path.transform(1, 0, 0, 1, shift, 0)
        metrics[name] = (math.ceil(right + shift + 80) if advance is None else advance, 80)
        return shift

    for cp, kind in OPERATORS.items():
        base = f'uni{cp:04X}'
        cmap[cp] = base
        vertical[base] = []
        for index, record in enumerate(termes.integral.MathGlyphVariantRecord):
            stem, center, diameter, stroke = termes.profile(index)
            name = base if index == 0 else f'{base}.v{index}'
            shape = termes.compose(kind, stem, center, termes.axis, diameter, stroke)
            shift = add(name, shape)
            attachments[name] = round(center + shift)
            added_height = round((shape.bounds[3] - shape.bounds[1])
                                 - (stem.bounds[3] - stem.bounds[1]))
            vertical[base].append((name, record.AdvanceMeasurement + added_height))
    builder = FontBuilder(termes.font['head'].unitsPerEm, isTTF=False)
    order = list(outlines)
    builder.setupGlyphOrder(order)
    builder.setupCharacterMap(cmap)
    charstrings = {}
    for name, path in outlines.items():
        pen = T2CharStringPen(metrics[name][0], None)
        path.draw(pen)
        charstrings[name] = pen.getCharString()
    copyright = termes.font['name'].getDebugName(0)
    notice = copyright + ' Derived font and additional glyphs Copyright 2026 Junhao Wu.'
    builder.setupCFF(PS_NAME, {'FullName': FAMILY + ' Regular', 'FamilyName': FAMILY,
                             'Weight': 'Regular', 'version': '0.1a', 'Notice': notice},
                     charstrings, {})
    builder.setupHorizontalMetrics(metrics)
    builder.setupHorizontalHeader(ascent=termes.font['hhea'].ascent,
                                  descent=termes.font['hhea'].descent,
                                  lineGap=termes.font['hhea'].lineGap)
    builder.setupNameTable({'familyName': FAMILY, 'styleName': 'Regular',
                           'uniqueFontIdentifier': 'TimesMathIntegrals-0.1a-JunhaoWu',
                           'fullName': FAMILY + ' Regular', 'psName': PS_NAME,
                           'version': 'Version 0.1a', 'copyright': notice,
                           'manufacturer': 'Junhao Wu; derived from TeX Gyre Termes Math',
                           'description': 'Supplementary Termes-derived integral operators for times-math.'})
    bounds = [path.bounds for name, path in outlines.items() if name != 'space']
    original_os2 = termes.font['OS/2']
    builder.setupOS2(sTypoAscender=original_os2.sTypoAscender,
                     sTypoDescender=original_os2.sTypoDescender,
                     sTypoLineGap=original_os2.sTypoLineGap,
                     usWinAscent=math.ceil(max(bound[3] for bound in bounds)),
                     usWinDescent=math.ceil(-min(bound[1] for bound in bounds)),
                     usWeightClass=400, usWidthClass=5, fsType=0, achVendID='TMTH',
                     sxHeight=original_os2.sxHeight, sCapHeight=original_os2.sCapHeight)
    builder.setupPost()
    font = builder.font
    license_text = (ROOT / 'GUST-FONT-LICENSE.txt').read_text(encoding='utf-8')
    font['name'].setName(license_text, 13, 3, 1, 0x409)
    font['name'].setName('https://tug.org/fonts/licenses/GUST-FONT-LICENSE.txt', 14, 3, 1, 0x409)
    constants = {}
    for converter in termes.math.MathConstants.getConverters():
        value = getattr(termes.math.MathConstants, converter.name)
        constants[converter.name] = value.Value if hasattr(value, 'Value') else value
    buildMathTable(font, constants=constants, italicsCorrections={name: 0 for name in order},
                   topAccentAttachments=attachments, extendedShapes=set(attachments),
                   minConnectorOverlap=termes.math.MathVariants.MinConnectorOverlap,
                   vertGlyphVariants=vertical)
    math_script(font)
    timestamp = int(datetime(2026, 10, 17, tzinfo=timezone.utc).timestamp()) + 2082844800
    font['head'].created = font['head'].modified = timestamp
    font['head'].fontRevision = 0.1
    font.recalcTimestamp = False
    font.save(output, reorderTables=True)
    checked = TTFont(output)
    assert checked.sfntVersion == 'OTTO' and 'MATH' in checked
    assert set(checked.getBestCmap()) == set(OPERATORS) | {0x20}
    print(f'{output.name}: {len(OPERATORS)} operators, {len(order)} glyphs, {output.stat().st_size} bytes')


def check(source, output):
    font = TTFont(output)
    termes = Termes(source)
    glyphs = font.getGlyphSet()
    assert font['name'].getDebugName(1) == FAMILY
    assert font['name'].getDebugName(6) == PS_NAME
    assert 'GUST Font License' in font['name'].getDebugName(13)
    assert set(font.getBestCmap()) == set(OPERATORS) | {0x20}
    variants = font['MATH'].table.MathVariants
    comparisons = 0
    for cp in OPERATORS:
        base = font.getBestCmap()[cp]
        record = variants.VertGlyphConstruction[variants.VertGlyphCoverage.glyphs.index(base)]
        assert len(record.MathGlyphVariantRecord) == 7
        for index, variant in enumerate(record.MathGlyphVariantRecord):
            shape = pathops.Path()
            glyphs[variant.VariantGlyph].draw(shape.getPen())
            left, _, right, _ = shape.bounds
            advance, bearing = font['hmtx'][variant.VariantGlyph]
            assert bearing == 80 and left >= 79 and advance - right >= 79
            original, _, _, _ = termes.profile(index)
            height = original.bounds[3] - original.bounds[1]
            added_height = round((shape.bounds[3] - shape.bounds[1]) - height)
            assert variant.AdvanceMeasurement == termes.integral.MathGlyphVariantRecord[index].AdvanceMeasurement + added_height
            offsets = []
            for direction in (-1, 1):
                y = termes.axis + direction * height * .44
                expected, actual = crossings(original, y), crossings(shape, y)
                assert len(expected) == len(actual) and expected, (variant.VariantGlyph, y, expected, actual)
                for expected_left, expected_right, actual_left, actual_right in zip(
                        expected[::2], expected[1::2], actual[::2], actual[1::2]):
                    assert abs((actual_right - actual_left) - (expected_right - expected_left)) <= 1.5, variant.VariantGlyph
                offsets.append(actual[0] - expected[0])
                comparisons += 1
            assert abs(offsets[0] - offsets[1]) <= 1.5, variant.VariantGlyph
    with tempfile.TemporaryDirectory(prefix='font-rebuild-', dir=ROOT / 'build') as directory:
        rebuilt = Path(directory) / output.name
        build(source, rebuilt)
        assert rebuilt.read_bytes() == output.read_bytes(), 'Font is not reproducible; run make font'
    print(f'Font checks: 16 Unicode operators, 112 variants, {comparisons} Termes outline comparisons, reproducible binary')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=Path)
    parser.add_argument('--output', type=Path, default=ROOT / 'times-math-integrals.otf')
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    source = args.source or Path(subprocess.check_output(
        ['kpsewhich', 'texgyretermes-math.otf'], text=True).strip())
    if args.check:
        check(source, args.output)
    else:
        build(source, args.output)


if __name__ == '__main__':
    main()
