"""Build small same-origin QR images while checking that QR payloads stay unchanged."""
import io
import json
from pathlib import Path
import subprocess

from PIL import Image, ImageOps
import zxingcpp

root = Path(__file__).resolve().parents[1]
metadata = json.loads(subprocess.check_output([
    'node', '--input-type=module', '-e',
    'import { COMMUNITY } from "./community-data.js"; console.log(JSON.stringify(COMMUNITY));',
], cwd=root, text=True))


def payloads(image):
    return sorted(code.text for code in zxingcpp.read_barcodes(image))


results = []
for login, person in metadata['contributors'].items():
    for method in person['donations']:
        destination = root / method['image']
        assert destination.parent == root / 'assets/community'
        original = subprocess.check_output(['curl', '--fail', '--silent', '--show-error',
            '--location', '--max-time', '45', '--retry', '2', '--proto', '=https',
            '--proto-redir', '=https', method['source']])
        source = ImageOps.exif_transpose(Image.open(io.BytesIO(original))).convert('RGBA')
        image = Image.new('RGB', source.size, 'white')
        image.paste(source, mask=source.getchannel('A'))
        expected = payloads(image)
        if expected and max(image.size) > 960:
            resized = image.copy()
            resized.thumbnail((960, 960), Image.Resampling.LANCZOS)
            if payloads(resized) == expected:
                image = resized
        candidates = []
        for options in [{'lossless': True}, *([{'quality': 90}] if expected else [])]:
            output = io.BytesIO()
            image.save(output, format='WEBP', method=6, **options)
            data = output.getvalue()
            decoded = Image.open(io.BytesIO(data))
            if not expected or payloads(decoded) == expected:
                candidates.append(data)
        if not candidates:
            raise ValueError('QR verification failed: ' + login + ' ' + method['label'])
        data = min(candidates, key=len)
        destination.write_bytes(data)
        results.append({'login': login, 'method': method['label'], 'original': len(original),
                        'optimized': len(data), 'size': image.size, 'verified_codes': len(expected)})
print(json.dumps(results, ensure_ascii=False, indent=2))
