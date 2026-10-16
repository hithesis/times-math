from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
STAGE = ROOT / 'build/release-source'
FILES = (
    'times-math.dtx', 'times-math.ins', 'times-math.tex', 'times-math-cn.tex',
    'times-math-doc.tex', 'times-math.ltx', 'times-math-glyphs.tex',
    'build.lua', 'Makefile', 'README.md', 'LICENSE',
    'times-math-integrals.otf', 'GUST-FONT-LICENSE.txt', 'MANIFEST-times-math-integrals.txt',
)


def main():
    paths = [ROOT / name for name in FILES]
    for directory, suffixes in (('dev', {'.lua', '.py', '.txt'}), ('test', {'.lua', '.py', '.tex'})):
        paths.extend(sorted(path for path in (ROOT / directory).iterdir()
                            if path.is_file() and path.suffix in suffixes))
    if STAGE.exists():
        shutil.rmtree(STAGE)
    for path in paths:
        target = STAGE / path.relative_to(ROOT)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
    print(f'Staged {len(paths)} source files in {STAGE.relative_to(ROOT)}')


if __name__ == '__main__':
    main()
