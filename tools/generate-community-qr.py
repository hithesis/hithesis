"""Generate the QQ QR asset from the same link used by the website."""
import json
from pathlib import Path
import subprocess

import qrcode
from qrcode.image.svg import SvgPathFillImage

root = Path(__file__).resolve().parents[1]
metadata = subprocess.check_output([
    'node', '--input-type=module', '-e',
    'import { COMMUNITY } from "./community-data.js"; console.log(JSON.stringify(COMMUNITY));',
], cwd=root, text=True)
group = json.loads(metadata)['group']
image = qrcode.make(group['joinURL'], image_factory=SvgPathFillImage,
                    error_correction=qrcode.constants.ERROR_CORRECT_M, border=4)
image.save(root / group['qrImage'])
print(group['number'], group['joinURL'], group['qrImage'])
