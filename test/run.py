import argparse
import os
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
STY = ROOT / 'build/unpacked/times-math.sty'
FONT = STY.with_name('times-math-integrals.otf')


def input_paths(fls, directory, name):
    paths = set()
    for line in fls.read_text(errors='replace').splitlines():
        if line.startswith('INPUT '):
            path = Path(line[6:])
            if path.name == name:
                paths.add((directory / path).resolve())
    return paths


def loaded_input(fls, directory, expected):
    return input_paths(fls, directory, expected.name) == {expected.resolve()}


def loaded_package(fls, directory):
    return loaded_input(fls, directory, STY)


def loaded_font(fls, directory, env=None, expected=FONT):
    paths = input_paths(fls, directory, expected.name)
    if paths and paths != {expected.resolve()}:
        return False
    found = subprocess.check_output(['kpsewhich', expected.name], cwd=directory,
                                    env=env, text=True).strip()
    return bool(found) and Path(found).resolve() == expected.resolve()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--engine', choices=('lualatex', 'xelatex'), action='append')
    args = parser.parse_args()
    if not STY.is_file() or not FONT.is_file():
        parser.error('Run make sty first')
    env = os.environ.copy()
    env['TEXINPUTS'] = str(STY.parent) + '//' + os.pathsep + env.get('TEXINPUTS', '')
    env['OPENTYPEFONTS'] = str(FONT.parent) + '//' + os.pathsep + env.get('OPENTYPEFONTS', '')
    failed = False
    for engine in args.engine or ('lualatex', 'xelatex'):
        for source in sorted((ROOT / 'test').glob('test-*.tex')):
            work = ROOT / 'test/output' / engine / source.stem
            work.mkdir(parents=True, exist_ok=True)
            log = work / source.with_suffix('.log').name
            fls = work / source.with_suffix('.fls').name
            for path in (log, fls, work / f'{source.stem}.layout.json'):
                path.unlink(missing_ok=True)
            command = [engine, '-interaction=nonstopmode', '-halt-on-error',
                       '-no-shell-escape', '-recorder', str(source)]
            try:
                with (work / 'console.txt').open('w') as console:
                    result = subprocess.run(command, cwd=work, env=env, stdin=subprocess.DEVNULL,
                                            stdout=console, stderr=subprocess.STDOUT, timeout=180)
                text = log.read_text(errors='replace') if log.exists() else ''
                errors = len(re.findall(r'^!', text, re.MULTILINE))
                missing = text.count('Missing character:')
                overfull = text.count('Overfull ')
                standalone = source.stem == 'test-integral-font'
                correct_sty = fls.is_file() and (
                    not input_paths(fls, work, STY.name) if standalone else loaded_package(fls, work))
                correct_font = fls.is_file() and loaded_font(fls, work, env)
                passed = (result.returncode == 0 and log.is_file() and not errors
                          and not missing and not overfull and correct_sty and correct_font)
                if source.stem == 'test-warnings':
                    compact = re.sub(r'\s+', '', text.replace('(times-math)', ''))
                    passed &= (text.count('Package times-math Warning:') == 2
                               and "Textfont'TimesNewRoman'notfound." in compact
                               and "Package'mathrsfs'mayconflictwithtimes-math." in compact)
                layout = ''
                if passed and source.stem == 'test-integral-layout':
                    with (work / 'console.txt').open('a') as console:
                        check = subprocess.run(
                            [sys.executable, str(ROOT / 'test/check-integral-layout.py'),
                             str(work / f'{source.stem}.pdf')],
                            cwd=work, stdout=console, stderr=subprocess.STDOUT, timeout=180)
                    passed = check.returncode == 0
                    layout = f', rendered-layout={passed}'
                print(f'{engine}/{source.stem}: {"PASS" if passed else "FAIL"} '
                      f'(exit={result.returncode}, errors={errors}, missing={missing}, '
                      f'overfull={overfull}, extracted-sty={correct_sty}, bundled-font={correct_font}{layout})', flush=True)
            except subprocess.TimeoutExpired:
                passed = False
                print(f'{engine}/{source.stem}: FAIL (timeout; see {work})', flush=True)
            failed |= not passed
    raise SystemExit(1 if failed else 0)


if __name__ == '__main__':
    main()
