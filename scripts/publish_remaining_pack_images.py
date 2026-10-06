"""Publish explicitly selected, source-described reusable alternatives."""
import json
import shutil
import subprocess
import sys
import urllib.request
from datetime import datetime
from prepare_destination_images import ROOT, DATA, HEADERS

SELECTED = {
    'hung_yen_poi_01_b': ('File:Chùa Chuông Hưng Yên.jpg', 'Chùa Chuông trong quần thể di tích Phố Hiến, Hưng Yên'),
    'hung_yen_poi_02': ('File:ChuaNomDrumPavilion.JPG', 'Lầu trống tại chùa Nôm'),
    'khanh_hoa_poi_04': ('File:Hang Rái in Ninh Thuan Province, Vietnam.jpg', 'Cảnh ven biển Hang Rái'),
    'khanh_hoa_poi_05_b': ('File:Po Klong Garai Temple.jpg', 'Kiến trúc tháp Po Klong Garai'),
    'can_tho_poi_03': ('File:Nha co Binh Thuy 1.jpg', 'Nhà cổ Bình Thủy, Cần Thơ'),
    'da_nang_poi_05': ('File:Gom Thanh Ha.JPG', 'Hoạt động làm gốm tại làng Thanh Hà'),
    'dak_lak_poi_01': ('File:Srepok Ban Don.JPG', 'Sông Sêrêpốk tại Bản Đôn'),
    'dak_lak_poi_03': ('File:Buôn Ma Thuột - buildings at Exile House former prison Apr 2024 01.jpg', 'Công trình trong Nhà đày Buôn Ma Thuột, ảnh tháng 4/2024'),
    'dien_bien_poi_01': ('File:Hố bộc phá ở đồi A1.jpg', 'Hố bộc phá tại đồi A1'),
    'dien_bien_poi_05': ('File:Đèo Pha Đin - panoramio.jpg', 'Cảnh đèo Pha Đin'),
    'gia_lai_poi_03': ('File:Eo Gió - Nhơn Lý.jpg', 'Eo Gió tại Nhơn Lý'),
    'hue_poi_04': ('File:Đầm Chuồn, Phá Tam Giang (a lagoon in central Vietnam), 2019.jpg', 'Đầm Chuồn trong vùng phá Tam Giang, ảnh năm 2019'),
}


def main():
    path = ROOT / 'src/rag/catalogue_images.json'
    records = {r['id']: r for r in json.loads(path.read_text(encoding='utf8'))}
    candidates = {r['id']: r for r in json.loads((DATA / 'remaining_pack_image_candidates.json').read_text(encoding='utf8'))}
    backup = ROOT / 'data/backups' / ('remaining_images_' + datetime.now().strftime('%Y%m%d_%H%M%S'))
    backup.mkdir(parents=True)
    shutil.copy2(path, backup / path.name)
    added, failed = [], []
    for identifier, (filename, caption) in SELECTED.items():
        if identifier in records:
            continue
        try:
            photo = next(p for p in candidates[identifier]['candidates'] if p['file'] == filename)
            assert photo['author'] and photo['description']
            assert photo['license'].startswith(('CC BY', 'CC0', 'Public domain'))
            assert photo['license_url'] or photo['license'] == 'Public domain'
            with urllib.request.urlopen(urllib.request.Request(photo['url'], headers=HEADERS), timeout=20) as response:
                content = response.read(6000001)
            extension = 'jpg' if content.startswith(b'\xff\xd8\xff') else 'png' if content.startswith(b'\x89PNG\r\n\x1a\n') else None
            assert extension and len(content) <= 6000000, 'Invalid image payload'
            target = ROOT / 'frontend/public/images/destinations' / (identifier + '.' + extension)
            target.write_bytes(content)
            image = {k: photo[k] for k in ('source', 'author', 'license', 'original_url')}
            image.update(url='/images/destinations/' + target.name, caption=caption,
                         license_url=photo['license_url'] or photo['source'],
                         changes='Không chỉnh sửa nội dung; dùng bản xem trước của nguồn.',
                         retrieved_on=datetime.now().date().isoformat())
            records[identifier] = {'id': identifier, 'image': image, 'review_note': photo['description']}
            added.append(identifier)
        except Exception as error:
            failed.append({'id': identifier, 'error': str(error)})
    path.write_text(json.dumps(list(records.values()), ensure_ascii=False, indent=2) + '\n', encoding='utf8')
    subprocess.run([sys.executable, str(ROOT / 'scripts/build_catalogue.py')], cwd=ROOT, check=True)
    places = json.loads((ROOT / 'src/rag/catalogue.json').read_text(encoding='utf8'))
    report = {'added': added, 'failed': failed, 'with_images': sum(bool(p.get('image')) for p in places),
              'remaining': [{'id': p['id'], 'name': p['name']} for p in places if not p.get('image')]}
    (DATA / 'remaining_pack_image_report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
    print(json.dumps({**report, 'remaining': len(report['remaining'])}, ensure_ascii=True))


if __name__ == '__main__':
    main()