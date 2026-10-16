#!/usr/bin/env python3
"""Copy actual VM fonts into a new private directory for same-file controls."""
import argparse
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import importlib.util
import json
from pathlib import Path
import threading
import uuid

ROOT = Path(__file__).resolve().parents[1]


def export(args):
    spec = importlib.util.spec_from_file_location('font_vm_bridge', ROOT / 'scripts/export-word-reference.py')
    bridge = importlib.util.module_from_spec(spec); spec.loader.exec_module(bridge)
    out = args.output.resolve()
    if out.exists(): raise FileExistsError('Private font output already exists: ' + str(out))
    candidates = ['times.ttf', 'timesbd.ttf', 'timesi.ttf', 'timesbi.ttf', 'simsun.ttc', 'simhei.ttf',
                  'simkai.ttf', 'simfang.ttf', 'kaiti.ttf', 'fangsong.ttf']
    command = ('$names=@(' + ','.join(bridge.quote(n) for n in candidates) + '); $r=@(); '
               "foreach($n in $names){$p=Join-Path ($env:WINDIR+'\\Fonts') $n;"
               "if(Test-Path -LiteralPath $p){$r+=@{name=$n;sha256=(Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLower()}}};"
               '[Console]::Write((ConvertTo-Json -InputObject $r -Depth 5))')
    records = json.loads(bridge.powershell(args.vm, command))
    actual = {r['name']: r['sha256'] for r in records}
    expected = json.loads((ROOT / 'tests/reference/word-fonts.json').read_text())['files']
    for name, digest in expected.items():
        if actual.get(name) != digest: raise ValueError('VM font differs from the approved content reference: ' + name)
    selected = candidates[:6] + [next(n for n in ('simkai.ttf', 'kaiti.ttf') if n in actual),
                                 next(n for n in ('simfang.ttf', 'fangsong.ttf') if n in actual)]
    if not all(n in actual for n in selected): raise ValueError('VM is missing a required font face')
    out.mkdir(parents=True, exist_ok=False)
    token = uuid.uuid4().hex; received = {}

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *unused): pass

        def do_POST(self):
            prefix = '/' + token + '/'
            name = self.path[len(prefix):] if self.path.startswith(prefix) else None
            size = int(self.headers.get('Content-Length', '0'))
            if name not in selected or name in received or not 0 < size < 64000000:
                self.send_error(400); return
            data = self.rfile.read(size)
            if len(data) != size or hashlib.sha256(data).hexdigest() != actual[name]:
                self.send_error(400); return
            (out / name).write_bytes(data); received[name] = actual[name]
            self.send_response(200); self.end_headers(); self.wfile.write(b'OK')

    server = ThreadingHTTPServer((args.host, 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
    endpoint = f'http://{args.host}:{server.server_port}/{token}/'
    try:
        for name in selected:
            bridge.powershell(args.vm, '[void](New-Object Net.WebClient).UploadData(' + bridge.quote(endpoint + name) +
                              ",'POST',[IO.File]::ReadAllBytes((Join-Path ($env:WINDIR+'\\Fonts') " + bridge.quote(name) + ')))')
    finally:
        server.shutdown(); server.server_close(); thread.join()
    if set(received) != set(selected): raise ValueError('Incomplete font transfer')
    record = {'kind': 'private-actual-windows-word-font-files', 'files': received,
              'reference_record_sha256': bridge.digest(ROOT / 'tests/reference/word-fonts.json'),
              'exporter_sha256': bridge.digest(__file__), 'vm': args.vm,
              'installation_performed': False, 'distribute_binaries': False}
    (out / 'fonts.json').write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n')
    print('Verified private font files:', len(received), out)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--vm', default='Windows')
    parser.add_argument('--host', default='10.211.55.2')
    export(parser.parse_args())


if __name__ == '__main__':
    main()
