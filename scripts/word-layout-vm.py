#!/usr/bin/env python3
"""Measure registered table rows and figure blocks using an isolated Windows Word instance."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import importlib.util
import json
from pathlib import Path
import threading
import uuid

ROOT=Path(__file__).resolve().parents[1]
loader=importlib.util.spec_from_file_location('word_layout_bridge',ROOT/'scripts/export-word-reference.py')
bridge=importlib.util.module_from_spec(loader);loader.loader.exec_module(bridge)


def measure(docx,out,spec,vm='Windows',host='10.211.55.2'):
    docx=Path(docx).resolve();out=Path(out).resolve();out.mkdir(parents=True,exist_ok=False)
    (out/'spec.json').write_text(json.dumps(spec,ensure_ascii=False,indent=2)+'\n')
    token=uuid.uuid4().hex
    downloads={'input.docx':docx,'spec.json':out/'spec.json','layout.ps1':out/'layout.ps1'}
    uploads={'output.pdf','layout.json'}
    if spec.get('save_roundtrip'):uploads.add('roundtrip.docx')

    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*unused):pass
        def member(self,allowed):
            prefix='/'+token+'/'
            name=self.path[len(prefix):] if self.path.startswith(prefix) else None
            return name if name in allowed else None
        def do_GET(self):
            name=self.member(downloads)
            if name is None:self.send_error(404);return
            value=downloads[name].read_bytes();self.send_response(200)
            self.send_header('Content-Length',str(len(value)));self.end_headers();self.wfile.write(value)
        def do_POST(self):
            name=self.member(uploads);size=int(self.headers.get('Content-Length','0'))
            if name is None or not 0<size<64000000:self.send_error(400);return
            value=self.rfile.read(size)
            if len(value)!=size:self.send_error(400);return
            (out/name).write_bytes(value);self.send_response(200);self.end_headers();self.wfile.write(b'OK')

    server=ThreadingHTTPServer((host,0),Handler)
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    endpoint=f'http://{host}:{server.server_port}/{token}/';remote=None
    try:
        remote=bridge.powershell(vm,"[Console]::Write([IO.Path]::Combine($env:TEMP,'hit-continuations-"+uuid.uuid4().hex[:12]+"'))")
        bridge.powershell(vm,'New-Item -ItemType Directory -Path '+bridge.quote(remote)+' | Out-Null')
        script=r'''$root=REMOTE;$app=$null;$doc=$null;$owned=$false;$before=[IntPtr]::Zero;$identity=[IntPtr]::Zero
try{$active=[Runtime.InteropServices.Marshal]::GetActiveObject('Word.Application');$before=[Runtime.InteropServices.Marshal]::GetIUnknownForObject($active);[void][Runtime.InteropServices.Marshal]::ReleaseComObject($active)}catch{}
try{
 $app=New-Object -ComObject Word.Application
 $identity=[Runtime.InteropServices.Marshal]::GetIUnknownForObject($app)
 if($before -ne [IntPtr]::Zero -and $identity -eq $before){throw 'Word instance is not isolated'}
 $owned=$true;$app.Visible=$false;$app.DisplayAlerts=0;$app.AutomationSecurity=3
 $input=$root+'\input.docx';$pdf=$root+'\output.pdf'
 $spec=Get-Content -LiteralPath ($root+'\spec.json') -Raw -Encoding UTF8|ConvertFrom-Json
 $doc=$app.Documents.Open($input,$false,$true,$false)
 $doc.Repaginate()
 $doc.ExportAsFixedFormat($pdf,17,$false,0,0,1,1,0,$true,$false,0,$true,$true,$false)
 $doc.Repaginate()
 function Position([string]$name){
  if(-not $doc.Bookmarks.Exists($name)){throw ('Missing registered bookmark: '+$name)}
  $range=$doc.Bookmarks.Item($name).Range
  $start=$doc.Range([int]$range.Start,[int]($range.Start+1))
  $last=[Math]::Max([int]$range.Start,[int]$range.End-1)
  $end=$doc.Range([int]$last,[int]($last+1))
  return @{bookmark=$name;start_page=[int]$start.Information(3);end_page=[int]$end.Information(3);text=$range.Text;inline_shapes=$range.InlineShapes.Count}
 }
 $tables=@()
 foreach($entry in @($spec.tables)){
  if(-not $doc.Bookmarks.Exists($entry.bookmark)){throw ('Missing table bookmark: '+$entry.bookmark)}
  $table=$doc.Bookmarks.Item($entry.bookmark).Range.Tables.Item(1);$rows=@()
  for($j=1;$j -le $table.Rows.Count;$j++){
   $r=$table.Rows.Item($j).Range
   $start=$doc.Range([int]$r.Start,[int]($r.Start+1))
   $last=[Math]::Max([int]$r.Start,[int]$r.End-2)
   $end=$doc.Range([int]$last,[int]($last+1))
   $rows+=@{index=$j;start_page=[int]$start.Information(3);end_page=[int]$end.Information(3);text=$r.Text}
  }
  $tables+=@{id=$entry.id;bookmark=$entry.bookmark;rows=$rows}
 }
 $figures=@()
 foreach($entry in @($spec.figures)){
  $units=@();$captions=@()
  foreach($name in @($entry.units)){$units+=Position $name}
  foreach($name in @($entry.captions)){$captions+=Position $name}
  $figures+=@{id=$entry.id;units=$units;captions=$captions}
 }
 $fonts=@{}
 foreach($name in @('times.ttf','timesbd.ttf','simsun.ttc','simhei.ttf')){
  $fonts[$name]=(Get-FileHash (Join-Path ($env:WINDIR+'\Fonts') $name) -Algorithm SHA256).Hash.ToLower()
 }
 $mode=$doc.CompatibilityMode;$pageCount=$doc.ComputeStatistics(2);$roundtripHash=$null;$roundtripMode=$mode
 if($spec.save_roundtrip){
  [object]$savePath=$root+'\roundtrip.docx';[object]$format=12
  $doc.SaveAs2([ref]$savePath,[ref]$format)
  $roundtripMode=$doc.CompatibilityMode
  $save=0;$doc.Close([ref]$save);[void][Runtime.InteropServices.Marshal]::ReleaseComObject($doc);$doc=$null
  $roundtripHash=(Get-FileHash ($root+'\roundtrip.docx') -Algorithm SHA256).Hash.ToLower()
 }
 @{kind='actual-word-continuation-layout';word_version=(Get-Item ($app.Path+'\WINWORD.EXE')).VersionInfo.FileVersion;
 os=[Environment]::OSVersion.VersionString;compatibility_mode=$mode;roundtrip_sha256=$roundtripHash;roundtrip_compatibility_mode=$roundtripMode;
 input_sha256=(Get-FileHash $input -Algorithm SHA256).Hash.ToLower();pdf_sha256=(Get-FileHash $pdf -Algorithm SHA256).Hash.ToLower();
 pages=$pageCount;tables=$tables;figures=$figures;fonts=$fonts;fields_updated=$false;isolated_com_identity=$true;active_instance_was_present=($before -ne [IntPtr]::Zero)}|ConvertTo-Json -Depth 12|Set-Content -Encoding UTF8 ($root+'\layout.json')
}finally{
 if($doc -ne $null -and $owned){$save=0;$doc.Close([ref]$save);[void][Runtime.InteropServices.Marshal]::ReleaseComObject($doc)}
 if($app -ne $null){if($owned){$save=0;$app.Quit([ref]$save)};[void][Runtime.InteropServices.Marshal]::ReleaseComObject($app)}
 if($identity -ne [IntPtr]::Zero){[void][Runtime.InteropServices.Marshal]::Release($identity)}
 if($before -ne [IntPtr]::Zero){[void][Runtime.InteropServices.Marshal]::Release($before)}
}'''.replace('REMOTE',bridge.quote(remote))
        (out/'layout.ps1').write_text("$ErrorActionPreference='Stop';\n"+script,encoding='utf-8-sig')
        for name in downloads:
            bridge.powershell(vm,'(New-Object Net.WebClient).DownloadFile('+bridge.quote(endpoint+name)+','+bridge.quote(remote+'\\'+name)+')')
        bridge.powershell(vm,'[ScriptBlock]::Create([IO.File]::ReadAllText('+bridge.quote(remote+'\\layout.ps1')+')).Invoke()',timeout=600)
        for name in sorted(uploads):
            bridge.powershell(vm,'[void](New-Object Net.WebClient).UploadData('+bridge.quote(endpoint+name)+",'POST',[IO.File]::ReadAllBytes("+bridge.quote(remote+'\\'+name)+'))')
        result=json.loads((out/'layout.json').read_text(encoding='utf-8-sig'))
        if result['input_sha256']!=bridge.digest(docx) or result['pdf_sha256']!=bridge.digest(out/'output.pdf'):
            raise ValueError('Word layout bytes do not match the VM record')
        if spec.get('save_roundtrip') and result['roundtrip_sha256']!=bridge.digest(out/'roundtrip.docx'):
            raise ValueError('Word roundtrip DOCX hash mismatch')
        expected=json.loads((ROOT/'tests/reference/word-fonts.json').read_text())['files']
        if result['fonts']!=expected:raise ValueError('VM fonts differ from the fixed Word reference')
        result.update(measurer_sha256=bridge.digest(__file__),powershell_sha256=bridge.digest(out/'layout.ps1'))
        (out/'verified-layout.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
        return result
    finally:
        try:
            if remote:bridge.powershell(vm,'Remove-Item -LiteralPath '+bridge.quote(remote)+' -Recurse -Force -ErrorAction SilentlyContinue')
        finally:server.shutdown();server.server_close();thread.join()
