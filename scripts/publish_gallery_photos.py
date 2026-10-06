"""Publish explicitly reviewed gallery files, retaining attribution."""
import json
import subprocess
import sys
from datetime import date
from prepare_destination_images import ROOT, DATA, PUBLIC, request
from prepare_destination_images import api, plain

SELECTED = {
    'trang-an': 'File:TrangAn04.jpg',
    'dong_thap_poi_05': 'File:Tham quan cồn Lân.jpg',
    'gia_lai_poi_02': 'File:QuangTrung museum landscape.jpg',
    'lang_son_poi_03': 'File:Cửa hang Tam Thanh.jpg',
    'lao_cai_poi_06': 'File:Thác Bà lake - panorama.jpg',
    'ninh_binh_poi_02': 'File:Codohoalu-1.jpg',
    'quang_tri_poi_03': 'File:Visitors in Vinh Moc tunnel.JPG',
    'tay_ninh_poi_01': 'File:Ba Den Mountain 2019.jpg',
    'thai_nguyen_poi_05': 'File:Ba Be Lake 2.jpg',
    'lang_son_poi_01': 'File:Mau Son.JPG',
    'vinh_long_poi_04': 'File:Nơi hành đạo của ông Đạo Dừa.jpg',
    'thanh_hoa_poi_02': 'File:Lam Kinh.jpg',
    'vinh_long_poi_01': 'File:An binh.JPG',
}

if __name__ == '__main__':
    path = ROOT / 'src/rag/catalogue_images.json'
    records = {r['id']: r for r in json.loads(path.read_text(encoding='utf8'))}
    rows = json.loads((DATA / 'photo_alternatives.json').read_text(encoding='utf8'))
    # Explicitly reviewed photographs absent from the corresponding article galleries.
    for identifier in ('thanh_hoa_poi_02', 'vinh_long_poi_01'):
        if identifier in records:
            continue
        filename = SELECTED[identifier]
        info = next(iter(api('commons.wikimedia.org', titles=filename, prop='imageinfo',
                            iiprop='url|extmetadata', iiurlwidth=800)['query']['pages'].values()))['imageinfo'][0]
        meta = info['extmetadata']
        row = next(r for r in rows if r['id'] == identifier)
        row['candidates'].append({'file': filename,
            'description': plain(meta.get('ImageDescription', {}).get('value', '')),
            'author': plain(meta.get('Artist', {}).get('value', '')),
            'license': plain(meta.get('LicenseShortName', {}).get('value', '')),
            'license_url': meta.get('LicenseUrl', {}).get('value', ''),
            'source': info['descriptionurl'], 'url': info.get('thumburl', info['url']),
            'original_url': info['url'], 'article_source': info['descriptionurl']})
    for row in rows:
        filename = SELECTED.get(row['id'])
        if not filename or row['id'] in records:
            continue
        candidate = next((c for c in row['candidates'] if c['file'] == filename), None)
        if not candidate or not candidate['author'] or not candidate['license'].startswith(('CC BY', 'CC0', 'Public domain')):
            continue
        try:
            picture = request(candidate['url'])
            extension = 'jpg' if picture.startswith(b'\xff\xd8\xff') else 'png' if picture.startswith(b'\x89PNG\r\n\x1a\n') else None
            if not extension or len(picture) > 1500000:
                raise ValueError('Invalid or oversized photo')
            destination = PUBLIC / (row['id'] + '.' + extension)
            destination.write_bytes(picture)
            image = {k: candidate[k] for k in ('source', 'author', 'license', 'license_url', 'original_url', 'article_source')}
            image.update(url='/images/destinations/' + destination.name, retrieved_on=date.today().isoformat())
            records[row['id']] = {'id': row['id'], 'image': image, 'review_note': candidate['description'] or candidate['file']}
            path.write_text(json.dumps(list(records.values()), ensure_ascii=False, indent=2) + '\n', encoding='utf8')
            print(row['id'], 'published', flush=True)
        except Exception as error:
            print(row['id'], str(error), flush=True)
    subprocess.run([sys.executable, str(ROOT / 'scripts/publish_reviewed_images_round2.py')], cwd=ROOT, check=True)