import argparse
from dataclasses import dataclass
import os
from pathlib import Path
import re
import subprocess

from run import FONT, ROOT, STY, loaded_font, loaded_package

TNR = 'Times New Roman'
TERMES = 'TeX Gyre Termes'


@dataclass
class Case:
    name: str
    option: str
    canonical: str | None
    channel: str = 'local'
    halt: bool = True


CASES = (
    Case('default', '', TNR),
    Case('tnr-short-name', 'text-font=TNR', None, halt=False),
    Case('tnr-spaced', 'text-font=Times New Roman', TNR),
    Case('tnr-braced', 'text-font={  Times   New Roman  }', TNR),
    Case('tnr-compact-case', 'text-font=tImEsNeWrOmAn', TNR),
    Case('tnr-space-command', r'text-font=Times\space New\space Roman', TNR),
    Case('termes-short-name', 'text-font=termes', None, halt=False),
    Case('termes-spaced', 'text-font=TeX Gyre Termes', TERMES),
    Case('termes-braced-case', 'text-font={  tex   GYRE  termes  }', TERMES),
    Case('termes-compact', 'text-font=TeXGyreTermes', TERMES),
    Case('termes-forwarded', 'text-font=TeX Gyre Termes', TERMES, 'forward'),
    Case('termes-forwarded-space', r'text-font=TeX\space Gyre\space Termes', TERMES, 'forward'),
    Case('termes-global', 'text-font=TeX Gyre Termes', TERMES, 'global'),
    Case('none', 'text-font=none', 'none'),
    Case('none-case', 'text-font={ NoNe }', 'none'),
    Case('unknown-installed', 'text-font=Arial', None, halt=False),
    Case('unknown-missing', 'text-font={No Such Text Font}', None),
    Case('unknown-math-font', 'text-font=TeX Gyre Termes Math', None),
    Case('unknown-forwarded', 'text-font=tgermes', None, 'forward'),
    Case('empty', 'text-font={}', None),
    Case('missing-value', 'text-font', None),
)


def source(case):
    lines = []
    if case.channel == 'forward':
        lines.append(r'\PassOptionsToPackage{' + case.option + '}{times-math}')
    options = '[' + case.option + ']' if case.option else ''
    lines.append(r'\documentclass' + (options if case.channel == 'global' else '') + '{article}')
    lines.append(r'\usepackage' + (options if case.channel == 'local' else '') + '{times-math}')
    if case.canonical is not None:
        expected = case.canonical.replace(' ', '~')
        lines.extend((
            r'\ExplSyntaxOn',
            r'\str_if_eq:VnF \l__mt_text_font_tl {' + expected + '}',
            r'  {\PackageError{test-text-font}{Canonical~font~name~mismatch}{}}',
        ))
        if case.canonical == 'none':
            lines.append(r'\bool_if:NT \l__mt_text_layer_bool {\PackageError{test-text-font}{Unexpected~text~layer}{}}')
        else:
            lines.extend((
                r'\IfFontExistsTF {' + expected + '}',
                r'  {\bool_if:NF \l__mt_text_layer_bool {\PackageError{test-text-font}{Text~layer~was~skipped}{}}}',
                r'  {\bool_if:NT \l__mt_text_layer_bool {\PackageError{test-text-font}{Missing~font~layer~was~enabled}{}}}',
            ))
        lines.extend((
            r'\iow_term:x {MT-TEXT-FONT=\tl_to_str:V\l__mt_text_font_tl}',
            r'\bool_if:NTF \l__mt_text_layer_bool',
            r'  {\iow_term:n {MT-TEXT-LAYER=yes}} {\iow_term:n {MT-TEXT-LAYER=no}}',
            r'\ExplSyntaxOff',
        ))
    lines.extend((r'\typeout{MT-OPTION-CONTINUED}', r'\begin{document}',
                  r'$\mathrm{A}+\mathit{x}+\symbf{v}+\alpha+\fint_0^1$.', r'\end{document}'))
    return '\n'.join(lines) + '\n'


def check(engine, case, env):
    work = ROOT / 'test/output/options' / engine / case.name
    work.mkdir(parents=True, exist_ok=True)
    for suffix in ('.pdf', '.log', '.fls'):
        (work / ('case' + suffix)).unlink(missing_ok=True)
    tex = work / 'case.tex'
    tex.write_text(source(case), encoding='utf-8')
    command = [engine, '-interaction=nonstopmode', '-no-shell-escape', '-recorder']
    if case.halt:
        command.append('-halt-on-error')
    command.append(str(tex))
    with (work / 'console.txt').open('w') as console:
        result = subprocess.run(command, cwd=work, env=env, stdin=subprocess.DEVNULL,
                                stdout=console, stderr=subprocess.STDOUT, timeout=180)
    log = work / 'case.log'
    text = log.read_text(errors='replace') if log.is_file() else ''
    compact = re.sub(r'\s+', '', text.replace('(times-math)', ''))
    fls = work / 'case.fls'
    if case.canonical is None:
        passed = (result.returncode != 0 and 'text-font' in text
                  and 'MT-OPTION-CONTINUED' not in text and not (work / 'case.pdf').exists()
                  and 'Thetext-fontlayerwillbeskipped' not in compact)
        if case.name != 'missing-value':
            passed &= 'Unknowntext-fontvalue' in compact and all(
                value in compact for value in ('TimesNewRoman', 'TeXGyreTermes', 'none'))
    else:
        passed = (result.returncode == 0 and 'MT-OPTION-CONTINUED' in text
                  and f'MT-TEXT-FONT={case.canonical}' in text
                  and not re.search(r'^!|Missing character:|Overfull ', text, re.MULTILINE)
                  and fls.is_file() and loaded_package(fls, work) and loaded_font(fls, work, env))
        active = 'MT-TEXT-LAYER=yes' in text
        if active:
            family = case.canonical.replace(' ', '')
            passed &= f"Fontfamily'{family}(" in compact
        if case.canonical == 'none':
            passed &= not active and 'Thetext-fontlayerwillbeskipped' not in compact
    print(f'{engine}/options/{case.name}: {"PASS" if passed else "FAIL"}'
          f' ({case.channel}; {"error required" if case.canonical is None else case.canonical})', flush=True)
    return passed


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--engine', choices=('lualatex', 'xelatex'), action='append')
    parser.add_argument('--case', choices=tuple(case.name for case in CASES))
    args = parser.parse_args()
    if not STY.is_file() or not FONT.is_file():
        parser.error('Run make sty first')
    env = os.environ.copy()
    env['TEXINPUTS'] = str(STY.parent) + '//' + os.pathsep + env.get('TEXINPUTS', '')
    env['OPENTYPEFONTS'] = str(FONT.parent) + '//' + os.pathsep + env.get('OPENTYPEFONTS', '')
    failed = False
    for engine in args.engine or ('lualatex', 'xelatex'):
        for case in CASES:
            if args.case and case.name != args.case:
                continue
            try:
                failed |= not check(engine, case, env)
            except subprocess.TimeoutExpired:
                print(f'{engine}/options/{case.name}: FAIL (timeout)', flush=True)
                failed = True
    raise SystemExit(1 if failed else 0)


if __name__ == '__main__':
    main()
