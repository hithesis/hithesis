"""Notification aggregation, delivery acknowledgement and persistent deduplication."""
import importlib.util
import io
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import Mock
from unittest.mock import patch
from urllib.error import HTTPError

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('dev_notify', ROOT / 'scripts/notify-dev.py')
notify = importlib.util.module_from_spec(spec)
spec.loader.exec_module(notify)


def entry(n, changes=None, commit=None):
    sha = commit or f'{n:040x}'
    build_id = f'dev-20261024-{sha[:12]}-{n}-1'
    result = {'schema': 2, 'build_id': build_id, 'commit': sha, 'source_commit': sha, 'source_sha256': 'f' * 64, 'version': 'v3.2b',
            'label': 'v3.2b-dev.1024', 'published_on': '2026-10-24',
            'release_url': f'https://hithesis.site/dev-builds/{build_id}/',
            'changes': changes or []}
    result['report'] = {'filename': 'DEV_UPDATE.pdf',
        'url': result['release_url'] + 'DEV_UPDATE.pdf',
        'sha256': 'd' * 64, 'identity': notify.report_gate().identity(result),
        'model': 'deepseek-flash', 'input_sha256': 'e' * 64}
    return result


class DevNotifyTests(unittest.TestCase):
    def setUp(self):
        clock = patch.object(notify, 'datetime', wraps=datetime)
        self.clock = clock.start()
        self.addCleanup(clock.stop)
        self.clock.now.return_value = datetime(2026, 10, 25, 1, tzinfo=timezone.utc)

    def test_automatic_task_cannot_start_outside_beijing_0800(self):
        for stamp in ('2026-10-24T23:59:59+00:00', '2026-10-25T00:01:00+00:00',
                      '2026-10-25T05:00:00+00:00', '2026-10-25T18:48:29+00:00'):
            with self.subTest(stamp=stamp), tempfile.TemporaryDirectory() as tmp:
                self.clock.now.return_value = datetime.fromisoformat(stamp)
                environment = {'QQ_GROUP_ID': '12345', 'ONEBOT_ACCESS_TOKEN': 'test',
                               'NOTIFY_STATE': str(Path(tmp) / 'state.json')}
                with patch.dict('os.environ', environment), patch('sys.argv', ['notify-dev.py', '--daily']), \
                        patch.object(notify, 'request_publication') as dispatch, \
                        patch.object(notify, 'wait_for_daily_release') as wait, \
                        patch.object(notify, 'fetch_history') as fetch, patch.object(notify, 'notify') as send:
                    notify.main()
                    dispatch.assert_not_called()
                    wait.assert_not_called()
                    fetch.assert_not_called()
                    send.assert_not_called()
                self.assertFalse(list(Path(tmp).iterdir()))

    def test_0800_task_waits_for_its_pdf_and_never_dispatches_actions(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.clock.now.return_value = datetime(2026, 10, 25, 0, tzinfo=timezone.utc)
            environment = {'QQ_GROUP_ID': '12345', 'ONEBOT_ACCESS_TOKEN': 'test',
                           'NOTIFY_STATE': str(Path(tmp) / 'state.json')}
            with patch.dict('os.environ', environment), patch('sys.argv', ['notify-dev.py', '--daily']), \
                    patch.object(notify, 'request_publication') as dispatch, \
                    patch.object(notify, 'wait_for_daily_release', return_value=[entry(1)]) as wait, \
                    patch.object(notify, 'notify') as send:
                notify.main()
                dispatch.assert_not_called()
                wait.assert_called_once()
                send.assert_called_once()

    def test_daily_wait_finds_new_build_without_consuming_state(self):
        state = {'build_id': entry(1)['build_id'], 'commit': entry(1)['commit']}
        original = dict(state)
        sleep = Mock()
        with patch.object(notify, 'fetch_history', side_effect=[[entry(1)], [entry(1), entry(2)]]), \
                patch.object(notify.time, 'monotonic', side_effect=range(20)):
            self.assertEqual(notify.wait_for_daily_release('https://example.com/history', state, 10, sleep),
                             [entry(1), entry(2)])
        sleep.assert_called_once()
        self.assertEqual(state, original)
        with patch.object(notify, 'fetch_history', return_value=[entry(1)]), \
                patch.object(notify.time, 'monotonic', side_effect=range(20)):
            self.assertEqual(notify.wait_for_daily_release('https://example.com/history', state, 5, sleep), [])
        self.assertEqual(state, original)

    def test_explicit_manual_force_can_send_at_night(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.clock.now.return_value = datetime(2026, 10, 25, 18, tzinfo=timezone.utc)
            sender, verifier = Mock(return_value=99), Mock(return_value={})
            self.assertTrue(notify.notify([entry(1)], Path(tmp) / 'state.json', 12345, '', '',
                                          force=True, sender=sender, verifier=verifier))
            sender.assert_called_once()
            verifier.assert_called_once()

    def test_timer_starts_only_daily_0800_and_never_catches_up(self):
        timer = (ROOT / 'deploy/qq-notify/hithesis-dev-notify.timer').read_text()
        service = (ROOT / 'deploy/qq-notify/hithesis-dev-notify.service').read_text()
        self.assertIn('OnCalendar=*-*-* 08:00:00 Asia/Shanghai\n', timer)
        self.assertIn('Persistent=false\n', timer)
        self.assertIn('ExecStart=/opt/hithesis-notify/notify.sh --daily\n', service)
        self.assertNotIn('0/5', timer)

    def test_daily_mode_cannot_be_combined_with_manual_operations(self):
        for flag in ('--force', '--dry-run', '--publish'):
            with self.subTest(flag=flag), patch('sys.argv', ['notify-dev.py', '--daily', flag]), \
                    patch('sys.stderr', io.StringIO()), self.assertRaises(SystemExit) as result:
                notify.main()
            self.assertEqual(result.exception.code, 2)

    def test_public_history_raw_response_and_first_publish_absence(self):
        payload = {'schema': 1, 'repository': 'hithesis/hithesis', 'releases': [entry(1)]}
        with patch.object(notify, 'urlopen', return_value=io.BytesIO(json.dumps(payload).encode())) as request:
            self.assertEqual(notify.fetch_history(notify.HISTORY_URL), payload['releases'])
            sent = request.call_args.args[0]
            self.assertIn('https://hithesis.site/dev-history.json?checked=', sent.full_url)
            self.assertEqual(sent.get_header('Accept'), 'application/json')
        with patch.object(notify, 'urlopen', side_effect=HTTPError(notify.HISTORY_URL, 404, 'Not found', {}, None)):
            self.assertEqual(notify.fetch_history(notify.HISTORY_URL), [])

    def test_first_install_only_announces_latest(self):
        releases = [entry(1), entry(2)]
        self.assertEqual(notify.pending_releases(releases, None), [releases[-1]])

    def test_default_polling_never_dispatches_actions(self):
        with tempfile.TemporaryDirectory() as tmp:
            environment = {'QQ_GROUP_ID': '12345', 'ONEBOT_ACCESS_TOKEN': 'test',
                           'NOTIFY_STATE': str(Path(tmp) / 'state.json')}
            with patch.dict('os.environ', environment), patch('sys.argv', ['notify-dev.py']), \
                    patch.object(notify, 'request_publication') as dispatch, \
                    patch.object(notify, 'fetch_history', return_value=[]):
                notify.main()
                dispatch.assert_not_called()

    def test_accumulates_unannounced_changes_without_duplicate_lines(self):
        change = {'id': 'old', 'text': '修复字段折行'}
        releases = [entry(1), entry(2, [change]), entry(3, [change, {'id': 'new', 'text': '增加选项'}])]
        pending = notify.pending_releases(releases, {'build_id': releases[0]['build_id'], 'commit': releases[0]['commit']})
        text = notify.format_message(pending)
        self.assertEqual(text.count('修复字段折行'), 1)
        self.assertIn('增加选项', text)
        self.assertIn('v3.2b-dev.1024', text)

    def test_report_link_is_bound_to_the_announced_immutable_release(self):
        release = entry(1)
        url = release['release_url'] + 'DEV_UPDATE.pdf'
        self.assertIn('详细说明（PDF）：' + url, notify.format_message([release]))
        release['report']['url'] = 'https://example.com/unrelated.pdf'
        with self.assertRaisesRegex(ValueError, 'PDF manifest does not match'):
            notify.format_message([release])

    def test_failed_delivery_does_not_consume_update_and_force_resends(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp) / 'state.json'
            releases = [entry(1)]
            failed = Mock(side_effect=RuntimeError('delivery failed'))
            verifier = Mock(return_value={})
            with self.assertRaises(RuntimeError):
                notify.notify(releases, state, 12345, 'http://localhost', 'token', sender=failed, verifier=verifier)
            self.assertFalse(state.exists())
            sender = Mock(return_value=99)
            self.assertTrue(notify.notify(releases, state, 12345, 'http://localhost', 'token', sender=sender, verifier=verifier))
            self.assertFalse(notify.notify(releases, state, 12345, 'http://localhost', 'token', sender=sender, verifier=verifier))
            self.assertEqual(sender.call_count, 1)
            self.assertTrue(notify.notify(releases, state, 12345, 'http://localhost', 'token', force=True, sender=sender, verifier=verifier))
            self.assertEqual(sender.call_count, 2)
            self.assertEqual(json.loads(state.read_text())['message_id'], 99)

    def test_missing_or_failed_pdf_never_sends_or_consumes_notification(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp) / 'state.json'
            sender = Mock()
            broken = entry(1); del broken['report']
            with self.assertRaisesRegex(ValueError, 'PDF required'):
                notify.notify([broken], state, 12345, '', '', sender=sender)
            with self.assertRaisesRegex(RuntimeError, 'PDF unavailable'):
                notify.notify([entry(1)], state, 12345, '', '', sender=sender,
                    verifier=Mock(side_effect=RuntimeError('PDF unavailable')))
            sender.assert_not_called()
            self.assertFalse(state.exists())

    def test_successful_workflow_without_its_published_pdf_cannot_notify(self):
        with tempfile.TemporaryDirectory() as tmp:
            environment = {'QQ_GROUP_ID': '12345', 'ONEBOT_ACCESS_TOKEN': 'test',
                           'NOTIFY_STATE': str(Path(tmp) / 'state.json')}
            with patch.dict('os.environ', environment), patch('sys.argv', ['notify-dev.py', '--publish']), \
                    patch.object(notify, 'request_publication', return_value={'head_sha': 'f' * 40}), \
                    patch.object(notify, 'fetch_history', return_value=[entry(1)]), \
                    patch.object(notify, 'notify') as send:
                with self.assertRaisesRegex(RuntimeError, 'did not publish this source and its PDF'):
                    notify.main()
                send.assert_not_called()

    def test_same_source_rebuild_and_dry_run_are_quiet(self):
        state = {'build_id': entry(1)['build_id'], 'commit': entry(1)['commit']}
        self.assertEqual(notify.pending_releases([entry(1), entry(2, commit=state['commit'])], state), [])
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'state.json'
            sender = Mock()
            notify.notify([entry(1)], path, 12345, '', '', dry_run=True, sender=sender)
            sender.assert_not_called()
            self.assertFalse(path.exists())

    def test_missing_history_is_not_replayed(self):
        with self.assertRaises(ValueError):
            notify.pending_releases([entry(2)], {'build_id': 'missing', 'commit': entry(1)['commit']})

    def test_onebot_http_contract_and_failed_retcode(self):
        requests = []
        result = {'status': 'ok', 'retcode': 0, 'data': {'message_id': 321}}
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args): pass
            def do_POST(self):
                requests.append((self.path, self.headers.get('Authorization'), json.loads(self.rfile.read(int(self.headers['Content-Length'])))))
                payload = json.dumps(result).encode()
                self.send_response(200)
                self.end_headers()
                self.wfile.write(payload)
        server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            url = f'http://127.0.0.1:{server.server_port}'
            self.assertEqual(notify.send_onebot(url, 'test-token', 12345, '[CQ:at,qq=all]'), 321)
            self.assertEqual(requests[0][0], '/send_group_msg')
            self.assertEqual(requests[0][1], 'Bearer test-token')
            self.assertTrue(requests[0][2]['auto_escape'])
            result.update(status='failed', retcode=100)
            with self.assertRaises(RuntimeError):
                notify.send_onebot(url, 'test-token', 12345, 'test')
        finally:
            server.shutdown()
            server.server_close()
            thread.join()


if __name__ == '__main__':
    unittest.main()
