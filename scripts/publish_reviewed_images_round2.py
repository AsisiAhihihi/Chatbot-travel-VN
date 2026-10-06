"""Publish only manually reviewed candidates from this collection round."""
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
APPROVED = {
    'cu-chi', 'an_giang_poi_01', 'an_giang_poi_04', 'an_giang_poi_06',
    'bac_ninh_poi_01', 'ca_mau_poi_02', 'can_tho_poi_01', 'dak_lak_poi_02',
    'thanh_hoa_poi_01', 'thanh_pho_ho_chi_minh_poi_01',
    'dak_lak_poi_04', 'dak_lak_poi_06', 'dong_nai_poi_02', 'dong_nai_poi_03',
    'dong_thap_poi_01', 'dong_thap_poi_02',
    'dong_thap_poi_04', 'ha_noi_poi_03', 'ha_noi_poi_04', 'ha_noi_poi_05',
    'hai_phong_poi_03', 'hue_poi_02', 'lai_chau_poi_03', 'nghe_an_poi_01',
    'nghe_an_poi_02', 'phu_tho_poi_01', 'quang_ngai_poi_06', 'tay_ninh_poi_02',
    'tay_ninh_poi_03', 'thai_nguyen_poi_02',
}

if __name__ == '__main__':
    path = ROOT / 'src/rag/catalogue_images.json'
    records = {r['id']: r for r in json.loads(path.read_text(encoding='utf8'))}
    candidates = json.loads((ROOT / 'data/geography/image_candidates.json').read_text(encoding='utf8'))
    for row in candidates:
        if row['id'] not in APPROVED or not row.get('image'):
            continue
        image = row['image']
        photo = ROOT / 'frontend/public' / image['url'].lstrip('/')
        if not photo.is_file() or not image.get('author') or not image.get('license'):
            raise ValueError('Missing photograph or credit: ' + row['id'])
        records[row['id']] = {'id': row['id'], 'image': image, 'review_note': row['description']}
    path.write_text(json.dumps(list(records.values()), ensure_ascii=False, indent=2) + '\n', encoding='utf8')
    subprocess.run([sys.executable, str(ROOT / 'scripts/build_catalogue.py')], cwd=ROOT, check=True)
    places = json.loads((ROOT / 'src/rag/catalogue.json').read_text(encoding='utf8'))
    mapped = [p for p in places if p.get('coordinates')]
    missing = [{'id': p['id'], 'name': p['name']} for p in mapped if not p.get('image')]
    summary = {'mapped': len(mapped), 'with_images': len(mapped) - len(missing), 'missing': missing}
    (ROOT / 'data/geography/image_coverage.json').write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
    print(json.dumps(summary, ensure_ascii=True))