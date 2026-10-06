"""Import supplied local photos without inventing a reuse license."""
import hashlib
import json
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / 'anh_17_dia_diem_kem_nguon/anh_17_dia_diem'


def main():
    rows = json.loads((PACK / 'image_sources.json').read_text(encoding='utf8'))
    catalogue = json.loads((ROOT / 'src/rag/catalogue.json').read_text(encoding='utf8'))
    places = {p['id']: p for p in catalogue}
    metadata = ROOT / 'src/rag/catalogue_images.json'
    records = {r['id']: r for r in json.loads(metadata.read_text(encoding='utf8'))}
    assert len(rows) == len({r['id'] for r in rows}) == 17
    # Validate all assets before modifying the published catalogue.
    for row in rows:
        assert row['id'] in places and places[row['id']]['name'] == row['name'], row['id']
        path = (PACK / row['image']).resolve()
        assert path.is_relative_to((PACK / 'images').resolve())
        payload = path.read_bytes()
        assert hashlib.sha256(payload).hexdigest() == row['sha256'], row['id']
        assert (payload.startswith(b'\xff\xd8\xff') or
                (payload.startswith(b'RIFF') and payload[8:12] == b'WEBP')), row['id']
        assert row['width'] > 0 and row['height'] > 0
        assert row['source_page_url'].startswith('https://')
        assert row['rights_status'] == 'permission_required' and row['license'] is None
        existing = places[row['id']].get('image')
        assert not existing or existing.get('supplied_pack') == 'final_17', row['id']
    backup = ROOT / 'data/backups' / ('final_photo_pack_' + datetime.now().strftime('%Y%m%d_%H%M%S'))
    backup.mkdir(parents=True)
    for source in (metadata, ROOT / 'src/rag/catalogue.json', ROOT / 'frontend/public/data/places.json',
                   ROOT / 'danh_sach_dia_diem_chua_co_anh.md'):
        shutil.copy2(source, backup / source.name)
    public = ROOT / 'frontend/public/images/places'
    public.mkdir(parents=True, exist_ok=True)
    for row in rows:
        source = PACK / row['image']
        shutil.copy2(source, public / source.name)
        records[row['id']] = {'id': row['id'], 'image': {
            'url': '/images/places/' + source.name,
            'source': row['source_page_url'], 'source_name': row['source_name'],
            'author': row['photo_credit'] or row['source_name'] + ' (chưa xác định tác giả)',
            'caption': row['caption'], 'original_url': row['image_url'],
            'rights_status': row['rights_status'], 'rights_note': row['rights_note'],
            'supplied_pack': 'final_17', 'retrieved_on': row['checked_on'],
            'sha256': row['sha256'], 'changes': 'Ảnh do người dùng cung cấp; giữ nguyên file.'}}
    metadata.write_text(json.dumps(list(records.values()), ensure_ascii=False, indent=2) + '\n', encoding='utf8')
    subprocess.run([sys.executable, str(ROOT / 'scripts/build_catalogue.py')], cwd=ROOT, check=True)
    updated = json.loads((ROOT / 'src/rag/catalogue.json').read_text(encoding='utf8'))
    missing = [p for p in updated if not p.get('image', {}).get('url')]
    assert not missing, [p['id'] for p in missing]
    (ROOT / 'danh_sach_dia_diem_chua_co_anh.md').write_text(
        '# Địa điểm chưa có ảnh\n\nCòn 0 / 209 điểm chưa có ảnh.\n\n'
        'Đã nhập 17 ảnh do người dùng cung cấp. Các ảnh này có nguồn nhưng chưa xác nhận '
        'quyền dùng lại (`permission_required`); cần xin phép trước khi đăng website công khai.\n', encoding='utf8')
    report = {'added': [r['id'] for r in rows], 'with_images': len(updated), 'missing': len(missing),
              'permission_required': [r['id'] for r in rows], 'backup': str(backup)}
    (ROOT / 'data/geography/final_photo_pack_report.json').write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
    print(json.dumps(report, ensure_ascii=False))


if __name__ == '__main__':
    main()