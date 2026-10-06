"""Publish reviewed source coordinates; leave unresolved objects unlocated."""
import json
import shutil
import re
from html import unescape
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
# Exact object scope, not a namesake administrative division.
VI = {'lam_dong_poi_06', 'lao_cai_poi_01', 'lao_cai_poi_02',
      'quang_ngai_poi_01', 'son_la_poi_03', 'son_la_poi_05',
      'tuyen_quang_poi_04_b', 'tuyen_quang_poi_06', 'thai_nguyen_poi_03'}
EN2 = {'ca_mau_poi_01', 'dong_nai_poi_01', 'dong_nai_poi_05',
       'gia_lai_poi_01', 'quang_tri_poi_02_b'}
EN3 = {'hung_yen_poi_01': 'Hiến Town', 'lam_dong_poi_04': 'Mũi Né',
       'son_la_poi_02': 'Mộc Châu', 'ninh_binh_poi_05_b': 'Phổ Minh Temple'}


def main():
    base = ROOT / 'src/rag'
    cache = ROOT / 'data/geography'
    path = base / 'catalogue_locations.json'
    existing = json.loads(path.read_text(encoding='utf8'))
    backup = ROOT / 'data/backups' / ('coordinates_additional_' + datetime.now().strftime('%Y%m%d_%H%M%S'))
    backup.mkdir(parents=True)
    shutil.copy2(path, backup / path.name)
    candidates = {c['id']: c for c in json.loads((cache / 'coordinate_candidates.json').read_text(encoding='utf8'))}
    round2 = {c['id']: c['enwiki'] for c in json.loads((cache / 'coordinate_round2.json').read_text(encoding='utf8'))}
    round3 = {p['title']: p for p in json.loads((cache / 'coordinate_round3.json').read_text(encoding='utf8'))['query']['pages'].values()}
    added = []
    for identifier in sorted(VI | EN2 | set(EN3)):
        if any(row['id'] == identifier for row in existing):
            continue
        if identifier in VI:
            page = candidates[identifier]
            values = page['wiki_coordinates']
            title = page['article']
            language = 'vi'
            date = page['retrieved_on']
            assert not page['disambiguation']
        else:
            page = round2[identifier] if identifier in EN2 else round3[EN3[identifier]]
            values = page['coordinates']
            title = page['title']
            language = 'en'
            date = datetime.now().date().isoformat()
            assert 'disambiguation' not in page.get('pageprops', {})
        assert len(values) == 1, identifier
        lat, lon = values[0]['lat'], values[0]['lon']
        assert 8 <= lat <= 24 and 102 <= lon <= 110
        source = f'https://{language}.wikipedia.org/wiki/' + quote(title.replace(' ', '_'))
        row = {'id': identifier, 'coordinates': [lon, lat], 'coordinate_source': source,
               'coordinate_sources': [source], 'coordinate_status': 'sourced_reference',
               'coordinate_precision': None, 'coordinate_retrieved_on': date,
               'coordinate_note': 'Vị trí tham chiếu của địa điểm hoặc vùng cảnh quan theo nguồn địa lý; không phải cổng vào, bến đón hay đường tiếp cận đã xác nhận. Đối với sông và vùng rộng, marker không thể hiện toàn bộ phạm vi.'}
        existing.append(row)
        added.append(row)
    for identifier, slug, expected in [('can_tho_poi_02', 'benninhkieu', 'Bến Ninh Kiều'),
                                       ('can_tho_poi_03', 'nhacobinhthuy', 'Nhà cổ Bình Thủy')]:
        if any(row['id'] == identifier for row in existing):
            continue
        html = unescape((cache / (identifier + '_extra_portal.html')).read_text(encoding='utf8'))
        assert expected in html
        pairs = set(re.findall(r'(?:google.maps.LatLng\(\s*|g_GetMapPlace_LatLng\s*=\s*\")([\d.]+),\s*([\d.]+)', html))
        assert len(pairs) == 1
        lat, lon = map(float, next(iter(pairs)))
        assert 8 <= lat <= 24 and 102 <= lon <= 110
        source = 'https://canthotourism.vn/vi/' + slug
        row = {'id': identifier, 'coordinates': [lon, lat], 'coordinate_source': source,
               'coordinate_sources': [source], 'coordinate_status': 'sourced_reference',
               'coordinate_precision': None, 'coordinate_retrieved_on': datetime.now().date().isoformat(),
               'coordinate_note': 'Vị trí từ bản đồ trên cổng du lịch địa điểm; chưa xác nhận đường tiếp cận hoặc lối vào tại hiện trường.'}
        existing.append(row)
        added.append(row)
    if not any(row['id'] == 'vinh_long_poi_05' for row in existing):
        # Official geographical-name table, Công báo 705+706, 26-09-2017,
        # printed page 9: ao Bà Om 9°55'07" N, 106°18'08" E.
        source = 'https://congbaocdn.chinhphu.vn/CongBaoCP/VanBan/2017/8/24727/19261-1-2017705-70621-2017-tt-btnmt.pdf'
        row = {'id': 'vinh_long_poi_05', 'coordinates': [106+18/60+8/3600, 9+55/60+7/3600],
               'coordinate_source': source, 'coordinate_sources': [source],
               'coordinate_status': 'sourced_reference', 'coordinate_precision': 1/3600,
               'coordinate_retrieved_on': datetime.now().date().isoformat(),
               'coordinate_note': 'Tọa độ trung tâm ao Bà Om trong bảng địa danh Công báo số 705+706 ngày 26-09-2017, trang in 9; chuyển độ-phút-giây sang độ thập phân. Không phải cổng vào.'}
        existing.append(row)
        added.append(row)
    path.write_text(json.dumps(existing, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
    (cache / 'coordinate_additional_review.json').write_text(json.dumps(added, ensure_ascii=False, indent=2), encoding='utf8')
    print('Added:', len(added), 'Backup:', backup)


if __name__ == '__main__':
    main()