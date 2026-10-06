"""Publish the reviewed Nậm Ban landscape with explicit geographic scope."""
import json
import shutil
import subprocess
import sys
from datetime import datetime
from prepare_destination_images import ROOT, PUBLIC, api, plain, request


def main():
    identifier = 'lai_chau_poi_02'
    title = 'File:Nậm Ban, Sìn Hồ, Lai Châu, Vietnam - panoramio.jpg'
    path = ROOT / 'src/rag/catalogue_images.json'
    records = json.loads(path.read_text(encoding='utf8'))
    if any(row['id'] == identifier for row in records):
        print('Already published; no existing image overwritten.')
        return
    page = next(iter(api('commons.wikimedia.org', titles=title, prop='imageinfo',
                         iiprop='url|extmetadata', iiurlwidth=800)['query']['pages'].values()))
    info = page['imageinfo'][0]
    metadata = info['extmetadata']
    description = plain(metadata['ImageDescription']['value'])
    author = plain(metadata['Artist']['value'])
    license_name = plain(metadata['LicenseShortName']['value'])
    assert 'Sìn Hồ' in description and 'Nậm Ban' in description
    assert author and license_name == 'CC BY-SA 3.0'
    payload = request(info.get('thumburl', info['url']))
    assert payload.startswith(b'\xff\xd8\xff') and len(payload) < 6000000
    backup = ROOT / 'data/backups' / ('sin_ho_photo_' + datetime.now().strftime('%Y%m%d_%H%M%S'))
    backup.mkdir(parents=True)
    shutil.copy2(path, backup / path.name)
    destination = PUBLIC / (identifier + '.jpg')
    destination.write_bytes(payload)
    records.append({'id': identifier, 'review_note': description, 'image': {
        'url': '/images/destinations/' + destination.name,
        'source': info['descriptionurl'], 'original_url': info['url'],
        'author': author, 'license': license_name,
        'license_url': metadata['LicenseUrl']['value'],
        'caption': 'Cảnh tại Nậm Ban, địa bàn Sìn Hồ, ảnh năm 2015; không phải trung tâm thị trấn Sìn Hồ.',
        'changes': 'Bản xem trước từ nguồn; không chỉnh sửa nội dung.',
        'retrieved_on': datetime.now().date().isoformat()}})
    path.write_text(json.dumps(records, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
    subprocess.run([sys.executable, str(ROOT / 'scripts/build_catalogue.py')], cwd=ROOT, check=True)
    print('Published', identifier)


if __name__ == '__main__':
    main()