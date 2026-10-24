"""Check published dev builds and send a daily digest through OneBot v11 HTTP."""
import argparse
from datetime import datetime, timezone
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import sys
import time
import tempfile
import uuid
from urllib.error import HTTPError
from urllib.request import Request, urlopen

HISTORY_URL = 'https://hithesis.site/dev-history.json'


def report_gate():
    spec = importlib.util.spec_from_file_location('dev_report_gate', Path(__file__).with_name('dev-report-gate.py'))
    gate = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gate)
    return gate


def verify_report(release):
    gate = report_gate()
    report = gate.manifest(release)
    request = Request(report['url'], headers={'User-Agent': 'hithesis-dev-pdf-check'})
    with urlopen(request, timeout=60) as response:
        data = response.read(gate.MAX_PDF_BYTES + 1)
    if len(data) > gate.MAX_PDF_BYTES or hashlib.sha256(data).hexdigest() != report['sha256']:
        raise ValueError('PDF download/checksum failed; notification blocked')
    with tempfile.TemporaryDirectory(prefix='hithesis-pdf-check-') as temporary:
        path = Path(temporary) / 'DEV_UPDATE.pdf'
        path.write_bytes(data)
        return gate.validate(path, release)


def request_publication(token, timeout=5400, request=None, sleep=time.sleep):
    if not token:
        raise ValueError('Set DEV_PUBLISH_TOKEN (repository Actions write) before enabling daily publication')
    identity = uuid.uuid4().hex
    title = 'dev publication ' + identity
    endpoint = 'https://api.github.com/repos/hithesis/hithesis/actions/workflows/test_dev.yml'
    def github(url, data=None):
        headers = {'Authorization': 'Bearer ' + token, 'User-Agent': 'hithesis-dev-publisher',
                   'Accept': 'application/vnd.github+json', 'Content-Type': 'application/json'}
        req = Request(url, data=json.dumps(data).encode() if data is not None else None, headers=headers)
        with urlopen(req, timeout=30) as response:
            body = response.read()
        return json.loads(body) if body else None
    api = request or github
    api(endpoint + '/dispatches', {'ref': 'dev', 'inputs': {
        'publish_only': True, 'notify_only': False, 'publication_request': identity}})
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        result = api(endpoint + '/runs?branch=dev&event=workflow_dispatch&per_page=30')
        run = next((r for r in result['workflow_runs'] if r['display_title'] == title), None)
        if run and run['status'] == 'completed':
            if run['conclusion'] != 'success':
                raise RuntimeError('Daily dev publication did not succeed: ' + run['html_url'])
            print('Daily publication check completed:', run['html_url'])
            return run
        sleep(15)
    raise RuntimeError('Timed out waiting for the dated dev publication; do not notify an unfinished build')


def fetch_history(url):
    url += ('&' if '?' in url else '?') + 'checked=' + str(int(datetime.now(timezone.utc).timestamp()))
    request = Request(url, headers={'User-Agent': 'hithesis-dev-notifier', 'Cache-Control': 'no-cache',
                                    'Accept': 'application/json'})
    try:
        with urlopen(request, timeout=30) as response:
            content = response.read(8 * 1024 * 1024 + 1)
    except HTTPError as error:
        if error.code == 404:
            error.close()
            print('No published dev history yet')
            return []
        raise
    if len(content) > 8 * 1024 * 1024:
        raise ValueError('Dev history exceeds the supported size')
    history = json.loads(content)
    if history.get('schema') != 1 or history.get('repository') != 'hithesis/hithesis':
        raise ValueError('Unexpected dev history')
    releases = history.get('releases', [])
    for release in releases:
        if (not re.fullmatch(r'[0-9a-f]{40}', release['commit']) or
                not re.fullmatch(r'dev-\d{8}-[0-9a-f]{12}-\d+-\d+', release.get('build_id', '')) or
                not re.fullmatch(r'v\d+\.\d+[a-z]?-dev\.\d{4}', release['label'])):
            raise ValueError('Invalid published dev identity')
        if release['release_url'] != 'https://hithesis.site/dev-builds/' + release['build_id'] + '/':
            raise ValueError('Unexpected release link')
    return releases


def pending_releases(releases, state, force=False):
    if not releases:
        return []
    if force:
        return [releases[-1]]
    if not state:
        # First installation announces the current preview, not the whole archive.
        return [releases[-1]]
    if state['commit'] == releases[-1]['commit']:
        return []
    for i, release in enumerate(releases):
        if release['build_id'] == state.get('build_id'):
            return releases[i + 1:]
    raise ValueError('Last notified release is missing from history; inspect state before resuming')


def format_message(releases):
    latest = releases[-1]
    report = report_gate().manifest(latest)
    changes, seen = [], set()
    for release in releases:
        for change in release['changes']:
            if change['id'] not in seen:
                seen.add(change['id'])
                # Keep this one text message; no CQ codes, images, or @all.
                changes.append(' '.join(change['text'].split()))
    lines = [f'hithesis 开发版更新｜{latest["label"]}',
             f'发布日期：{latest["published_on"]}（北京时间）', '', '本次更新：']
    if latest.get('announcement'):
        announcement = latest['announcement']
        if not isinstance(announcement, str) or len(announcement) > 1800:
            raise ValueError('Invalid public announcement')
        lines.append(announcement)
    else:
        for text in changes[:12]:
            lines.append('· ' + (text[:180] + '…' if len(text) > 180 else text))
        if not changes:
            lines.append('· 本次为维护更新，具体变化见附件。')
        if len(changes) > 12:
            lines.append(f'另有 {len(changes) - 12} 条，见更新详情。')
    lines += ['', '下载：https://hithesis.site/?version=dev',
              '更新详情：https://hithesis.site/DEV_CHANGELOG.md']
    lines += ['详细说明（PDF）：' + report['url'], gate_label()]
    return '\n'.join(lines)


def gate_label():
    return report_gate().AI_LABEL


def send_onebot(base_url, token, group_id, message):
    body = json.dumps({'group_id': group_id, 'message': message, 'auto_escape': True}).encode()
    request = Request(base_url.rstrip('/') + '/send_group_msg', data=body,
                      headers={'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json'})
    # A send is deliberately not automatically retried after an ambiguous timeout.
    with urlopen(request, timeout=30) as response:
        result = json.loads(response.read(1024 * 1024))
    if result.get('status') != 'ok' or result.get('retcode') != 0:
        raise RuntimeError(f'OneBot did not confirm delivery (retcode={result.get("retcode")})')
    message_id = (result.get('data') or {}).get('message_id')
    if message_id is None:
        raise RuntimeError('OneBot response has no message_id; notification state was not changed')
    return message_id


def notify(releases, state_path, group_id, base_url, token, force=False, dry_run=False, sender=send_onebot, verifier=None):
    state = json.loads(state_path.read_text()) if state_path.exists() else None
    if state and state.get('group_id') != group_id:
        raise ValueError('Notification state belongs to a different QQ group')
    pending = pending_releases(releases, state, force)
    if not pending:
        print('No unannounced dev changes')
        return False
    message = format_message(pending)
    if force and state and state.get('build_id') == releases[-1]['build_id']:
        message = state.get('message', message)
    if dry_run:
        print(message)
        return False
    # Confirm that the public PDF can actually be downloaded and parsed before
    # sending any group message or consuming notification state.
    (verifier or verify_report)(releases[-1])
    message_id = sender(base_url, token, group_id, message)
    record = {'group_id': group_id, 'build_id': releases[-1]['build_id'], 'commit': releases[-1]['commit'],
              'message_id': message_id, 'message': message,
              'sent_at': datetime.now(timezone.utc).isoformat(timespec='seconds')}
    temporary = state_path.with_suffix('.tmp')
    with temporary.open('w', encoding='utf-8') as output:
        json.dump(record, output, ensure_ascii=False, indent=2)
        output.write('\n')
        output.flush()
        os.fsync(output.fileno())
    temporary.replace(state_path)
    print('Notified', releases[-1]['label'], releases[-1]['commit'][:12], 'message_id=' + str(message_id))
    return True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--force', action='store_true', help='Resend the current preview even if already announced')
    parser.add_argument('--dry-run', action='store_true', help='Print a message without sending or recording it')
    parser.add_argument('--publish', action='store_true', help='Run and await the 08:00 dated publication before notifying')
    args = parser.parse_args()
    if args.publish and (args.force or args.dry_run):
        parser.error('--publish is a release operation; use --force/--dry-run separately for notifications')
    group = os.environ.get('QQ_GROUP_ID', '')
    if not group.isdigit() or int(group) <= 0:
        parser.error('Set QQ_GROUP_ID to the destination group number')
    base = os.environ.get('ONEBOT_URL', 'http://napcat:3000')
    token = os.environ.get('ONEBOT_ACCESS_TOKEN', '')
    if not token and not args.dry_run:
        parser.error('Set ONEBOT_ACCESS_TOKEN')
    state = Path(os.environ.get('NOTIFY_STATE', '/data/notified.json'))
    state.parent.mkdir(parents=True, exist_ok=True)
    with state.with_suffix('.lock').open('a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print('A dev publication/notification check is already in progress')
            return
        publication = request_publication(os.environ.get('DEV_PUBLISH_TOKEN', '')) if args.publish else None
        releases = fetch_history(os.environ.get('DEV_HISTORY_URL', HISTORY_URL))
        if publication:
            head = publication.get('head_sha')
            if (not releases or not isinstance(head, str) or not re.fullmatch(r'[0-9a-f]{40}', head)
                    or head not in (releases[-1]['commit'], releases[-1].get('source_commit'))):
                raise RuntimeError('Daily workflow did not publish this source and its PDF; notification blocked')
        notify(releases, state, int(group), base, token, args.force, args.dry_run)


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        print(f'Notification failed: {error}', file=sys.stderr)
        sys.exit(1)
