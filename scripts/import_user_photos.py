"""Import the four destination photos supplied in the project root."""
import json
import shutil
import subprocess
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MATCHES = {'cam son': 'bac_ninh_poi_06', 'pa kh': 'dien_bien_poi_04',
           'cu thach': 'dong_nai_poi_04', 'vanh': 'hung_yen_poi_05'}

if __name__ == '__main__':
    path = ROOT / 'src/rag/catalogue_images.json'
    records = {r['id']: r for r in json.loads(path.read_text(encoding='utf8'))}
    imported = set()
    for photo in ROOT.glob('*.jpg'):
        normalized = ''.join(c for c in unicodedata.normalize('NFD', photo.stem.lower())
                             if not unicodedata.combining(c))
        identifier = next((identifier for fragment, identifier in MATCHES.items() if fragment in normalized), None)
        if not identifier:
            continue
        if identifier in imported:
            raise ValueError('Ambiguous photo match: ' + identifier)
        if not photo.read_bytes().startswith(b'\xff\xd8\xff'):
            raise ValueError('Not a JPEG: ' + photo.name)
        target = ROOT / 'frontend/public/images/destinations' / (identifier + '.jpg')
        shutil.copyfile(photo, target)
        records[identifier] = {'id': identifier, 'image': {
            'url': '/images/destinations/' + target.name,
            'source': '/images/destinations/' + target.name,
            'author': 'Người dùng cung cấp',
            'license': 'Chưa xác minh giấy phép',
            'retrieved_on': '2026-10-01',
        }, 'review_note': 'Ghép theo tên file do người dùng cung cấp: ' + photo.name}
        imported.add(identifier)
    if imported != set(MATCHES.values()):
        raise ValueError('Missing supplied images: ' + repr(set(MATCHES.values()) - imported))
    path.write_text(json.dumps(list(records.values()), ensure_ascii=False, indent=2) + '\n', encoding='utf8')
    subprocess.run([sys.executable, str(ROOT / 'scripts/publish_reviewed_images_round2.py')], cwd=ROOT, check=True)