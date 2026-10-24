"""Runner-only Workbench credentials and fixed server command checks."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('workbench_notify', ROOT / 'scripts/workbench-notify.py')
workbench = importlib.util.module_from_spec(spec)
spec.loader.exec_module(workbench)


class WorkbenchNotifyTests(unittest.TestCase):
    def test_private_config_and_preserve_existing_credentials(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            config = workbench.write_config(home, 'test-access-id', 'test-access-secret')
            self.assertEqual(config.stat().st_mode & 0o777, 0o600)
            self.assertEqual(config.parent.stat().st_mode & 0o777, 0o700)
            payload = json.loads(config.read_text())
            self.assertEqual(payload['profiles']['default']['mode'], 'AK')
            self.assertFalse(payload['agent_enabled'])
            before = config.read_bytes()
            with self.assertRaises(FileExistsError):
                workbench.write_config(home, 'other-id', 'other-secret')
            self.assertEqual(config.read_bytes(), before)

    def test_missing_credentials_do_not_create_a_config(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                workbench.write_config(Path(tmp), '', '')
            self.assertFalse((Path(tmp) / '.workbench').exists())

    def test_remote_commands_are_fixed(self):
        self.assertEqual(workbench.remote_command(), '/opt/hithesis-notify/notify.sh')
        self.assertEqual(workbench.remote_command(True), '/opt/hithesis-notify/notify.sh --force')


if __name__ == '__main__':
    unittest.main()
