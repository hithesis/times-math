from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
STEMS = ('times-math', 'times-math-cn', 'times-math-glyphs')
SUFFIXES = ('.aux', '.fdb_latexmk', '.fls', '.log', '.out', '.pdf',
            '.synctex.gz', '.toc', '.xdv')


def main():
    for name in ('build', 'test/output', 'dev/__pycache__', 'test/__pycache__'):
        path = ROOT / name
        if path.exists():
            shutil.rmtree(path)
    for stem in STEMS:
        for suffix in SUFFIXES:
            (ROOT / (stem + suffix)).unlink(missing_ok=True)
    for name in ('times-math.sty', 'times-math-ctan.zip', 'times-math.tds.zip', '.DS_Store'):
        (ROOT / name).unlink(missing_ok=True)


if __name__ == '__main__':
    main()
