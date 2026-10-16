"""Regression tests for false-success and stale-output handling in the Lua runner."""
from contextlib import redirect_stderr, redirect_stdout
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('check_lua', ROOT / 'scripts/check-lua.py')
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


class LuaRunnerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        (self.root / 'tests').mkdir()
        (self.root / 'testfiles').mkdir()
        (self.root / 'config-lua.lua').write_text('checkengines={"luatex"}\n')
        self.manifest = (ROOT / 'tests/lua-cases.txt').read_text(encoding='utf-8')
        (self.root / 'tests/lua-cases.txt').write_text(self.manifest, encoding='utf-8')
        self.cases = [line for line in self.manifest.splitlines() if line and not line.startswith('#')]
        self.expected = 'TEST 1: Preserve geometry\nLaTeX Font Info: preserved\nstate=yes\n'
        for name in self.cases:
            (self.root / 'testfiles' / (name + '.lvt')).write_text('test input\n')
            (self.root / 'testfiles' / (name + '.luatex.tlg')).write_text(self.expected)
        self.work = self.root / 'build/test-config-lua'

    def output(self, cases=None):
        cases = self.cases if cases is None else cases
        return 'Running checks on\n' + ''.join(f'  {name} ({i}/{len(cases)})\n'
            for i, name in enumerate(cases, 1)) + '\n  All checks passed\n'

    def write_logs(self, cases=None, engine='LuaHBTeX', text=None):
        self.work.mkdir(parents=True, exist_ok=True)
        for name in self.cases if cases is None else cases:
            (self.work / (name + '.log')).write_text(f'This is {engine}, Version test\n')
            (self.work / (name + '.luatex.log')).write_text(self.expected if text is None else text)

    def execute(self, effect):
        with patch.object(runner.subprocess, 'run', side_effect=effect) as invoked:
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                code = runner.run_checks(self.root)
        report = json.loads((self.root / 'build/lua-checks.json').read_text())
        return code, report, invoked

    def test_all_nine_lua_logs_and_expected_results_are_required(self):
        def fake(command, **kwargs):
            self.assertEqual(command, ['l3build', 'check', '-c', 'config-lua', '-e', 'luatex'])
            self.assertEqual(kwargs['cwd'], self.root)
            self.write_logs()
            return subprocess.CompletedProcess(command, 0, self.output())
        code, report, _ = self.execute(fake)
        self.assertEqual(code, 0)
        self.assertTrue(report['success'])
        self.assertEqual(report['executed_count'], 9)

    def test_skipped_engine_with_exit_zero_cannot_reuse_old_logs(self):
        self.write_logs()
        (self.work / 'unrelated.txt').write_text('keep')
        code, report, _ = self.execute(lambda *a, **k: subprocess.CompletedProcess(a[0], 0,
            'Skipping unknown engine luatex\nNo applicable engine requested, config ignored\n'))
        self.assertEqual(code, 1)
        self.assertFalse(report['success'])
        self.assertEqual(report['executed_count'], 0)
        self.assertFalse((self.work / (self.cases[0] + '.luatex.log')).exists())
        self.assertEqual((self.work / 'unrelated.txt').read_text(), 'keep')

    def test_eight_cases_are_not_a_success(self):
        def fake(command, **kwargs):
            self.write_logs(self.cases[:-1])
            return subprocess.CompletedProcess(command, 0, self.output(self.cases[:-1]))
        code, report, _ = self.execute(fake)
        self.assertEqual(code, 1)
        self.assertEqual(report['executed_count'], 8)

    def test_xetex_output_is_not_accepted_as_lua(self):
        def fake(command, **kwargs):
            self.write_logs(engine='XeTeX')
            return subprocess.CompletedProcess(command, 0, self.output())
        code, report, _ = self.execute(fake)
        self.assertEqual(code, 1)
        self.assertTrue(any('LuaTeX/LuaHBTeX' in error for error in report['errors']))

    def test_nine_progress_rows_must_name_the_nine_expected_cases(self):
        def fake(command, **kwargs):
            self.write_logs()
            return subprocess.CompletedProcess(command, 0, self.output([self.cases[0]] * 9))
        code, report, _ = self.execute(fake)
        self.assertEqual(code, 1)
        self.assertEqual(report['executed_count'], 9)
        self.assertFalse(report['success'])

    def test_nonzero_exit_is_preserved_even_with_complete_outputs(self):
        def fake(command, **kwargs):
            self.write_logs()
            return subprocess.CompletedProcess(command, 1, self.output())
        code, report, _ = self.execute(fake)
        self.assertEqual(code, 1)
        self.assertEqual(report['l3build_exit_code'], 1)

    def test_font_info_changes_are_not_filtered(self):
        def fake(command, **kwargs):
            self.write_logs(text=self.expected.replace('Info: preserved', 'Info: changed'))
            return subprocess.CompletedProcess(command, 0, self.output())
        code, report, _ = self.execute(fake)
        self.assertEqual(code, 1)
        self.assertFalse(report['tests'][0]['passed'])

    def test_a_missing_normalized_log_cannot_pass(self):
        def fake(command, **kwargs):
            self.write_logs()
            (self.work / (self.cases[0] + '.luatex.log')).unlink()
            return subprocess.CompletedProcess(command, 0, self.output())
        code, report, _ = self.execute(fake)
        self.assertEqual(code, 1)
        self.assertFalse(report['tests'][0]['passed'])

    def test_missing_lua_baseline_stops_before_execution(self):
        (self.root / 'testfiles' / (self.cases[0] + '.luatex.tlg')).unlink()
        code, report, invoked = self.execute(lambda *a, **k: self.fail('must not execute'))
        self.assertEqual(code, 1)
        invoked.assert_not_called()
        self.assertFalse(report['success'])

    def test_engine_flags_are_not_forwarded_to_a_different_configuration(self):
        with patch.object(runner.subprocess, 'run') as invoked:
            with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as raised:
                runner.main(['-e', 'luatex'])
        self.assertEqual(raised.exception.code, 2)
        invoked.assert_not_called()


if __name__ == '__main__':
    unittest.main()
