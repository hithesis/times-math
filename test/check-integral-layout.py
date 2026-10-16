import argparse
import json
from pathlib import Path
import re
import shutil
import statistics
import subprocess
import tempfile


def read_ppm(path):
    data = path.read_bytes()
    header = re.match(rb'P6\s+(\d+)\s+(\d+)\s+255\s', data)
    if header is None:
        raise ValueError(f'Invalid PPM header: {path}')
    width, height = map(int, header.groups())
    pixels = data[header.end():]
    if len(pixels) != width * height * 3:
        raise ValueError(f'Invalid PPM size: {path}')
    return width, pixels


def masks(pixels):
    blue, green, red = {}, {}, set()
    for index, (r, g, b) in enumerate(zip(pixels[0::3], pixels[1::3], pixels[2::3])):
        if b > r + 24 and b > g + 24:
            blue[index] = 1 - max(r, g) / 255
        elif g > r + 24 and g > b + 24:
            green[index] = 1 - max(r, b) / 255
        elif r > g + 24 and r > b + 24:
            red.add(index)
    return blue, green, red


def stroke_width(mask, width):
    rows = {}
    for index, coverage in mask.items():
        y, x = divmod(index, width)
        rows.setdefault(y, {})[x] = coverage
    top, bottom = min(rows), max(rows)
    margin = (bottom - top) // 4
    strokes = []
    for y in range(top + margin, bottom - margin + 1):
        row = rows.get(y, {})
        longest = run = 0
        previous = -2
        for x in sorted(row):
            run = run + row[x] if x == previous + 1 else row[x]
            longest = max(longest, run)
            previous = x
        if longest:
            strokes.append(longest)
    return statistics.median(strokes)


def inspect(pdf):
    log = pdf.with_suffix('.log').read_text(errors='replace')
    cases = re.findall(r'INTEGRAL-LAYOUT\|(\d+)\|(\w+)\|(\d+)\|(\w+)\|(\w+)', log)
    if len(cases) != 512:
        raise ValueError(f'Expected 512 layout cases, found {len(cases)}')
    failures, weights = [], []
    with tempfile.TemporaryDirectory(prefix='raster-', dir=pdf.parent) as directory:
        directory = Path(directory)
        subprocess.run(['mutool', 'draw', '-q', '-r', '360', '-c', 'rgb', '-F', 'ppm',
                        '-o', str(directory / 'page-%04d.ppm'), str(pdf)],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=120)
        for number, command, size, style, scripts in cases:
            width, pixels = read_ppm(directory / f'page-{int(number):04d}.ppm')
            blue, green, red = masks(pixels)
            case = dict(page=int(number), command=command, size=int(size),
                        style=style, scripts=scripts)
            if not blue or not green or not red:
                failures.append(case | {'error': 'missing colored glyphs'})
                continue
            touching = any(index + dy * width + dx in green
                           for index in red for dy in (-1, 0, 1) for dx in (-1, 0, 1))
            if touching:
                failures.append(case | {'error': 'operator and script touch or overlap'})
            blue_rows = [index // width for index in blue]
            green_rows = [index // width for index in green]
            extra = .15 * (max(blue_rows) - min(blue_rows)) if command in {'upint', 'lowint'} else 0
            if (abs(min(blue_rows) - min(green_rows)) > extra + 2
                    or abs(max(blue_rows) - max(green_rows)) > extra + 2):
                failures.append(case | {'error': 'rendered height or axis differs from Termes'})
            if (command in {'intbar', 'intBar', 'upint', 'lowint'}
                    and style in {'D', 'T'} and scripts == 'both'):
                ratio = stroke_width(green, width) / stroke_width(blue, width)
                weights.append(case | {'stroke_ratio': ratio})
                if not 0.80 <= ratio <= 1.30:
                    failures.append(case | {'error': 'stroke weight differs from Termes',
                                            'stroke_ratio': ratio})
    report = pdf.with_suffix('.layout.json')
    report.write_text(json.dumps({'cases': len(cases), 'failures': failures, 'weights': weights},
                                 indent=2) + '\n', encoding='utf-8')
    print(f'{pdf.parent.parent.name}: {len(cases)} rendered layout cases, '
          f'{len(failures)} failures; {report.name}')
    for failure in failures[:8]:
        print(f'  {failure}')
    return not failures


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('pdf', type=Path)
    args = parser.parse_args()
    if shutil.which('mutool') is None:
        parser.error('mutool is required; install MuPDF tools')
    raise SystemExit(0 if inspect(args.pdf.resolve()) else 1)


if __name__ == '__main__':
    main()
