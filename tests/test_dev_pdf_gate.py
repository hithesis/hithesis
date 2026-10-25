"""Missing, stale and corrupt PDFs block publication before any remote writes."""
import hashlib
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts' / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gate, release = load('dev-report-gate'), load('dev-release')


class RequiredPDFTests(unittest.TestCase):
    def test_new_format_manifest_cannot_point_at_an_unversioned_pdf(self):
        from pypdf import PdfWriter
        from test_dev_release import build
        info = build() | {'report': {'format_version': 1}}
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'DEV_UPDATE.pdf'
            writer = PdfWriter()
            writer.add_blank_page(width=595, height=842)
            writer.add_metadata({'/Subject': 'hithesis-report:' + gate.identity(info), '/Title': 'x' * 1800})
            writer.write(path)
            with self.assertRaisesRegex(ValueError, 'report format does not match'):
                gate.validate(path, info)

    def test_publication_without_pdf_cannot_call_git_or_github(self):
        from test_dev_release import build
        info = build()
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            release.write_json(folder / 'dev.json', info)
            environment = {'GITHUB_REPOSITORY': 'hithesis/hithesis', 'GITHUB_REF': 'refs/heads/dev',
                'GITHUB_EVENT_NAME': 'workflow_dispatch', 'GITHUB_SHA': info['source_commit']}
            with patch.dict('os.environ', environment), patch.object(release, 'command') as remote:
                with self.assertRaisesRegex(ValueError, 'PDF required'):
                    release.publish(folder, folder)
                remote.assert_not_called()

    def test_manifest_is_bound_to_source_build_and_model(self):
        from test_dev_release import build
        info = build()
        info['report'] = {'filename': 'DEV_UPDATE.pdf', 'url': info['release_url'] + 'DEV_UPDATE.pdf',
            'sha256': 'a' * 64, 'identity': gate.identity(info), 'model': 'deepseek-flash', 'input_sha256': 'b' * 64}
        gate.manifest(info)
        with self.assertRaisesRegex(ValueError, 'does not match'):
            gate.manifest(info | {'source_commit': 'c' * 40})

    def test_pdf_header_alone_and_valid_but_stale_pdf_are_rejected(self):
        from pypdf import PdfWriter
        from test_dev_release import build
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'DEV_UPDATE.pdf'
            path.write_bytes(b'%PDF-' + b'x' * 1500)
            with self.assertRaisesRegex(ValueError, 'validation failed'):
                gate.validate(path, build())
            writer = PdfWriter(); writer.add_blank_page(width=595, height=842)
            writer.add_metadata({'/Subject': 'old-build', '/Title': 'x' * 1800})
            writer.write(path)
            with self.assertRaisesRegex(ValueError, 'does not belong'):
                gate.validate(path, build())
