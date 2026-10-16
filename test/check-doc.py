import re

from run import ROOT, loaded_font, loaded_input, loaded_package


def main():
    directory = ROOT / 'build/doc'
    failed = False
    for name in ('times-math', 'times-math-cn', 'times-math-glyphs'):
        log = directory / f'{name}.log'
        text = log.read_text(errors='replace') if log.is_file() else ''
        problems = re.findall(
            r'^!.*|Missing character:.*|Overfull .*|.*(?:undefined references|'
            r'undefined on input line|Rerun to get cross-references).*', text, re.MULTILINE)
        passed = log.is_file() and (directory / f'{name}.pdf').is_file() and not problems
        fls = directory / f'{name}.fls'
        passed &= fls.is_file() and loaded_package(fls, ROOT)
        passed &= fls.is_file() and loaded_font(fls, ROOT, expected=ROOT / 'times-math-integrals.otf')
        sources = [ROOT / f'{name}.tex']
        if name != 'times-math-glyphs':
            sources.extend(ROOT / source for source in ('times-math-doc.tex', 'times-math.ltx'))
        passed &= fls.is_file() and all(loaded_input(fls, ROOT, source) for source in sources)
        print(f'{name}: {"PASS" if passed else "FAIL"}')
        for problem in problems:
            print(f'  {problem}')
        failed |= not passed
    raise SystemExit(1 if failed else 0)


if __name__ == '__main__':
    main()
