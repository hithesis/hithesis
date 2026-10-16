#!/usr/bin/env python3
"""Export prepared references with an isolated Parallels Windows Word COM instance."""
import argparse
import base64
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import re
import subprocess
import threading
import time
import uuid

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def quote(value):
    return "'" + str(value).replace("'", "''") + "'"


def powershell(vm, command, timeout=120):
    source = "$ErrorActionPreference='Stop'; [Console]::OutputEncoding=[Text.UTF8Encoding]::new($false); " + command
    encoded = base64.b64encode(source.encode('utf-16-le')).decode()
    for attempt in range(6):
        result = subprocess.run(['prlctl', 'exec', vm, '--current-user', 'powershell.exe', '-NoProfile', '-EncodedCommand', encoded],
                                capture_output=True, timeout=timeout)
        output = (result.stdout + result.stderr).decode('utf-8-sig', errors='replace')
        if result.returncode == 0:
            return result.stdout.decode('utf-8-sig').strip()
        if attempt == 5 or not any(s in output for s in ('Invalid argument', 'Unable to open new session')):
            raise RuntimeError(output)
        time.sleep(2 * (attempt + 1))


def export(args):
    source = args.input.resolve(); out = args.output.resolve()
    manifest_file = source / 'inputs.json'
    manifest = json.loads(manifest_file.read_text())
    documents = manifest['documents']
    if not documents:
        raise ValueError('No prepared documents')
    names = [d['name'] for d in documents]
    if len(set(names)) != len(names) or any(not re.fullmatch(r'[a-z0-9-]+', n) for n in names):
        raise ValueError('Document identifiers must be unique ASCII names')
    for d in documents:
        if d['file'] != d['name'] + '.docx' or digest(source / d['file']) != d['sha256']:
            raise ValueError('Prepared input does not match manifest: ' + d['name'])
    font_spec = json.loads(args.fonts_record.read_text())
    font_records = {}
    for name, expected in font_spec['files'].items():
        if not re.fullmatch(r'[a-zA-Z0-9_.-]+', name):
            raise ValueError('Invalid font file identifier')
        actual = powershell(args.vm, '[Console]::Write((Get-FileHash (Join-Path (Join-Path $env:WINDIR "Fonts") ' + quote(name) + ') -Algorithm SHA256).Hash.ToLower())')
        if actual != expected:
            raise ValueError('VM font differs from reference font record: ' + name)
        font_records[name] = actual
    out.mkdir(parents=True, exist_ok=False)
    (out / 'fonts.json').write_text(json.dumps({'files': font_records, 'source_record_sha256': digest(args.fonts_record)}, indent=2) + '\n')
    token = uuid.uuid4().hex
    downloads = {n + '.docx': source / (n + '.docx') for n in names}
    downloads['word-export.ps1'] = out / 'word-export.ps1'
    uploads = {n + '.pdf' for n in names} | {'export.json'}

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *unused):
            pass

        def selected(self, allowed):
            prefix = '/' + token + '/'
            name = self.path[len(prefix):] if self.path.startswith(prefix) else None
            return name if name in allowed else None

        def do_GET(self):
            name = self.selected(downloads)
            if name is None:
                self.send_error(404); return
            data = downloads[name].read_bytes()
            self.send_response(200); self.send_header('Content-Length', str(len(data))); self.end_headers(); self.wfile.write(data)

        def do_POST(self):
            name = self.selected(uploads)
            length = int(self.headers.get('Content-Length', '0'))
            if name is None or not 0 < length < 64000000:
                self.send_error(400); return
            data = self.rfile.read(length)
            if len(data) != length:
                self.send_error(400); return
            (out / name).write_bytes(data)
            self.send_response(200); self.end_headers(); self.wfile.write(b'OK')

    server = ThreadingHTTPServer((args.host, 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
    endpoint = f'http://{args.host}:{server.server_address[1]}/{token}/'
    remote = None
    try:
        remote = powershell(args.vm, "[Console]::Write([IO.Path]::Combine($env:TEMP,'hithesis-reference-" + uuid.uuid4().hex[:12] + "'))")
        powershell(args.vm, 'New-Item -ItemType Directory -Path ' + quote(remote) + ' | Out-Null')
        script = r'''$root=REMOTE; $items=@(NAMES); $records=@(); $app=$null; $doc=$null; $owned=$false
$before=0; try {$active=[Runtime.InteropServices.Marshal]::GetActiveObject('Word.Application'); $before=$active.Hwnd; [void][Runtime.InteropServices.Marshal]::ReleaseComObject($active)} catch {}
try {
  $app=New-Object -ComObject Word.Application
  if($before -ne 0 -and $app.Hwnd -eq $before){throw 'Word instance is not isolated'}
  $owned=$true; $app.Visible=$false; $app.DisplayAlerts=0; $app.AutomationSecurity=3
  $version=$app.Version; $build=$app.Build; $exe=(Get-Item ($app.Path+'\WINWORD.EXE')).VersionInfo.FileVersion
  foreach($name in $items){
    $input=$root+'\'+$name+'.docx'; $pdf=$root+'\'+$name+'.pdf'
    $doc=$app.Documents.Open($input,$false,$true,$false)
    $doc.Repaginate()
    $doc.ExportAsFixedFormat($pdf,17,$false,0,0,1,1,0,$true,$false,0,$true,$true,$false)
    $records+=@{name=$name; input_sha256=(Get-FileHash $input -Algorithm SHA256).Hash.ToLower(); pdf_sha256=(Get-FileHash $pdf -Algorithm SHA256).Hash.ToLower(); pages=$doc.ComputeStatistics(2)}
    $save=0; $doc.Close([ref]$save); [void][Runtime.InteropServices.Marshal]::ReleaseComObject($doc); $doc=$null
  }
  @{word_version=$version; word_build=$build; executable_version=$exe; os=[Environment]::OSVersion.VersionString; hwnd=$app.Hwnd; inputs=$records}|ConvertTo-Json -Depth 6|Set-Content -Encoding UTF8 ($root+'\export.json')
} finally {
  if($doc -ne $null -and $owned){$save=0; $doc.Close([ref]$save); [void][Runtime.InteropServices.Marshal]::ReleaseComObject($doc)}
  if($app -ne $null){if($owned){$save=0; $app.Quit([ref]$save)}; [void][Runtime.InteropServices.Marshal]::ReleaseComObject($app)}
}
'''.replace('REMOTE', quote(remote)).replace('NAMES', ','.join(quote(n) for n in names))
        (out / 'word-export.ps1').write_text("$ErrorActionPreference='Stop';\n" + script, encoding='utf-8-sig')
        for name in downloads:
            powershell(args.vm, '(New-Object Net.WebClient).DownloadFile(' + quote(endpoint + name) + ',' + quote(remote + '\\' + name) + ')')
        powershell(args.vm, '[ScriptBlock]::Create([IO.File]::ReadAllText(' + quote(remote + '\\word-export.ps1') + ')).Invoke()', timeout=600)
        for name in sorted(uploads):
            powershell(args.vm, '[void](New-Object Net.WebClient).UploadData(' + quote(endpoint + name) + ",'POST',[IO.File]::ReadAllBytes(" + quote(remote + '\\' + name) + '))')
        report = json.loads((out / 'export.json').read_text(encoding='utf-8-sig'))
        expected = {d['name']: d for d in documents}
        for entry in report['inputs']:
            if entry['input_sha256'] != expected[entry['name']]['sha256'] or digest(out / (entry['name'] + '.pdf')) != entry['pdf_sha256']:
                raise ValueError('Exported bytes do not match VM hash record')
        if {e['name'] for e in report['inputs']} != set(names):
            raise ValueError('Incomplete Word export')
        report.update(kind='actual-windows-word-com-export', input_manifest_sha256=digest(manifest_file),
                      exporter_sha256=digest(__file__),
                      font_record_sha256=digest(out / 'fonts.json'), fields_updated=False,
                      prepared_input_directory=str(source))
        (out / 'verified-export.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
        print('WORD VERIFIED', report['executable_version'], report['inputs'])
    finally:
        if remote is not None:
            try:
                powershell(args.vm, 'Remove-Item -LiteralPath ' + quote(remote) + ' -Recurse -Force -ErrorAction SilentlyContinue')
            finally:
                server.shutdown(); server.server_close(); thread.join()
        else:
            server.shutdown(); server.server_close(); thread.join()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--vm', default='Windows')
    p.add_argument('--host', default='10.211.55.2', help='Host-only interface reachable from the VM')
    p.add_argument('--fonts-record', type=Path, default=ROOT / 'tests/reference/word-fonts.json')
    export(p.parse_args())


if __name__ == '__main__':
    main()
