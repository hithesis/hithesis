"""Invoke the fixed notification command via Workbench from a GitHub runner."""
import json
import os
from pathlib import Path
import re
import subprocess
import sys


def write_config(home, access_id, access_secret):
    if not access_id or not access_secret:
        raise ValueError('Set DEV_NOTIFY_ACCESS_KEY_ID and DEV_NOTIFY_ACCESS_KEY_SECRET')
    directory = home / '.workbench'
    directory.mkdir(parents=True, mode=0o700, exist_ok=True)
    config = directory / 'config.json'
    payload = {'current': 'default', 'profiles': {'default': {
        'mode': 'AK', 'access_key_id': access_id, 'access_key_secret': access_secret}},
        'agent_enabled': False, 'language': 'zh'}
    fd = os.open(config, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, 'w') as output:
        json.dump(payload, output)
    return config


def remote_command(force=False):
    return '/opt/hithesis-notify/notify.sh' + (' --force' if force else '')


def main():
    instance = os.environ.get('DEV_NOTIFY_INSTANCE_ID', '')
    region = os.environ.get('DEV_NOTIFY_REGION', 'cn-beijing')
    if not re.fullmatch(r'i-[A-Za-z0-9]+', instance):
        raise ValueError('Set repository variable DEV_NOTIFY_INSTANCE_ID')
    if not re.fullmatch(r'[a-z0-9-]+', region):
        raise ValueError('Invalid DEV_NOTIFY_REGION')
    binary = Path(sys.argv[1]).resolve()
    # Workbench keeps a Unix socket under HOME; keep its path short on macOS too.
    home = Path(os.environ['RUNNER_TEMP']) / 'wb'
    config = write_config(home, os.environ.get('DEV_NOTIFY_ACCESS_KEY_ID', ''),
                          os.environ.get('DEV_NOTIFY_ACCESS_KEY_SECRET', ''))
    environment = dict(os.environ, HOME=str(home))
    try:
        subprocess.run([str(binary), 'exec', '--region', region, '--instance-id', instance,
                        '--command', remote_command(os.environ.get('FORCE_NOTIFY') == 'true'),
                        '--timeout', '60'], env=environment, check=True)
    finally:
        try:
            subprocess.run([str(binary), 'daemon', 'stop'], env=environment,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        finally:
            config.unlink(missing_ok=True)


if __name__ == '__main__':
    main()
