"""Import only packaged licensed images, matched by catalogue ID."""
import json
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    pack = ROOT / 'nguon_anh_95_dia_diem'
    rows = json.loads((pack / 'poi_image_sources.json').read_text(encoding='utf8'))
    registry = ROOT / 'src/rag/catalogue_images.json'
    existing = {r['id']: r for r in json.loads(registry.read_text(encoding='utf8'))}
    places = json.loads((ROOT / 'src/rag/catalogue.json').read_text(encoding='utf8'))
    known = {p['id'] for p in places}
    pending = []
    skipped = []
    for row in rows:
        if row['status'] != 'licensed_photo_available':
            skipped.append({'id': row['id'], 'reason': row['status']})
            continue
        if row['id'] not in known:
            raise ValueError('Unknown destination: ' + row['id'])
        if row['id'] in existing:
            skipped.append({'id': row['id'], 'reason': 'existing_image_preserved'})
            continue
        photo = next((p for p in row.get('images', []) if p.get('local_path')), None)
        if not photo:
            raise ValueError('Missing packaged image: ' + row['id'])
        source = (pack / photo['local_path']).resolve()
        if not source.is_relative_to((pack / 'images').resolve()) or source.stem != row['id']:
            raise ValueError('Unsafe or mismatched image path: ' + str(source))
        content = source.read_bytes()
        if not (content.startswith(b'\xff\xd8\xff') or content.startswith(b'\x89PNG\r\n\x1a\n')):
            raise ValueError('Invalid image: ' + str(source))
        for key in ('author', 'license', 'source_page_url', 'caption'):
            if not photo.get(key):
                raise ValueError(f'Missing {key}: {row["id"]}')
        if not photo.get('license_url') and photo['license'] != 'Public domain':
            raise ValueError('Missing license link: ' + row['id'])
        target = ROOT / 'frontend/public/images/supplied' / source.name
        image = {'url': '/images/supplied/' + source.name,
                 'source': photo['source_page_url'], 'author': photo['author'],
                 'license': photo['license'], 'license_url': photo.get('license_url') or photo['source_page_url'],
                 'caption': photo['caption'], 'changes': photo.get('changes', ''),
                 'retrieved_on': row.get('checked_on'),
                 'attribution_text': photo.get('attribution_text', '')}
        pending.append((source, target, {'id': row['id'], 'image': image,
                        'review_note': 'User-supplied licensed pack, matched by ID; ' + row.get('notes', '')}))
    backup = ROOT / 'data/backups' / ('supplied_images_' + datetime.now().strftime('%Y%m%d_%H%M%S'))
    backup.mkdir(parents=True)
    shutil.copy2(registry, backup / registry.name)
    for source, target, record in pending:
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        existing[record['id']] = record
    registry.write_text(json.dumps(list(existing.values()), ensure_ascii=False, indent=2) + '\n', encoding='utf8')
    subprocess.run([sys.executable, str(ROOT / 'scripts/build_catalogue.py')], cwd=ROOT, check=True)
    places = json.loads((ROOT / 'src/rag/catalogue.json').read_text(encoding='utf8'))
    report = {'imported': [r['id'] for _, _, r in pending], 'skipped': skipped,
              'with_images': sum(bool(p.get('image')) for p in places),
              'without_images': sum(not p.get('image') for p in places)}
    (ROOT / 'data/geography/supplied_image_import_report.json').write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
    print(json.dumps({**report, 'skipped': len(skipped)}, ensure_ascii=True))


if __name__ == '__main__':
    main()