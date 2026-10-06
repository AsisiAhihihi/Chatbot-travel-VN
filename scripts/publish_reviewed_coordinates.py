"""Publish explicitly reviewed geographic objects from cached source responses.

No first-result geocoding, administrative centroids or generated coordinates.
"""
import json
import shutil
import re
from html import unescape
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
REVIEWED = set('''an_giang_poi_02 an_giang_poi_05_b
bac_ninh_poi_02 bac_ninh_poi_02_b bac_ninh_poi_05 bac_ninh_poi_05_b
can_tho_poi_07_b da_nang_poi_01 da_nang_poi_02 da_nang_poi_02_b
dak_lak_poi_01_b dak_lak_poi_05 gia_lai_poi_03_b gia_lai_poi_04
ha_tinh_poi_04 ha_tinh_poi_04_b hai_phong_poi_01 hai_phong_poi_01_b
hai_phong_poi_04 hai_phong_poi_04_b hue_poi_03 hue_poi_03_b
hung_yen_poi_01_b khanh_hoa_poi_03 khanh_hoa_poi_03_b khanh_hoa_poi_05_b
lai_chau_poi_04 lam_dong_poi_01 lam_dong_poi_01_b lam_dong_poi_05 lam_dong_poi_05_b
lao_cai_poi_01_b lao_cai_poi_03_b ninh_binh_poi_03 ninh_binh_poi_03_b ninh_binh_poi_05
phu_tho_poi_02_b quang_ngai_poi_03 quang_tri_poi_02 quang_tri_poi_04 quang_tri_poi_04_b
thanh_hoa_poi_04 thanh_pho_ho_chi_minh_poi_05 thanh_pho_ho_chi_minh_poi_05_b
thanh_pho_ho_chi_minh_poi_06 tuyen_quang_poi_01 tuyen_quang_poi_04 tuyen_quang_poi_05'''.split())


def main():
    base = ROOT / 'src/rag'
    cache = ROOT / 'data/geography'
    path = base / 'catalogue_locations.json'
    candidates = {c['id']: c for c in json.loads((cache / 'coordinate_candidates.json').read_text(encoding='utf8'))}
    existing = json.loads(path.read_text(encoding='utf8'))
    backup = ROOT / 'data/backups' / ('coordinates_' + datetime.now().strftime('%Y%m%d_%H%M%S'))
    backup.mkdir(parents=True)
    for file in ('catalogue_locations.json', 'catalogue.json'):
        shutil.copy2(base / file, backup / file)
    decisions = []
    for identifier in sorted(REVIEWED):
        if any(row['id'] == identifier for row in existing):
            continue
        candidate = candidates[identifier]
        assert not candidate['disambiguation']
        wiki = candidate['wiki_coordinates']
        wd = candidate['wikidata_coordinates']
        # Never pick the first of conflicting Wikidata statements.
        assert len(wiki) == 1 or (not wiki and len(wd) == 1), identifier
        article = 'https://vi.wikipedia.org/wiki/' + quote(candidate['article'].replace(' ', '_'))
        value = wiki[0] if wiki else wd[0]
        lon = value.get('lon', value.get('longitude'))
        lat = value.get('lat', value.get('latitude'))
        source = article if wiki else 'https://www.wikidata.org/wiki/' + candidate['wikidata_id'] + '#P625'
        assert 102 <= lon <= 110 and 8 <= lat <= 24
        note = ('Vị trí tham chiếu theo nguồn địa lý cho đúng địa điểm, không phải lối vào, bến đón '
                'hay tuyến đường đã xác nhận. Với núi, vịnh, đảo, đô thị và vườn quốc gia, '
                'địa điểm trải rộng quanh vị trí tham chiếu; không dùng marker để suy ra đường tiếp cận.')
        existing.append({'id': identifier, 'coordinates': [lon, lat],
                         'coordinate_source': source, 'coordinate_sources': [article, source],
                         'coordinate_status': 'sourced_reference',
                         'coordinate_precision': value.get('precision'),
                         'coordinate_retrieved_on': candidate['retrieved_on'],
                         'coordinate_note': note})
        decisions.append({'id': identifier, 'article': candidate['article'], 'coordinates': [lon, lat],
                          'status': 'reviewed', 'source': source})
    portals = [
        ('bac_ninh_poi_03', 'dinhbang_source.html', 'https://mybacninh.vn/vi/dinhdinhbang', 'Đình Đình Bảng'),
        ('thai_nguyen_poi_04', 'thai_nguyen_poi_04_portal.html', 'https://mythainguyen.vn/vi/hangphuonghoang', 'Phượng Hoàng'),
        ('vinh_long_poi_03', 'vanthanh_portal.html', 'https://vinhlongtourist.vn/vi/vanthanhmieuvinhlong', 'VĂN THÁNH MIẾU'),
    ]
    for identifier, filename, url, expected in portals:
        if any(row['id'] == identifier for row in existing):
            continue
        html = unescape((cache / filename).read_text(encoding='utf8'))
        assert expected in html, identifier
        pairs = re.findall(r'google.maps.LatLng\(\s*([\d.]+),\s*([\d.]+)\)', html)
        if not pairs:
            pairs = re.findall(r'g_GetMapPlace_LatLng\s*=\s*"([\d.]+),([\d.]+)"', html)
        assert len(set(pairs)) == 1, identifier
        lat, lon = map(float, pairs[0])
        assert 102 <= lon <= 110 and 8 <= lat <= 24
        existing.append({'id': identifier, 'coordinates': [lon, lat],
                         'coordinate_source': url, 'coordinate_sources': [url],
                         'coordinate_status': 'sourced_reference', 'coordinate_precision': None,
                         'coordinate_retrieved_on': datetime.now().date().isoformat(),
                         'coordinate_note': 'Vị trí tham chiếu từ bản đồ trên cổng du lịch của địa điểm; chưa xác nhận lối vào hoặc điều kiện tiếp cận tại hiện trường.'})
        decisions.append({'id': identifier, 'article': expected, 'coordinates': [lon, lat],
                          'status': 'reviewed_portal', 'source': url})
    path.write_text(json.dumps(existing, ensure_ascii=False, indent=2)+'\n', encoding='utf8')
    (cache / 'coordinate_review_decisions.json').write_text(json.dumps(decisions, ensure_ascii=False, indent=2)+'\n', encoding='utf8')
    print('Added:', len(decisions), 'Backup:', backup)


if __name__ == '__main__':
    main()