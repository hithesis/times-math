import os
from pathlib import Path
import re
import subprocess
import tempfile
import zipfile

from run import ROOT, loaded_font, loaded_input


def check_archives():
    tds_path = ROOT / 'times-math.tds.zip'
    with zipfile.ZipFile(ROOT / 'times-math-ctan.zip') as ctan, zipfile.ZipFile(tds_path) as tds:
        assert ctan.testzip() is None and tds.testzip() is None
        assert ctan.read('times-math.tds.zip') == tds_path.read_bytes()
        for name in ctan.namelist():
            if not name.startswith('times-math/') or name.endswith('/'):
                continue
            relative = Path(name).relative_to('times-math')
            if relative.suffix == '.pdf':
                assert ctan.read(name) == tds.read('doc/latex/times-math/' + str(relative))
            else:
                assert not {'build', '__pycache__', 'output'} & set(relative.parts), name
                assert ctan.read(name) == (ROOT / relative).read_bytes(), name
        assert tds.read('tex/latex/times-math/times-math.sty') == (
            ROOT / 'build/unpacked/times-math.sty').read_bytes()
        assert tds.read('fonts/opentype/public/times-math/times-math-integrals.otf') == (
            ROOT / 'times-math-integrals.otf').read_bytes()
    print('CTAN/TDS archives: current sources, matching style, font and documents PASS')


def main():
    check_archives()
    with tempfile.TemporaryDirectory(prefix='font-install-', dir=ROOT / 'build') as directory:
        root = Path(directory)
        texmf = root / 'texmf'
        with zipfile.ZipFile(ROOT / 'times-math.tds.zip') as archive:
            archive.extractall(texmf)
        sty = texmf / 'tex/latex/times-math/times-math.sty'
        font = texmf / 'fonts/opentype/public/times-math/times-math-integrals.otf'
        assert sty.is_file() and font.is_file()
        env = os.environ.copy()
        env.update(TEXMFHOME=str(texmf), TEXINPUTS='', OPENTYPEFONTS='')
        for engine in ('lualatex', 'xelatex'):
            work = root / engine
            work.mkdir()
            for expected in (sty, font):
                found = subprocess.check_output(['kpsewhich', expected.name], cwd=work,
                                                env=env, text=True).strip()
                assert Path(found).resolve() == expected.resolve(), found
            result = subprocess.run(
                [engine, '-interaction=nonstopmode', '-halt-on-error', '-no-shell-escape',
                 '-recorder', str(ROOT / 'test/test-integrals.tex')],
                cwd=work, env=env, stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=180)
            if result.returncode:
                log = ROOT / f'build/font-install-{engine}.log'
                log.write_text(result.stdout, encoding='utf-8')
                raise RuntimeError(f'Isolated font installation failed; see {log}')
            log = (work / 'test-integrals.log').read_text(errors='replace')
            assert not re.search(r'^!|Missing character:|Overfull ', log, re.MULTILINE)
            fls = work / 'test-integrals.fls'
            assert loaded_input(fls, work, sty)
            assert loaded_font(fls, work, env, font)
            print(f'{engine}: isolated TDS style and OTF installation PASS')


if __name__ == '__main__':
    main()
