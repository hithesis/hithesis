"""Check font evidence integrity and actual shipped-font auditing without private fonts."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('word_font_controls', ROOT / 'scripts/compare-word-fonts.py')
control = importlib.util.module_from_spec(spec); spec.loader.exec_module(control)


class FontControlTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name)
        self.fonts = self.path / 'private'; self.fonts.mkdir()

    def make_record(self):
        files = {}
        for name in ('times.ttf', 'timesbd.ttf', 'timesi.ttf', 'timesbi.ttf', 'simsun.ttc', 'simhei.ttf'):
            data = ('synthetic integrity fixture ' + name).encode()
            (self.fonts / name).write_bytes(data)
            files[name] = hashlib.sha256(data).hexdigest()
        (self.fonts / 'fonts.json').write_text(json.dumps({'files': files}))
        repo = self.path / 'repo'; reference = repo / 'tests/reference'; reference.mkdir(parents=True)
        (reference / 'word-fonts.json').write_text(json.dumps({'files': {n: files[n] for n in ('times.ttf', 'timesbd.ttf', 'simsun.ttc', 'simhei.ttf')}}))
        return repo

    def test_changed_font_bytes_are_rejected(self):
        repo = self.make_record()
        with patch.object(control, 'ROOT', repo):
            control.verify_fonts(self.fonts)
            (self.fonts / 'simsun.ttc').write_bytes(b'wrong font bytes')
            with self.assertRaisesRegex(ValueError, 'does not match hash record'):
                control.verify_fonts(self.fonts)

    def test_shipped_host_font_is_rejected_in_selected_cjk_control(self):
        self.make_record()
        host = self.path / 'host-simsun.ttc'; host.write_bytes(b'host font')
        (self.path / 'used-fonts.tsv').write_text('id\tname\tfilename\tresolved\tsubfont\n'
            f'1\tTimes New Roman\t{self.fonts / "times.ttf"}\t\t1\n'
            f'2\tSimSun\t{host}\t\t1\n')
        with self.assertRaisesRegex(ValueError, 'still uses host files'):
            control.font_audit(self.path, self.fonts, 'cjk')

    def test_actual_file_hashes_are_preserved(self):
        self.make_record()
        (self.path / 'used-fonts.tsv').write_text('id\tname\tfilename\tresolved\tsubfont\n'
            f'1\tTimes New Roman\t{self.fonts / "times.ttf"}\t\t1\n'
            f'2\tSimSun\t{self.fonts / "simsun.ttc"}\t\t1\n')
        rows = control.font_audit(self.path, self.fonts, 'all')
        self.assertTrue(all(r['from_private_vm_directory'] for r in rows))
        self.assertEqual(rows[1]['sha256'], control.digest(self.fonts / 'simsun.ttc'))

    def test_lua_audit_records_only_shipped_nested_glyph_fonts(self):
        script = r'''
node={id=function(name) return name end,
  traverse=function(list) local i=0; return function() i=i+1; return list[i] end end}
token={create=function() return {mode=1} end}
tex={box={[1]={list={{id='glyph',font=1},{id='vlist',list={{id='hlist',list={{id='glyph',font=2}}}}}}}}}
font={getfont=function(id) return {fullname='Used '..id,filename='font-'..id..'.ttf',specification={sub=1}} end}
local audit=dofile(AUDIT)
audit.page(); audit.finish()
'''.replace('AUDIT', json.dumps(str(ROOT / 'scripts/audit-used-fonts.lua')))
        path = self.path / 'audit-fixture.lua'; path.write_text(script)
        run = subprocess.run(['texlua', str(path)], cwd=self.path, capture_output=True, text=True)
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        rows = [line.split('\t') for line in (self.path / 'used-fonts.tsv').read_text().splitlines()]
        self.assertTrue(all(len(row) == 5 for row in rows))
        self.assertEqual([row[0] for row in rows[1:]], ['1', '2'])


if __name__ == '__main__':
    unittest.main()
